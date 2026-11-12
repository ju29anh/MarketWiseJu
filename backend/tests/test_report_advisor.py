import json
from urllib.error import HTTPError

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import SecretStr
from main import app
from schemas.advisor import ChatRequest, AdvisorDraft
from services import advisor
from services.research_evidence import subject_context


def draft(**changes):
    value = {'answer': 'Nên thử hai mẫu váy trước khi nhập thêm hàng; đây là phương án cần kiểm nghiệm.',
             'assumptions': ['Chưa có dữ liệu chi phí hoặc nhu cầu mua thực tế.'],
             'steps': [{'title': 'Kiểm tra mẫu và bảng size', 'when': 'Ngày 1–2 (đề xuất)',
                        'action': 'Xin ảnh thật, bảng size và báo giá vốn cho hai mẫu váy xòe.',
                        'deliverable': 'Bảng giá vốn và số đo của từng mẫu.',
                        'decision_rule': 'Chưa lấy được giá vốn thì chưa chốt giá bán hoặc nhập thêm.'}],
             'questions': ['Bạn có bao nhiêu vốn để thử?'], 'evidence': []}
    value.update(changes)
    return AdvisorDraft.model_validate(value)


@pytest.fixture(autouse=True)
def isolate_chat(monkeypatch):
    advisor._chats.clear()
    monkeypatch.setattr(advisor, 'available_models', lambda: ['models/gemini-test-flash'])
    yield
    advisor._chats.clear()


def test_classifier_handles_product_idea_without_confusing_loans():
    assert subject_context('Váy xòe dành cho GenZ')['category'] == 'Fashion & E-Commerce'
    assert subject_context('chan vay di hoc')['category'] == 'Fashion & E-Commerce'
    assert subject_context('vay vốn kinh doanh')['category'] != 'Fashion & E-Commerce'


def test_chat_uses_server_context_and_keeps_followup(monkeypatch):
    identity = advisor.save_research_context('Váy xòe dành cho GenZ', [])
    calls = []
    def generate(context, sources, history, question):
        calls.append((context['query'], len(history), [t['question'] for t in history], question))
        return draft(), [], 'gemini-test-flash'
    monkeypatch.setattr(advisor, 'generate_reply', generate)
    with TestClient(app) as client:
        first = client.post('/api/research/chat', json={'research_id': identity, 'question': 'Vốn 0 đồng, làm trong 14 ngày.'})
        assert first.status_code == 200
        data = first.json()
        assert data['confidence_pct'] is None
        assert data['assistant_name'] == 'MarketWiseJu'
        assert 'model_used' not in data
        second = client.post('/api/research/chat', json={'research_id': identity,
            'conversation_id': data['conversation_id'], 'question': 'Chỉ làm qua kênh online thì sao?'})
        assert second.status_code == 200
        assert calls[1][1] == 1
        assert calls[1][2] == ['Vốn 0 đồng, làm trong 14 ngày.']
        assert calls[1][0] == 'Váy xòe dành cho GenZ'
        mismatch = client.post('/api/research/chat', json={'research_id': advisor.save_research_context('Coffee', []),
            'conversation_id': data['conversation_id'], 'question': 'Tôi muốn tiếp tục.'})
        assert mismatch.status_code == 409


@pytest.mark.parametrize('extra', [{'sources': []}, {'history': []}, {'context': {'growth_pct': 999}}])
def test_client_cannot_forge_sources_or_metrics(extra):
    with TestClient(app) as client:
        response = client.post('/api/research/chat', json={'research_id': 'a'*32, 'question': 'Kế hoạch?', **extra})
        assert response.status_code == 422


@pytest.mark.parametrize('payload', [
    {'question': '  ', 'research_id': 'a'*32}, {'question': 'Hi', 'research_id': '../bad'},
    {'question': 'Hi'}, {'question': 'Hi', 'analysis_id': 'mw_'+'a'*10, 'research_id': 'a'*32},
    {'question': 'a'*1601, 'research_id': 'a'*32},
])
def test_chat_rejects_invalid_requests(payload):
    with TestClient(app) as client:
        assert client.post('/api/research/chat', json=payload).status_code == 422


def test_missing_report_and_expired_conversation_are_explicit():
    with TestClient(app) as client:
        assert client.post('/api/research/chat', json={'analysis_id': 'mw_'+'a'*10, 'question': 'Giải thích?'}).status_code == 404
        identity = advisor.save_research_context('Váy xòe', [])
        assert client.post('/api/research/chat', json={'research_id': identity, 'question': 'Giải thích?',
            'conversation_id': 'b'*32}).status_code == 410


def test_evidence_must_match_server_text():
    sources = [{'source_id': 'S1', 'url': 'https://example.com/vay', 'title': 'Bảng mẫu',
                'excerpt': 'Mẫu váy xòe có bảng size riêng cho từng chất liệu.', 'content': ''}]
    reply = draft(evidence=[{'quote_id': 'S1Q1'}])
    assert advisor.validate_evidence(reply, sources)[0]['url'] == sources[0]['url']
    assert advisor.validate_evidence(reply, sources)[0]['quote'] == sources[0]['excerpt']
    with pytest.raises(ValueError):
        advisor.validate_evidence(draft(evidence=[{'source_id': 'S1', 'quote': 'Thị phần mẫu váy này đã tăng 90 phần trăm.'}]), sources)
    with pytest.raises(ValueError):
        advisor.validate_evidence(draft(evidence=[{'quote_id': 'S2Q1'}]), sources)
    with pytest.raises(ValueError):
        advisor.validate_evidence(draft(answer='Mở https://fake.example để kiểm tra thông tin'), sources)


def test_server_passages_preserve_original_text_and_bound_size():
    text = 'Mẫu váy có bảng size riêng. ' + ('Chất liệu cotton được mô tả trong tài liệu này ' * 70)
    source = {'source_id': 'S1', 'excerpt': text, 'content': text, 'url': 'https://example.com/size'}
    passages = advisor.source_quotes([source])
    assert 1 <= len(passages) <= 8
    for identity, value in passages.items():
        assert identity.startswith('S1Q')
        assert 16 <= len(value['quote']) <= 450
        assert value['quote'] in text


def test_ad_copy_cannot_introduce_a_price_without_input_or_source():
    reply = draft(answer='Thông điệp thử: váy xòe năng động, giá chỉ 250k.')
    with pytest.raises(ValueError, match='Unsupported selling price'):
        advisor.validate_prices(reply, 'Ngân sách tối đa 5 triệu đồng')
    advisor.validate_prices(reply, 'Giá vốn mẫu hiện có là 250k.')
    advisor.validate_prices(draft(answer='Dành tối đa 1 triệu đồng cho thử nội dung, đây là khoản chi đề xuất.'), '')
    advisor.validate_prices(draft(answer='Thông điệp thử: váy xòe, giá [chốt sau khi tính giá vốn].'), '')


def test_sources_exclude_variants_and_unsafe_links():
    identity = advisor.save_research_context('Váy xòe', [
        {'match_status': 'exact', 'url': 'https://example.com/dress', 'excerpt': 'Váy xòe có bảng size.'},
        {'match_status': 'variant', 'url': 'https://example.com/other', 'excerpt': 'Đối tượng khác.'},
        {'match_status': 'exact', 'url': 'http://127.0.0.1/admin', 'excerpt': 'Nội bộ.'},
    ])
    _, sources = advisor.load_context(ChatRequest(research_id=identity, question='Lập kế hoạch?'))
    assert len(sources) == 1
    assert sources[0]['source_id'] == 'S1'


def test_ml_context_retains_macro_scope_without_template_strategies(monkeypatch):
    monkeypatch.setattr(advisor, 'get_analysis_session_by_id', lambda _: {
        'product_name': 'Váy xòe', 'category': 'Fashion & E-Commerce',
        'evidence_scope': {'analysis_mode': 'national_reference', 'scope_label': 'GDP Việt Nam'},
        'data_context': {'unit': 'USD', 'indicator_label': 'GDP bình quân'},
        'regression': {'validation': {'beats_baseline': False}},
        'strategy_plan': {'conclusion': 'Không được xem mẫu này là dữ kiện'},
    })
    context, _ = advisor.load_context(ChatRequest(analysis_id='mw_'+'a'*10, question='Có nên bán?'))
    assert context['scope']['analysis_mode'] == 'national_reference'
    assert context['regression']['validation']['beats_baseline'] is False
    assert 'strategy_plan' not in context


def fake_opener(monkeypatch, draft_value=None, code=None, finish='STOP', captured=None):
    monkeypatch.setattr(advisor.settings, 'gemini_api_key', SecretStr('private-test-key'))
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, _):
            return json.dumps({'candidates': [{'finishReason': finish, 'content': {'parts': [
                {'text': json.dumps(draft_value if draft_value is not None else draft().model_dump())}]}}]}).encode()
    class Opener:
        def open(self, request, timeout):
            if captured is not None: captured.append(json.loads(request.data))
            if code: raise HTTPError(request.full_url, code, 'private-test-key', {}, None)
            return Response()
    monkeypatch.setattr(advisor, 'build_opener', lambda *_: Opener())


def test_real_model_label_and_constraints_history(monkeypatch):
    captured = []
    fake_opener(monkeypatch, captured=captured)
    history = [{'question': f'Ràng buộc {i}: ngân sách 0 đồng', 'draft': draft().model_dump()} for i in range(8)]
    _, _, model = advisor.generate_reply({'query': 'Váy'}, [], history, 'Hãy sửa bước 2')
    assert model == 'gemini-test-flash'
    assert 'Ràng buộc 0' in captured[0]['contents'][0]['parts'][0]['text']
    assert 'responseJsonSchema' in captured[0]['generationConfig']
    assert 'private-test-key' not in json.dumps(captured)


@pytest.mark.parametrize('code,status', [(429, 429), (401, 503), (503, 503)])
def test_provider_failure_never_returns_fake_ai_success(monkeypatch, code, status):
    fake_opener(monkeypatch, code=code)
    with pytest.raises(HTTPException) as error:
        advisor.generate_reply({'query': 'Váy'}, [], [], 'Kế hoạch?')
    assert error.value.status_code == status
    assert 'private-test-key' not in error.value.detail


@pytest.mark.parametrize('value,finish', [({'answer': 'Thiếu cấu trúc'}, 'STOP'), (None, 'MAX_TOKENS')])
def test_malformed_or_truncated_ai_response_is_not_published(monkeypatch, value, finish):
    fake_opener(monkeypatch, draft_value=value, finish=finish)
    with pytest.raises(HTTPException) as error:
        advisor.generate_reply({'query': 'Váy'}, [], [], 'Kế hoạch?')
    assert error.value.status_code == 502


def test_failed_first_turn_does_not_leak_empty_sessions(monkeypatch):
    identity = advisor.save_research_context('Váy', [])
    def fail(*_): raise HTTPException(503, 'Gemini không khả dụng.')
    monkeypatch.setattr(advisor, 'generate_reply', fail)
    with pytest.raises(HTTPException):
        advisor.chat(ChatRequest(research_id=identity, question='Kế hoạch?'))
    assert not advisor._chats
