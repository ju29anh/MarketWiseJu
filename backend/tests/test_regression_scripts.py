"""Run legacy scripts as real regression checks without changing their assertions."""
import os
import subprocess
import sys
from pathlib import Path
import pytest


@pytest.mark.parametrize('filename', ['test_backend.py', 'test_api_endpoints.py', 'test_all_datasets.py'])
def test_legacy_script(filename, tmp_path):
    env = dict(os.environ, DATABASE_URL='sqlite:///' + str(tmp_path / 'legacy.db'), PYTHONIOENCODING='utf-8')
    result = subprocess.run([sys.executable, str(Path(__file__).with_name(filename))], env=env,
                            capture_output=True, text=True, encoding='utf-8', timeout=180)
    assert result.returncode == 0, result.stdout + result.stderr
    assert '=== FAILED:' not in result.stdout, result.stdout
