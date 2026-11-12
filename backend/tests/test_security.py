import io
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from main import app
from core.config import settings
from core.serialization import np_clean
from services import upload as upload_service


@pytest.fixture
def client(tmp_path, monkeypatch):
    import services.datasets as datasets
    monkeypatch.setattr(upload_service, 'UPLOADS_DIR', tmp_path)
    monkeypatch.setattr(upload_service, 'BACKEND_DIR', tmp_path)
    monkeypatch.setattr(datasets, 'UPLOADS_DIR', tmp_path)
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def sample_csv():
    return ('product_name,price,sales,search_volume,growth_rate,rating\n' + '\n'.join(
        f'Sample,{10+i},{100+i*10},{200+i*20},{2+i/10},4.5' for i in range(30))).encode()


@pytest.mark.parametrize('name', ['../database.py', '..\\database.py', 'C:\\secret.csv', '/etc/passwd', 'file.csv:secret'])
def test_path_traversal_rejected(client, name):
    assert client.post('/api/validate', json={'dataset_name': name}).status_code == 422


def test_validation_never_echoes_input(client):
    response = client.post('/api/analyze', json={'dataset_name': '../secret', 'product_name': 'x'})
    assert response.status_code == 422
    assert '../secret' not in response.text and 'input' not in response.text


def test_cors_only_explicit_origins(client):
    for origin, expected in [('http://localhost:5173', 200), ('https://untrusted.invalid', 400)]:
        response = client.options('/api/datasets', headers={'Origin': origin, 'Access-Control-Request-Method': 'POST'})
        assert response.status_code == expected
        assert response.headers.get('access-control-allow-origin') == (origin if expected == 200 else None)


def test_security_headers(client):
    response = client.get('/api/datasets')
    assert response.headers['x-content-type-options'] == 'nosniff'
    assert response.headers['cache-control'] == 'no-store'
    assert len(response.headers['x-request-id']) == 32


def test_upload_preview_csv_and_no_persistence(client, tmp_path):
    response = client.post('/api/datasets/preview', files={'file': ('sample.csv', sample_csv())})
    assert response.status_code == 200, response.text
    assert response.json()['total_rows'] == 30
    assert len(response.json()['rows']) == 5
    assert list(tmp_path.iterdir()) == []


def test_upload_supports_storage_outside_application(client, tmp_path, monkeypatch):
    monkeypatch.setattr(upload_service, 'BACKEND_DIR', tmp_path / 'application')
    response = client.post('/api/datasets/upload', files={'file': ('sample.csv', sample_csv())})
    assert response.status_code == 200, response.text
    payload = response.json()
    assert (tmp_path / payload['filename']).exists()
    assert client.post('/api/validate', json={'dataset_name': payload['filename']}).json()['valid']


def test_xlsx_upload_normalizes_and_ignores_path(client, tmp_path):
    output = io.BytesIO()
    pd.read_csv(io.BytesIO(sample_csv())).to_excel(output, index=False)
    response = client.post('/api/datasets/upload', files={'file': ('../../unsafe.XLSX', output.getvalue())})
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload['filename'].startswith('upload_') and payload['filename'].endswith('.csv')
    assert '..' not in payload['filename']
    assert (tmp_path / payload['filename']).exists()
    assert client.post('/api/validate', json={'dataset_name': payload['filename']}).json()['valid']
    assert not list(tmp_path.glob('*.tmp'))


@pytest.mark.parametrize('name,data', [('bad.exe', b'MZ'), ('empty.csv', b''), ('text.csv', b'a,b\none,two'), ('bad.xlsx', b'not a zip')])
def test_invalid_upload_cleanup(client, tmp_path, name, data):
    response = client.post('/api/datasets/upload', files={'file': (name, data)})
    assert response.status_code == 400, response.text
    assert not list(tmp_path.iterdir())


def test_upload_limits(client, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'max_upload_mb', 1)
    response = client.post('/api/datasets/upload', files={'file': ('large.csv', b'a' * (1024**2 + 1))})
    assert response.status_code == 413
    monkeypatch.setattr(settings, 'max_dataset_rows', 10)
    response = client.post('/api/datasets/upload', files={'file': ('sample.csv', sample_csv())})
    assert response.status_code == 413
    assert not list(tmp_path.iterdir())


def test_finite_json():
    assert json.dumps(np_clean({'array': np.array([np.nan, np.inf, 2]), 'scalar': float('-inf')}), allow_nan=False)
    assert np_clean(np.float64('nan')) is None


def test_async_analysis_and_model_eval(client):
    response = client.post('/api/analysis/jobs', json={'product_name': 'Geisha Honey Process', 'category': 'Food & Beverage', 'dataset_name': 'food_beverage_specialty_coffee.csv'})
    assert response.status_code == 202, response.text
    job_id = response.json()['job_id']
    seen_steps = []
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        job = client.get(f'/api/analysis/jobs/{job_id}').json()
        seen_steps.append(job['step'])
        if job['status'] in ('complete', 'failed'):
            break
        time.sleep(.05)
    assert job['status'] == 'complete', job
    assert seen_steps == sorted(seen_steps)
    session = client.get('/api/analysis/' + job['session_id'])
    assert session.status_code == 200, session.text
    evaluation = client.get('/api/analysis/' + job['session_id'] + '/model-eval')
    assert evaluation.status_code == 200, evaluation.text
    assert len(evaluation.json()['classification']) == 2


def test_jobs_reject_missing_files(client):
    response = client.post('/api/analysis/jobs', json={'product_name': 'Coffee', 'category': 'Food', 'dataset_name': 'missing.csv'})
    assert response.status_code == 404
    assert client.get('/api/analysis/jobs/unknown').status_code == 404


def test_template_valid(client):
    response = client.get('/api/datasets/template')
    assert response.status_code == 200
    assert client.post('/api/datasets/upload', files={'file': ('template.csv', response.content)}).status_code == 200


def test_global_exception_does_not_leak(client, monkeypatch):
    import services.catalog as catalog
    def fail():
        raise RuntimeError('private-password-filesystem-path')
    monkeypatch.setattr(catalog, 'get_dashboard_summary', fail)
    response = client.get('/api/dashboard/stats')
    assert response.status_code == 500
    assert 'private-password' not in response.text
    assert 'request_id' in response.json()


def test_custom_roles_must_exist(client):
    response = client.post('/api/analyze', json={'product_name': 'Coffee', 'category': 'Food',
        'dataset_name': 'food_beverage_specialty_coffee.csv', 'custom_roles': {'sales_col': 'missing'}})
    assert response.status_code == 400


def test_database_failure_rolls_back_file(client, tmp_path, monkeypatch):
    def fail():
        raise RuntimeError('test storage unavailable')
    monkeypatch.setattr(upload_service, 'get_db_connection', fail)
    response = client.post('/api/datasets/upload', files={'file': ('sample.csv', sample_csv())})
    assert response.status_code == 500
    assert not list(tmp_path.iterdir())


def test_chunked_body_limit(client, monkeypatch):
    monkeypatch.setattr(settings, 'max_upload_mb', 1)
    boundary = b'marketwise-test'
    def chunks():
        yield b'--' + boundary + b'\r\nContent-Disposition: form-data; name="file"; filename="large.csv"\r\n\r\n'
        for _ in range(18):
            yield b'a' * 65536
        yield b'\r\n--' + boundary + b'--\r\n'
    response = client.post('/api/datasets/upload', content=chunks(), headers={'Content-Type': 'multipart/form-data; boundary=marketwise-test'})
    assert response.status_code == 413, response.text


def test_zip_bomb_limit(client, monkeypatch):
    from zipfile import ZipFile, ZIP_DEFLATED
    monkeypatch.setattr(settings, 'max_dataset_memory_mb', 1)
    output = io.BytesIO()
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        archive.writestr('xl/worksheets/sheet1.xml', b'a' * (1024**2 + 1))
    assert client.post('/api/datasets/upload', files={'file': ('bomb.xlsx', output.getvalue())}).status_code == 413


def test_queue_bounds_and_expiry(monkeypatch):
    from services.jobs import JobManager
    from schemas.analysis import AnalyzeRequest
    from fastapi import HTTPException
    manager = JobManager()
    monkeypatch.setattr(manager.executor, 'submit', lambda *args: None)
    monkeypatch.setattr(settings, 'max_pending_jobs', 1)
    request = AnalyzeRequest(product_name='Coffee', category='Food', dataset_name='sample.csv')
    try:
        job = manager.submit(request)
        with pytest.raises(HTTPException) as error:
            manager.submit(request)
        assert error.value.status_code == 429
        manager._update(job['job_id'], status='complete')
        manager.jobs[job['job_id']]['_updated'] -= settings.job_ttl_seconds + 1
        with pytest.raises(HTTPException) as error:
            manager.get(job['job_id'])
        assert error.value.status_code == 404
        assert manager.submit(request)['status'] == 'queued'
    finally:
        manager.shutdown()
