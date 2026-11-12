from fastapi.testclient import TestClient
import main
from core.config import Settings, settings
from core.request_limits import RequestLimiter


def test_public_health_and_config_expose_no_credentials():
    with TestClient(main.app) as client:
        assert client.get('/api/health').json()['status'] == 'ok'
        config = client.get('/api/config').json()
        assert set(config) == {'public_demo', 'max_upload_mb'}


def test_database_resolves_inside_configured_storage(tmp_path):
    assert Settings(storage_dir=str(tmp_path)).database_path == tmp_path / 'marketwise.db'


def test_limiter_window_and_separate_clients(monkeypatch):
    import core.request_limits as limits
    now = [100.0]
    monkeypatch.setattr(limits, 'monotonic', lambda: now[0])
    limiter = RequestLimiter()
    assert limiter.allow('a', 1, 60)[0]
    assert limiter.allow('a', 1, 60) == (False, 61)
    assert limiter.allow('b', 1, 60)[0]
    now[0] += 60
    assert limiter.allow('a', 1, 60)[0]
    assert 'b' not in limiter.clients


def test_production_requests_are_bounded(monkeypatch):
    # An invalid analysis request exercises middleware without starting work.
    with TestClient(main.app) as client:
        monkeypatch.setattr(settings, 'environment', 'production')
        monkeypatch.setattr(settings, 'rate_limit_requests', 2)
        monkeypatch.setattr(main, 'request_limiter', RequestLimiter())
        assert client.post('/api/analyze', json={}).status_code == 422
        assert client.post('/api/analyze', json={}).status_code == 422
        response = client.post('/api/analyze', json={})
        assert response.status_code == 429
        assert int(response.headers['retry-after']) > 0
        assert client.get('/api/health').status_code == 200
