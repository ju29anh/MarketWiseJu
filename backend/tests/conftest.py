"""Keep HTTP/regression checks isolated from the user's SQLite database."""
import os
import sys
import tempfile
from pathlib import Path

# Match the container's CPU bounds before NumPy / OpenMP are imported.
for thread_setting in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[thread_setting] = '1'

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
_storage = tempfile.TemporaryDirectory(prefix='marketwise-tests-')
os.environ['DATABASE_URL'] = 'sqlite:///' + str(Path(_storage.name) / 'test.db')
os.environ['ENVIRONMENT'] = 'test'
os.environ['ENABLE_WIKIPEDIA'] = 'false'
os.environ['RESEARCH_FETCH_PAGES'] = 'false'
# Tests and legacy subprocesses must never inherit real provider credentials.
for provider_key in ('GEMINI_API_KEY', 'BRAVE_SEARCH_API_KEY', 'TAVILY_API_KEY'):
    os.environ[provider_key] = ''
for provider_flag in ('RESEARCH_WIKIPEDIA', 'RESEARCH_WIKIDATA', 'RESEARCH_DUCKDUCKGO', 'RESEARCH_GOOGLE_NEWS', 'RESEARCH_OPENALEX'):
    os.environ[provider_flag] = 'false'
os.environ['ALLOWED_ORIGINS'] = 'http://localhost:5173'
os.environ['LOKY_MAX_CPU_COUNT'] = '4'


def pytest_configure(config):
    if not config.option.basetemp:
        config.option.basetemp = str(Path(_storage.name) / 'pytest-tmp')
    config._inicache['cache_dir'] = str(Path(_storage.name) / 'pytest-cache')
