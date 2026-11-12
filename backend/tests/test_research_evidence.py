import pandas as pd
import pytest
from fastapi import HTTPException
from pydantic import SecretStr

from services.research_evidence import summarize, compare, extract_observations, subject_context
from services import research
from services import research_collectors as collectors
from ml_engine.validator import DataValidator
from services.ai_engine import build_web_grounded_dataset, score_web_source_credibility


def source(title='Đại học Thủ Dầu Một tuyển sinh 2025', excerpt='Năm 2025 trường có 12.000 sinh viên. Học phí 25,5 triệu đồng mỗi năm.'):
    return dict(title=title, excerpt=excerpt, url='https://tdmu.edu.vn/cong-khai', provider='DuckDuckGo Web', verified=False)


def test_university_context_is_not_online_course_market():
    result = summarize('Đại học Thủ Dầu Một', [source()])
    assert result['detected_category_vi'] == 'Giáo dục đại học & tuyển sinh'
    assert result['recommended_dataset'] is None
    assert result['benchmark_metrics']['potential_score'] is None
    assert result['benchmark_metrics']['avg_growth_pct'] is None
    assert any(c['label'] == 'Việc làm sau tốt nghiệp' for c in result['criteria'])
    assert result['dataset_readiness']['ready'] is False


def test_literal_observations_keep_provenance_and_missing_period():
    rows = extract_observations('Đại học Thủ Dầu Một', [source()])
    assert [r['value'] for r in rows] == [12000, 25.5]
    assert rows[0]['period'] == '2025'
    assert all(r['source_url'] == source()['url'] and r['verified'] is False for r in rows)
    rows = extract_observations('Trường X', [source(excerpt='Tỷ lệ việc làm 95% trong hai năm 2024 và 2025.')])
    assert rows[0]['period'] is None
    assert rows[0]['value'] == 95
    assert 'mẫu số' in rows[0]['metric']


def test_no_source_no_manufactured_metrics_for_unknown_keyword():
    data = summarize('123xyz chưa tồn tại', [])
    assert data['observations'] == []
    assert data['market_signals']['signal_score'] is None
    assert data['benchmark_metrics']['potential_score'] is None
    assert subject_context('123xyz')['category'] == 'General Research'


def test_direct_comparison_needs_no_stored_sessions():
    left = {'query': 'Đại học Bình Dương', 'sources': [source('Đại học Bình Dương học phí', 'Học phí cần xem theo chương trình.')]}
    right = {'query': 'Đại học Mở', 'sources': [source('Đại học Mở tuyển sinh', 'Thông báo tuyển sinh chính thức.')]}
    result = compare(left, right)
    row = next(r for r in result['comparison_matrix'] if r['metric'] == 'Học phí & học bổng')
    assert row['left_sources']
    assert not row['right_sources']
    assert 'Chưa có dữ liệu' in row['right_value']
    assert not any('tiềm năng' in r['metric'] or 'tăng trưởng' in r['metric'] for r in result['comparison_matrix'])


def test_aggregators_do_not_verify_unknown_publisher():
    assert not score_web_source_credibility('https://untrusted.example/story', 'Google News')['is_reputable']
    assert not score_web_source_credibility('https://wikipedia.org.evil.example/story', 'Wikipedia')['is_reputable']
    assert score_web_source_credibility('https://tdmu.edu.vn/story')['is_reputable']


def test_unreviewed_export_cannot_be_trained_as_demand():
    result = DataValidator.validate_dataset(pd.DataFrame(extract_observations('Trường X', [source()])))
    assert result['valid'] is False
    assert 'chưa phải' in result['error']
    with pytest.raises(ValueError, match='không tự tạo'):
        build_web_grounded_dataset('Trường X', 'Education & EdTech', [source()])


def test_every_enabled_provider_runs_even_with_other_results(monkeypatch):
    monkeypatch.setattr(research, 'provider_configuration', lambda: {'web_search_configured': True, 'providers': [
        {'name': p, 'configured': True, 'requires_key': True} for p in ['Brave Search', 'Tavily', 'Wikidata']]})
    calls = []
    def collect(name, query):
        calls.append(name)
        item = source()
        item['provider'] = name
        return [item], {'name': name, 'status': 'ok'}
    monkeypatch.setattr(collectors, 'collect', collect)
    result = collectors.discover('Đại học Thủ Dầu Một')
    assert set(calls) == {'Brave Search', 'Tavily', 'Wikidata'}
    assert len(result['sources']) == 1
    assert len(result['providers']) == 3


def test_unrelated_academic_hit_is_rejected(monkeypatch):
    monkeypatch.setattr(research, 'fetch_json', lambda *args, **kwargs: {'results': [
        {'title': 'Nghiên cứu môi trường biển', 'id': 'https://openalex.org/W123', 'publication_year': 2025}]})
    items, status = collectors.collect('OpenAlex Research', 'Đại học Thủ Dầu Một')
    assert items == []
    assert status['status'] == 'no_results'


def test_analysis_rejects_wrong_entity_before_training(monkeypatch):
    from services.analysis import analyze
    from schemas.analysis import AnalyzeRequest
    monkeypatch.setattr('services.analysis.resolve_dataset', lambda name: name)
    monkeypatch.setattr('services.analysis.read_dataset', lambda _: pd.DataFrame({'Product_Name': ['Khóa học trực tuyến'] * 30, 'Sales': list(range(30)), 'Price': list(range(30))}))
    with pytest.raises(HTTPException) as error:
        analyze(AnalyzeRequest(dataset_name='education_edtech_courses.csv', product_name='Đại học Thủ Dầu Một', category='Education & EdTech'))
    assert error.value.status_code == 422


def test_provider_configuration_is_honest_and_hides_credentials(monkeypatch):
    monkeypatch.setattr(research.settings, 'brave_search_api_key', SecretStr(''))
    monkeypatch.setattr(research.settings, 'tavily_api_key', SecretStr('private-key'))
    result = research.provider_configuration()
    assert next(p for p in result['providers'] if p['name'] == 'Brave Search')['configured'] is False
    assert next(p for p in result['providers'] if p['name'] == 'Tavily')['configured'] is True
    assert 'private-key' not in str(result)


def test_negative_values_preserve_sign():
    rows = extract_observations('Trường X', [source(excerpt='Mức thay đổi -10,5% năm 2025.')])
    assert rows[0]['value'] == -10.5


def test_malformed_or_huge_number_does_not_break_research():
    assert extract_observations('Trường X', [source(excerpt='Chuỗi sai 1.2.3% và ' + '9' * 400 + ' USD')]) == []
