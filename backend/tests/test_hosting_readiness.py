"""Regressions for configuration, public file roots and error response protections."""
import base64
import json

import pytest
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

import main
from core.config import BACKEND_DIR, Settings, settings
from core.request_limits import RequestLimiter


def test_template_documents_every_application_setting():
    assert {key.upper() for key in Settings.model_fields} <= set(dotenv_values(BACKEND_DIR / '.env.example'))


def test_production_cannot_be_bypassed_with_environment_spelling():
    assert Settings(environment=' Production ').environment == 'production'
    with pytest.raises(ValidationError):
        Settings(environment='prodution')
    with pytest.raises(ValueError, match='SECRET_KEY'):
        Settings(environment='Production', secret_key='short').validate_runtime()


def test_public_binding_requires_explicit_demo_acknowledgement():
    config = Settings(host='0.0.0.0', secret_key=SecretStr('test-only-' * 6))
    with pytest.raises(ValueError, match='PUBLIC_DEMO'):
        config.validate_runtime()
    config.public_demo = True
    config.validate_runtime()
    config.public_demo = False
    config.host = '127.0.0.1'
    config.validate_runtime()


@pytest.mark.parametrize('private_file', ['.env', 'assets/private.key', '.git/config'])
def test_static_root_rejects_source_and_private_files(tmp_path, private_file):
    for path in (BACKEND_DIR, BACKEND_DIR.parent, BACKEND_DIR / 'datasets'):
        with pytest.raises(ValueError, match='outside backend'):
            Settings(environment='test', static_dir=str(path)).validate_runtime()
    (tmp_path / 'index.html').write_text('<html></html>')
    (tmp_path / 'assets').mkdir()
    config = Settings(environment='test', static_dir=str(tmp_path))
    config.validate_runtime()
    secret_file = tmp_path / private_file
    secret_file.parent.mkdir(exist_ok=True)
    secret_file.write_text('TEST_ONLY=example')
    with pytest.raises(ValueError, match='private'):
        config.validate_runtime()


@pytest.mark.parametrize('kind,status', [('validation', 422), ('length', 413), ('stream', 413), ('cors', 400), ('failure', 500), ('rate', 429)])
def test_security_headers_cover_early_and_unhandled_errors(monkeypatch, kind, status):
    with TestClient(main.app, raise_server_exceptions=False, base_url='https://testserver') as client:
        monkeypatch.setattr(settings, 'environment', 'production')
        monkeypatch.setattr(settings, 'max_upload_mb', 1)
        monkeypatch.setattr(settings, 'rate_limit_requests', 1)
        monkeypatch.setattr(main, 'request_limiter', RequestLimiter())
        if kind == 'validation':
            response = client.post('/api/analyze', json={})
        elif kind == 'length':
            response = client.post('/api/analyze', content=b'{}', headers={'Content-Length': '99999999'})
        elif kind == 'stream':
            response = client.post('/api/analyze', content=iter([b'x' * 65536] * 18), headers={'Content-Type': 'application/json'})
        elif kind == 'cors':
            response = client.options('/api/analyze', headers={'Origin': 'https://untrusted.invalid', 'Access-Control-Request-Method': 'POST'})
        elif kind == 'rate':
            client.post('/api/analyze', json={})
            response = client.post('/api/analyze', json={})
        else:
            import services.catalog as catalog
            def fail():
                raise RuntimeError('private-test-only-value')
            monkeypatch.setattr(catalog, 'get_dashboard_summary', fail)
            response = client.get('/api/dashboard/stats')
        assert response.status_code == status, response.text
        assert response.headers['x-frame-options'] == 'DENY'
        assert response.headers['x-content-type-options'] == 'nosniff'
        assert response.headers['cache-control'] == 'no-store'
        assert "script-src 'self'" in response.headers['content-security-policy']
        assert response.headers['strict-transport-security'] == 'max-age=31536000'
        assert len(response.headers['x-request-id']) == 32
        assert 'private-test-only-value' not in response.text
        if kind == 'failure':
            assert response.json()['request_id'] == response.headers['x-request-id']


@pytest.mark.parametrize('tts', [False, True])
def test_ai_credentials_stay_out_of_urls_and_redirects(monkeypatch, tts):
    from services import ai_engine
    from services.research import NoRedirect
    monkeypatch.setattr(settings, 'gemini_api_key', SecretStr('test-only-provider-key'))
    monkeypatch.setattr(ai_engine, 'is_ai_configured', lambda: True)
    requests = []

    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, limit):
            part = {'inlineData': {'data': base64.b64encode(b'RIFFtest-audio').decode(), 'mimeType': 'audio/wav'}} if tts else {'text': '{"answer":"test"}'}
            return json.dumps({'candidates': [{'content': {'parts': [part]}}]}).encode()

    class Opener:
        def open(self, request, **kwargs):
            requests.append(request)
            return Response()

    def opener(handler):
        assert handler is NoRedirect
        return Opener()

    monkeypatch.setattr(ai_engine, 'build_opener', opener)
    if tts:
        assert ai_engine.generate_tts_briefing('Bản tin thử')['audio_base64']
    else:
        assert ai_engine.call_gemini_json('test')[0] == {'answer': 'test'}
    assert len(requests) == 1
    request = requests[0]
    assert '?' not in request.full_url and 'test-only-provider-key' not in request.full_url
    assert request.get_header('X-goog-api-key') == 'test-only-provider-key'
    assert json.loads(request.data)['contents'][0]['role'] == 'user'
