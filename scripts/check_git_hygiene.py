"""Inspect staged filenames/content without echoing possible secret values."""
import re
import subprocess
import sys
from pathlib import PurePosixPath


def git(*args):
    return subprocess.check_output(['git', *args], stderr=subprocess.PIPE)


try:
    git('rev-parse', '--show-toplevel')
except subprocess.CalledProcessError:
    sys.exit('No Git repository. Initialize/clone first, then run this before commit.')

paths = git('diff', '--cached', '--name-only', '--diff-filter=ACMR', '-z').decode().split('\0')
blocked = []
patterns = [r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
            r'\bAKIA[0-9A-Z]{16}\b', r'\bgh[pousr]_[A-Za-z0-9]{30,}\b',
            r'\bsk-[A-Za-z0-9_-]{32,}\b',
            r'''(?i)(?:api_key|secret_key|password)\s*[:=]\s*["'][^"'\s]{24,}["']''']
for name in filter(None, paths):
    path = PurePosixPath(name)
    if ((path.name.startswith('.env') and path.name != '.env.example') or
        path.suffix.lower() in {'.db', '.sqlite', '.sqlite3', '.pem', '.key', '.pyc'} or
        any(part in {'node_modules', '.venv', 'venv', '__pycache__', 'dist', '.test-artifacts', 'uploads'} for part in path.parts)):
        blocked.append((name, 'runtime or sensitive file'))
        continue
    if path.name.endswith('.example'):
        continue
    content = git('show', ':' + name).decode('utf-8', errors='replace')
    if any(re.search(pattern, content) for pattern in patterns):
        blocked.append((name, 'possible credential; review locally'))
for name, reason in blocked:
    print(f'BLOCK: {name}: {reason}')
if blocked:
    sys.exit(1)
print('Staged hygiene check passed. Pattern checks do not replace credential review or secret scanning.')
