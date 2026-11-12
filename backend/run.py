"""Launch with the same environment settings as the application."""
import os

for thread_setting in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(thread_setting, '1')

import uvicorn
from core.config import settings

if __name__ == '__main__':
    use_reload = os.environ.get('UVICORN_RELOAD', '').lower() == 'true'
    settings.validate_runtime()
    if use_reload and settings.environment == 'production':
        raise RuntimeError('UVICORN_RELOAD must be disabled in production')
    uvicorn.run('main:app', host=settings.host, port=settings.port,
                reload=use_reload, workers=1, server_header=False)
