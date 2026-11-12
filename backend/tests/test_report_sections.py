import pytest
from services.report_sections import build_sections
from services.research_evidence import subject_context


def sections(query, sources=None):
    return build_sections(query, subject_context(query, sources or []), sources or [], {}, None)


def test_education_prices_the_program_not_the_institution():
    result = sections('Đại học Thủ Dầu Một')
    pricing = result['pricing_strategy']
    assert pricing['applicable']
    assert pricing['title'] == 'Chính sách học phí & học bổng'
    assert pricing['recommended_price'] is None
    assert not pricing['formulas']
    assert 'kiểm định' in str(result['risk_assessment'])


@pytest.mark.parametrize('query', ['trà sữa', 'Nước ép trái cây tươi đóng chai ngách văn phòng', 'nhà hàng chay'])
def test_food_has_cost_methods_and_food_safety_risks(query):
    result = sections(query)
    assert result['pricing_strategy']['applicable']
    assert len(result['pricing_strategy']['formulas']) == 3
    assert 'An toàn thực phẩm' in str(result['risk_assessment'])


@pytest.mark.parametrize('query', ['biến đổi khí hậu', 'một từ khóa xyz123 chưa xác định'])
def test_unknown_or_public_topic_never_invents_a_price(query):
    result = sections(query)
    assert result['pricing_strategy']['applicable'] is False
    assert result['pricing_strategy']['methods'] == []
    assert result['market_analysis']['size_estimate'] is None
    assert all(x['probability'] is None and x['impact'] is None for x in result['risk_assessment']['items'])


def test_source_quotes_keep_provenance_without_claiming_verified_facts():
    source = {'title': 'Học phí chương trình', 'url': 'https://example.edu.vn/hoc-phi', 'excerpt': 'Học phí cần đối chiếu theo năm học.'}
    result = sections('Đại học Thủ Dầu Một', [source])
    assert result['market_analysis']['source_findings'][0]['excerpt'] == source['excerpt']
    assert result['market_analysis']['source_findings'][0]['verified'] is False
    assert result['pricing_strategy']['price_sources'][0]['url'] == source['url']
