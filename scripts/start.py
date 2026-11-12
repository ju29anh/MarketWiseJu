"""Portable launcher; no PowerShell execution-policy changes required."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[1]
python = root / 'backend/.venv/Scripts/python.exe'
node = shutil.which('node') or str(Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'nodejs/node.exe')
for path in [python, Path(node), root/'backend/.env', root/'frontend/.env', root/'frontend/node_modules/vite/bin/vite.js']:
    if not path.exists():
        sys.exit(f'Missing {path.name}. Follow README.md setup instructions.')
processes = []
for folder, command in [('backend', [str(python), 'run.py']), ('frontend', [node, 'node_modules/vite/bin/vite.js'])]:
    with (root/folder/'server.log').open('w') as out, (root/folder/'server-error.log').open('w') as err:
        processes.append(subprocess.Popen(command, cwd=root/folder, stdout=out, stderr=err,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0))
time.sleep(3)
if any(p.poll() is not None for p in processes):
    for p in processes:
        if p.poll() is None:
            p.terminate()
    sys.exit('Startup failed. See backend/server-error.log and frontend/server-error.log.')
print('Started. Open the Local URL from frontend/server.log.')
print('Stop with PowerShell: Stop-Process -Id ' + ','.join(str(p.pid) for p in processes))
