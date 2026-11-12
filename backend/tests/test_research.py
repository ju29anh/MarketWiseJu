import pytest
from urllib.error import HTTPError
from pydantic import SecretStr
from fastapi.testclient import TestClient
from fastapi import HTTPException
from main import app
from services import research
from services.analysis import analyze
from schemas.analysis import AnalyzeRequest


@pytest.fixture(autouse=True)
def isolate_provider_configuration(monkeypatch):
    # Tests must never consume a real API key inherited from .env/the host.
    monkeypatch.setattr(research.settings, 'research_wikipedia', True)
    monkeypatch.setattr(research.settings, 'research_wikidata', False)
    monkeypatch.setattr(research.settings, 'research_duckduckgo', False)
    monkeypatch.setattr(research.settings, 'research_google_news', False)
    monkeypatch.setattr(research.settings, 'research_openalex', False)
    monkeypatch.setattr(research.settings, 'brave_search_api_key', SecretStr(''))
    monkeypatch.setattr(research.settings, 'tavily_api_key', SecretStr(''))
    monkeypatch.setattr(research.settings, 'gemini_api_key', SecretStr(''))


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


def test_source_discovery_is_not_verification(client, monkeypatch):
    monkeypatch.setattr(research.settings, 'research_wikipedia', True)
    monkeypatch.setattr(research.settings, 'brave_search_api_key', SecretStr(''))
    monkeypatch.setattr(research, 'fetch_json', lambda *args: {'pages': [
        {'title': 'Đại học Thủ Dầu Một', 'key': 'Đại_học_Thủ_Dầu_Một', 'excerpt': '<b>Trường</b> đại học &amp; nghiên cứu'}]})
    result = client.post('/api/research/search', json={'query': 'Đại học Thủ Dầu Một'}).json()
    assert result['status'] == 'needs_review'
    assert result['sources'][0]['verified'] is False
    assert '<b>' not in result['sources'][0]['excerpt']
    assert result['sources'][0]['identity_match'] is True
    assert result['checked_at']


def test_provider_failure_has_no_fabricated_result(client, monkeypatch):
    monkeypatch.setattr(research.settings, 'research_wikipedia', True)
    monkeypatch.setattr(research.settings, 'brave_search_api_key', SecretStr(''))
    def fail(*args):
        raise OSError('private error')
    monkeypatch.setattr(research, 'fetch_json', fail)
    result = client.post('/api/research/search', json={'query': 'Highland Coffee'}).json()
    assert result['sources'] == []
    assert result['status'] == 'insufficient_evidence'
    assert 'private error' not in str(result)


@pytest.mark.parametrize('url', ['javascript:alert(1)', 'http://example.com', 'https://127.0.0.1/', 'https://[::1]/', 'https://user:pass@example.com', 'https://host.local', 'https://example.com:8000'])
def test_unsafe_result_urls(url):
    assert research.safe_url(url) is None


def test_title_relevance_rejects_unrelated_search_hits():
    assert not research.relevant_title('Highland Coffee', 'Việt Nam')
    assert research.relevant_title('Highland Coffee', 'Highlands Coffee')
    assert research.relevant_title('Đại học Thủ Dầu Một', 'Trường Đại học Thủ Dầu Một')
    assert research.relevant_title('R', 'R (ngôn ngữ lập trình)')
    assert research.relevant_title('C++', 'C++')
    assert not research.relevant_title('C++', 'C#')
    assert not research.relevant_title('C#', 'C (programming language)')


def test_compare_validation_and_no_winner(client, monkeypatch):
    assert client.post('/api/research/search', json={'query': '  '}).status_code == 422
    assert client.post('/api/research/compare', json={'left': {'query': 'Cà phê'}, 'right': {'query': 'ca phe'}}).status_code == 400
    monkeypatch.setattr('routers.research.discover', lambda q: {'query': q, 'sources': []})
    response = client.post('/api/research/compare', json={'left': {'query': 'Trường A'}, 'right': {'query': 'Trường B'}})
    assert response.status_code == 200
    assert 'Chưa đủ' in response.json()['conclusion']


def test_brave_filters_links_and_keeps_key_server_side(client, monkeypatch):
    monkeypatch.setattr(research.settings, 'research_wikipedia', False)
    monkeypatch.setattr(research.settings, 'brave_search_api_key', SecretStr('test-private-key'))
    def provider(url, headers):
        assert url.startswith('https://api.search.brave.com/')
        assert headers['X-Subscription-Token'] == 'test-private-key'
        return {'web': {'results': [{'url': 'javascript:alert(1)'}, {'url': 'https://example.com/page', 'title': 'Highlands Coffee', 'description': '<i>Trích đoạn</i>'}]}}
    monkeypatch.setattr(research, 'fetch_json', provider)
    response = client.post('/api/research/search', json={'query': 'Highlands Coffee'})
    assert len(response.json()['sources']) == 1
    assert 'test-private-key' not in response.text


def test_analysis_supports_any_custom_keyword_with_benchmark_and_web(monkeypatch):
    import pandas as pd
    monkeypatch.setattr('services.analysis.resolve_dataset', lambda name: name)
    monkeypatch.setattr('services.analysis.read_dataset', lambda path: pd.DataFrame({
        'product_name': ['Cà phê mẫu'] * 30, 'price': list(range(30)), 'sales': list(range(100, 130))}))
    monkeypatch.setattr('services.analysis.discover', lambda q: {
        'query': q, 'sources': [{'title': q, 'url': 'https://example.org/info', 'excerpt': 'Tăng trưởng 15%', 'provider': 'DuckDuckGo Web'}],
        'market_analysis': {'market_signals': {'signal_score': 78, 'extracted_figures': ['15%']}, 'executive_summary': 'Tóm tắt thực tế'}
    })
    with pytest.raises(HTTPException) as exc:
        analyze(AnalyzeRequest(dataset_name='sample.csv', product_name='Trà sữa Phê La', category='Food & Beverage'))
    assert exc.value.status_code == 422


def test_provider_configuration_never_calls_network_or_leaks_keys(client, monkeypatch):
    monkeypatch.setattr(research.settings, 'brave_search_api_key', SecretStr('private-brave-key'))
    monkeypatch.setattr(research.settings, 'tavily_api_key', SecretStr('private-tavily-key'))
    def no_network(*args, **kwargs):
        pytest.fail('Configuration discovery must not call a paid provider')
    monkeypatch.setattr(research, 'fetch_json', no_network)
    response = client.get('/api/research/providers')
    assert response.status_code == 200
    assert response.json()['web_search_configured'] is True
    assert len(response.json()['providers']) >= 4
    assert 'private-brave-key' not in response.text
    assert 'private-tavily-key' not in response.text


@pytest.mark.parametrize('failure', ['empty', 'unsafe', 401, 429, 503])
def test_tavily_fallback_on_primary_failure(client, monkeypatch, failure):
    monkeypatch.setattr(research.settings, 'research_wikipedia', False)
    monkeypatch.setattr(research.settings, 'brave_search_api_key', SecretStr('private-brave-key'))
    monkeypatch.setattr(research.settings, 'tavily_api_key', SecretStr('private-tavily-key'))
    calls = []
    def provider(url, headers, **kwargs):
        calls.append(url)
        if 'brave.com' in url:
            if isinstance(failure, int):
                raise HTTPError(url, failure, 'private provider error', {}, None)
            return {'web': {'results': [] if failure == 'empty' else [{'url': 'javascript:alert(1)'}]}}
        assert url == 'https://api.tavily.com/search'
        assert headers['Authorization'] == 'Bearer private-tavily-key'
        assert kwargs['payload']['query'] == 'Nghiên cứu một chủ đề bất kỳ'
        assert kwargs['payload']['include_answer'] is False
        assert kwargs['payload']['include_raw_content'] is False
        assert kwargs['payload']['auto_parameters'] is False
        return {'answer': 'Unsupported generated claim', 'results': [
            {'title': 'Nghiên cứu một chủ đề bất kỳ', 'url': 'https://example.org/article', 'content': '<b>Nội dung</b> có nguồn'}]}
    monkeypatch.setattr(research, 'fetch_json', provider)
    response = client.post('/api/research/search', json={'query': 'Nghiên cứu một chủ đề bất kỳ'})
    result = response.json()
    assert len(calls) == 2
    assert result['sources'][0]['provider'] == 'Tavily'
    assert result['sources'][0]['excerpt'] == 'Nội dung có nguồn'
    assert result['sources'][0]['verified'] is False
    assert result['web_search_configured'] is True
    assert all(value not in response.text for value in ['private-brave-key', 'private-tavily-key', 'private provider error', 'Unsupported generated claim'])
    statuses = {p['name']: p['status'] for p in result['providers']}
    assert statuses['Tavily'] == 'ok'
    assert statuses['Brave Search'] == ({401: 'authentication_failed', 429: 'rate_limited', 503: 'unavailable'}.get(failure, 'no_results'))


def test_tavily_can_be_only_configured_web_provider(client, monkeypatch):
    monkeypatch.setattr(research.settings, 'research_wikipedia', False)
    monkeypatch.setattr(research.settings, 'tavily_api_key', SecretStr('private-key'))
    def provider(url, headers, **kwargs):
        assert url == 'https://api.tavily.com/search'
        return {'results': [
            {'title': 'Từ khóa mới', 'url': 'https://example.org/article#section1', 'content': 'Trích đoạn'},
            {'title': 'Từ khóa mới trùng', 'url': 'https://example.org/article#section2', 'content': 'Trích đoạn'},
            {'title': 'Nội bộ', 'url': 'https://127.0.0.1/', 'content': 'Không hiển thị'}]}
    monkeypatch.setattr(research, 'fetch_json', provider)
    result = client.post('/api/research/search', json={'query': 'Từ khóa mới'}).json()
    assert len(result['sources']) == 1
    assert result['sources'][0]['url'] == 'https://example.org/article'


def test_successful_primary_also_queries_supplementary_source(client, monkeypatch):
    monkeypatch.setattr(research.settings, 'research_wikipedia', False)
    monkeypatch.setattr(research.settings, 'brave_search_api_key', SecretStr('brave-key'))
    monkeypatch.setattr(research.settings, 'tavily_api_key', SecretStr('tavily-key'))
    calls = []
    def provider(url, headers, **kwargs):
        calls.append(url)
        item = {'title': 'Chủ đề', 'url': 'https://example.org/article', 'description': 'Có kết quả', 'content': 'Có kết quả'}
        return {'web': {'results': [item]}} if 'brave.com' in url else {'results': [item]}
    monkeypatch.setattr(research, 'fetch_json', provider)
    result = client.post('/api/research/search', json={'query': 'Chủ đề'}).json()
    assert len(calls) == 2
    assert next(p for p in result['providers'] if p['name'] == 'Tavily')['status'] == 'ok'
    assert len(result['sources']) == 1  # deduplicated across providers


def test_wikidata_finds_alias_without_wikipedia_article(client, monkeypatch):
    monkeypatch.setattr(research.settings, 'research_wikidata', True)
    def provider(url, *args):
        if 'wikipedia.org' in url:
            return {'pages': []}
        assert url.startswith('https://www.wikidata.org/w/api.php?')
        assert 'action=wbsearchentities' in url
        return {'search': [{'id': 'Q123', 'label': 'Tên đầy đủ', 'description': 'Mô tả công khai'},
                           {'id': '../unsafe', 'label': 'Không dùng'}]}
    monkeypatch.setattr(research, 'fetch_json', provider)
    result = client.post('/api/research/search', json={'query': 'Tên viết tắt'}).json()
    assert len(result['sources']) == 1
    assert result['sources'][0]['url'] == 'https://www.wikidata.org/wiki/Q123'
    assert result['sources'][0]['identity_match'] is False
    assert result['sources'][0]['verified'] is False


@pytest.mark.parametrize('query', ['C', 'R', 'C++', 'C#', '人工智能', 'Đại học Thủ Dầu Một', 'Highland Coffee', 'một từ khóa chưa từng tồn tại 123xyz'])
def test_any_nonempty_topic_has_honest_empty_response(client, monkeypatch, query):
    monkeypatch.setattr(research, 'fetch_json', lambda *args, **kwargs: {'pages': []})
    response = client.post('/api/research/search', json={'query': query})
    assert response.status_code == 200
    result = response.json()
    assert result['sources'] == []
    assert result['status'] == 'insufficient_evidence'
    assert result['web_search_configured'] is True  # Wikipedia is configured; no result is not a disabled source
    assert result['next_steps']


@pytest.mark.parametrize('url', ['https://127.0.0.1/search', 'https://api.tavily.com.evil.example/search',
                               'https://api.tavily.com/other', 'http://api.tavily.com/search',
                               'https://username:password@api.tavily.com/search'])
def test_provider_fetch_cannot_target_arbitrary_urls(url):
    with pytest.raises(ValueError, match='Unsupported provider endpoint'):
        research.fetch_json(url)


@pytest.mark.parametrize('query', ['Gaming Laptop', 'iPhone', 'ROG Strix G16', 'Cà phê', 'Trà sữa Phê La', 'VinFast VF3'])
def test_market_overview_resolves_actionable_dataset_and_product(client, query):
    overview = client.get('/api/market-overview', params={'q': query}).json()
    assert overview['found'] is True
    md = overview['market_data']
    assert md and md['dataset_filename']
    assert len(md['top_items']) > 0
    products = client.get(f"/api/datasets/{md['dataset_filename']}/products").json()['products']
    assert md['target_product_name'] in products


def test_wide_web_search_ddg_and_google_news_and_market_analysis(client, monkeypatch):
    monkeypatch.setattr(research.settings, 'research_wikipedia', False)
    monkeypatch.setattr(research.settings, 'research_duckduckgo', True)
    monkeypatch.setattr(research.settings, 'research_google_news', True)

    def fake_fetch_text(url, headers=None, *, form_data=None):
        if 'duckduckgo.com' in url:
            return '<a class="result__a" href="https://phela.vn/">Phê La Ô Long</a><a class="result__snippet">Thương hiệu trà sữa tăng trưởng 25% với 30 cửa hàng</a>'
        if 'news.google.com' in url:
            return '<?xml version="1.0"?><rss><channel><item><title>Phê La mở rộng chuỗi trà Ô Long</title><link>https://news.google.com/rss/articles/123</link><source url="https://cafef.vn">CafeF</source><pubDate>Wed, 15 Oct 2025</pubDate><description>Doanh thu đạt 500 tỷ đồng</description></item></channel></rss>'
        raise AssertionError('Unexpected URL')

    monkeypatch.setattr(research, 'fetch_text', fake_fetch_text)
    res = client.post('/api/research/search', json={'query': 'Trà sữa Phê La'}).json()
    assert res['web_search_configured'] is True
    assert len(res['sources']) == 2
    ma = res['market_analysis']
    assert ma['detected_category'] == 'Food & Beverage'
    assert ma['recommended_dataset'] is None
    assert ma['market_signals']['signal_score'] is None
    assert '25%' in ma['market_signals']['extracted_figures'] or '500 tỷ đồng' in ma['market_signals']['extracted_figures']


def test_university_requires_real_observations_instead_of_edtech_sample(client, monkeypatch):
    monkeypatch.setattr(research.settings, 'research_wikipedia', False)
    overview = client.get('/api/market-overview', params={'q': 'Đại học Thủ Dầu Một'}).json()
    assert overview['found'] is False and overview['market_data'] is None
    for name, dataset in [('Đại học Thủ Dầu Một', 'smart_home_iot_devices.csv'), ('Đại học Bình Dương', 'education_edtech_courses.csv')]:
        with pytest.raises(HTTPException) as error:
            analyze(AnalyzeRequest(dataset_name=dataset, product_name=name, category='Education & EdTech'))
        assert error.value.status_code == 422


def test_gemini_tts_and_qa_advisor_endpoints(client):
    tts_res = client.post('/api/research/tts', json={
        'text': 'Báo cáo phân tích thị trường Đại học Thủ Dầu Một tăng trưởng tích cực.',
        'voice': 'Kore'
    })
    assert tts_res.status_code == 200
    tts_data = tts_res.json()
    assert tts_data['assistant_name'] == 'MarketWiseJu'
    assert 'model_used' not in tts_data
    assert tts_data['fallback_browser_tts'] is True
    assert tts_data['clean_text']

    ask_res = client.post('/api/research/ask', json={
        'query': 'Đại học Thủ Dầu Một',
        'question': 'Chiến lược cạnh tranh tuyển sinh ngành CNTT và Bán dẫn tại Bình Dương?',
        'context': {'category': 'Giáo dục & Đại học', 'potential_score': 82, 'growth_pct': 4.4}
    })
    assert ask_res.status_code == 200
    ask_data = ask_res.json()
    assert ask_data['answer']
    assert len(ask_data['key_points']) >= 2
    assert ask_data['assistant_name'] == 'MarketWiseJu'
    assert 'model_used' not in ask_data and 'routing_model' not in ask_data
    assert ask_data['confidence_pct'] is None




