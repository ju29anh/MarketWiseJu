"""Regression checks for issues found during the final handover audit."""
import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.mark.parametrize('context', [
    {'potential_score': 'invalid'}, {'potential_score': -1}, {'potential_score': 101},
    {'growth_pct': 'invalid'}, {'growth_pct': 'NaN'}, {'growth_pct': 'Infinity'},
])
def test_advisor_context_is_validated(client, context):
    response = client.post('/api/research/ask', json={'query': 'Coffee', 'question': 'Xu hướng?', 'context': context})
    assert response.status_code == 422


def test_advisor_preserves_zero_metrics(client, monkeypatch):
    import routers.research as router
    monkeypatch.setattr(router, 'ask_market_ai', lambda **kwargs: kwargs)
    response = client.post('/api/research/ask', json={
        'query': 'Coffee', 'question': 'Xu hướng?', 'context': {'potential_score': 0, 'growth_pct': 0},
    })
    assert response.status_code == 200
    assert response.json()['potential_score'] == 0
    assert response.json()['growth_pct'] == 0


@pytest.mark.parametrize('field,value', [('product_name', '  '), ('product_name', ' a '), ('category', '  ')])
def test_analysis_rejects_blank_labels(client, field, value):
    payload = {'product_name': 'Coffee', 'category': 'Food', 'dataset_name': 'food_beverage_specialty_coffee.csv'}
    payload[field] = value
    assert client.post('/api/analysis/jobs', json=payload).status_code == 422


def test_malformed_xlsx_is_a_client_error_and_cleans_up(client, tmp_path, monkeypatch):
    import io
    from zipfile import ZipFile
    import services.upload as upload
    monkeypatch.setattr(upload, 'UPLOADS_DIR', tmp_path)
    content = io.BytesIO()
    with ZipFile(content, 'w') as archive:
        archive.writestr('unrelated.txt', 'Not an Excel workbook')
    response = client.post('/api/datasets/preview', files={'file': ('broken.xlsx', content.getvalue())})
    assert response.status_code == 400
    assert not list(tmp_path.iterdir())


def test_infinite_csv_is_a_client_error(client, tmp_path, monkeypatch):
    import services.upload as upload
    monkeypatch.setattr(upload, 'UPLOADS_DIR', tmp_path)
    response = client.post('/api/datasets/upload', files={'file': ('infinite.csv', b'price,sales\n1,inf\n2,3\n3,4\n4,5\n5,6')})
    assert response.status_code == 400
    assert not list(tmp_path.iterdir())


def test_sparse_entity_does_not_borrow_other_entities():
    import pandas as pd
    from ml_engine.preprocessor import DataPreprocessor
    frame = pd.DataFrame({'product_name': ['Small']*3 + ['Other']*8, 'sales': list(range(11)), 'price': list(range(11))})
    with pytest.raises(ValueError, match='ít nhất 4 quan sát riêng'):
        DataPreprocessor.extract_features(frame, {'item_col': 'product_name', 'sales_col': 'sales'}, product_name='Small')


def test_advisor_does_not_invent_missing_metrics(client):
    response = client.post('/api/research/ask', json={'query': 'Coffee', 'question': 'Xu hướng?'})
    assert response.status_code == 200
    result = response.json()
    assert result['assistant_name'] == 'MarketWiseJu'
    assert 'model_used' not in result
    assert result['confidence_pct'] is None
    assert 'chưa được cung cấp' in result['answer']


def test_catalog_quality_matches_actual_validation(client):
    datasets = client.get('/api/datasets').json()['datasets']
    for dataset in datasets:
        if dataset['filename'].startswith('upload_'):
            continue
        validation = client.post('/api/validate', json={'dataset_name': dataset['filename']}).json()
        assert dataset['quality_score'] == validation['quality_score']
        assert dataset['total_rows'] == validation['total_rows']


def test_oversized_request_keeps_security_headers(client):
    response = client.post('/api/analyze', content=b'{}', headers={'Content-Length': '9'*30})
    assert response.status_code == 413
    assert response.headers['x-content-type-options'] == 'nosniff'
    assert response.headers['x-request-id']


def test_weak_forecast_does_not_trigger_expansion():
    from ml_engine.strategy_engine import StrategyEngine
    result = StrategyEngine.generate_strategy('Coffee', 'Food',
        {'potential_score': 90, 'potential_level': 'HIGH'},
        {'trend_direction': 'Increasing', 'projected_growth_pct': 50, 'metrics': {'r2_score': -2}},
        {'classification_confidence': 99}, {'current_item_cluster': {'cluster_name': 'Premium'}})
    assert 'ƯU TIÊN XÁC MINH' in result['recommended_action']
    assert all(item.startswith('Giả thuyết cần kiểm nghiệm:') for item in result['opportunities'])


@pytest.mark.parametrize('quote', [
    'Trường Đại học Thủ Dầu Một đăng cai Hội thảo Quốc gia năm 2027.',
    'Trường Đại học Thủ Dầu Một đánh giá chất lượng chương trình đào tạo.',
    'Trường Đại học Thủ Dầu Một tổ chức hoạt động văn hóa đọc cho sinh viên.',
])
def test_general_news_is_not_pricing_evidence(quote):
    from services.subject_report import extracted_claim
    source = {'title': 'Đại học Thủ Dầu Một', 'excerpt': quote, 'source_id': 'S1'}
    assert extracted_claim('Đại học Thủ Dầu Một', source, 'pricing') is None


@pytest.mark.parametrize('quote', [
    'Trường Đại học Thủ Dầu Một công bố học phí theo chương trình năm 2026.',
    'Trường Đại học Thủ Dầu Một công bố giá 500.000 đồng cho khóa học ngắn hạn.',
])
def test_explicit_pricing_evidence_is_kept(quote):
    from services.subject_report import extracted_claim
    source = {'title': 'Đại học Thủ Dầu Một', 'excerpt': quote, 'source_id': 'S1'}
    assert extracted_claim('Đại học Thủ Dầu Một', source, 'pricing')['quote'] == quote


def test_reading_legacy_session_is_stable_and_performs_no_ai_calls(monkeypatch):
    import database
    import services.ai_engine as ai
    from datetime import datetime
    payload = {'session_id': 'handover-legacy', 'product_name': 'Coffee', 'category': 'Food',
        'description': '', 'dataset_name': 'coffee.csv', 'quality_score': 80, 'potential_score': 70,
        'potential_level': 'HIGH', 'regression': {}, 'classification': {}, 'clustering': {},
        'strategy_recommendation': {'market_overview': 'Original saved report'}}
    database.save_analysis_session(payload)
    def forbidden(*args, **kwargs):
        pytest.fail('Opening a saved report must not call AI or rewrite the database')
    monkeypatch.setattr(ai, 'build_domain_specific_strategy', forbidden)
    monkeypatch.setattr(database, 'save_analysis_session', forbidden)
    first = database.get_analysis_session_by_id('handover-legacy')
    second = database.get_analysis_session_by_id('handover-legacy')
    assert first == second == payload
    assert datetime.fromisoformat(first['created_at']).tzinfo is not None
