"""Check a same-origin deployment; --exercise also creates one sample analysis."""
import argparse
import re
import time
from urllib.parse import quote

import httpx


def check(base_url, exercise=False):
    checks = 0
    def passed(label):
        nonlocal checks
        checks += 1
        print(f'PASS {label}', flush=True)

    with httpx.Client(base_url=base_url.rstrip('/'), timeout=120, trust_env=False) as client:
        page = client.get('/')
        assert page.status_code == 200 and 'text/html' in page.headers.get('content-type', '')
        assets = re.findall(r'(?:src|href)="(/assets/[^"]+)"', page.text)
        assert assets, 'Frontend production assets missing'
        assert not re.search(r'<script(?![^>]*\bsrc=)[^>]*>\s*\S', page.text), 'Inline script blocked by production CSP'
        assert "script-src 'self'" in page.headers.get('content-security-policy', '')
        assert page.headers.get('x-frame-options') == 'DENY'
        assert page.headers.get('x-content-type-options') == 'nosniff'
        if base_url.startswith('https://'):
            assert 'max-age=' in page.headers.get('strict-transport-security', ''), 'HTTPS must provide HSTS (check trusted proxy configuration)'
        passed('production HTML')
        for asset in assets + ['/theme.js']:
            response = client.get(asset)
            assert response.status_code == 200
            assert 'text/html' not in response.headers.get('content-type', '')
            assert not re.search(r'http://(?:localhost|127\.0\.0\.1):(?:8000|5173)', response.text)
        passed('frontend assets and same-origin API configuration')
        assert client.get('/api/health').json()['status'] == 'ok'
        config = client.get('/api/config').json()
        assert set(config) == {'max_upload_mb', 'public_demo'}
        passed('health and public configuration')
        assert len(client.get('/api/categories').json()['categories']) >= 16
        datasets = client.get('/api/datasets').json()['datasets']
        bundled = [d for d in datasets if not d['filename'].startswith('upload_')]
        assert len(bundled) >= 16
        for dataset in bundled:
            response = client.get('/api/datasets/' + quote(dataset['filename'], safe='') + '/products')
            assert response.status_code == 200 and response.json()['products']
        passed(f'{len(bundled)} datasets and product lists')
        assert client.get('/api/dashboard/stats').status_code == 200
        assert client.get('/api/research/providers').status_code == 200
        passed('dashboard and research provider configuration')
        for path in ('/.env', '/.env.example', '/backend/.env', '/frontend/.env', '/.git/config',
                     '/main.py', '/marketwise.db', '/docs', '/redoc', '/openapi.json', '/api/unknown', '/api/analysis/missing'):
            response = client.get(path)
            assert response.status_code == 404, path
            assert response.headers.get('x-content-type-options') == 'nosniff', path
            assert response.headers.get('cache-control') == 'no-store', path
        passed('private files and unknown resources return 404')
        template = client.get('/api/datasets/template')
        assert template.status_code == 200 and 'text/csv' in template.headers['content-type']
        passed('downloadable CSV template')
        if exercise:
            upload = client.post('/api/datasets/upload', files={'file': ('release-sample.csv', template.content, 'text/csv')})
            assert upload.status_code == 200, upload.text
            payload = {'dataset_name': upload.json()['filename'], 'product_name': 'Sample product', 'category': 'Release audit'}
            response = client.post('/api/analysis/jobs', json=payload)
            assert response.status_code == 202, response.text
            job_id = response.json()['job_id']
            deadline = time.monotonic() + 120
            while time.monotonic() < deadline:
                response = client.get(f'/api/analysis/jobs/{job_id}')
                assert response.status_code == 200
                job = response.json()
                if job['status'] in ('complete', 'failed'):
                    break
                time.sleep(.7)
            assert job['status'] == 'complete', job
            result = client.get('/api/analysis/' + job['session_id'])
            assert result.status_code == 200 and result.json()['regression']['future_forecast']
            evaluation = client.get('/api/analysis/' + job['session_id'] + '/model-eval')
            assert evaluation.status_code == 200
            passed('template upload, queued ML, persisted report and model evaluation')
    print(f'Completed: {checks} checks passed.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url', nargs='?', default='http://127.0.0.1:8001')
    parser.add_argument('--exercise', action='store_true', help='Create one dataset and analysis using public sample data')
    args = parser.parse_args()
    check(args.url, args.exercise)
