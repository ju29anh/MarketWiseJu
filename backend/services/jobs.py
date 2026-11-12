"""Bounded, single-process job queue. Persisted results remain in SQLite."""
import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Lock, BoundedSemaphore
from fastapi import HTTPException
from core.config import settings

logger = logging.getLogger(__name__)
analysis_slots = BoundedSemaphore(settings.max_concurrent_analyses)


class JobManager:
    def __init__(self):
        self.lock = Lock()
        self.jobs = {}
        self.executor = ThreadPoolExecutor(max_workers=settings.max_concurrent_analyses, thread_name_prefix='marketwise')

    def submit(self, request):
        with self.lock:
            now = time.monotonic()
            self.jobs = {k: v for k, v in self.jobs.items() if v['status'] in ('queued', 'running') or now - v['_updated'] < settings.job_ttl_seconds}
            if sum(j['status'] in ('queued', 'running') for j in self.jobs.values()) >= settings.max_pending_jobs or len(self.jobs) >= 1000:
                raise HTTPException(429, 'Hệ thống đang xử lý nhiều yêu cầu. Vui lòng thử lại sau ít phút.')
            job_id = uuid.uuid4().hex
            self.jobs[job_id] = dict(job_id=job_id, status='queued', step=0, message='Đang chờ xử lý', session_id=None, _updated=now)
        self.executor.submit(self._run, job_id, request)
        return self.get(job_id)

    def _update(self, job_id, **values):
        with self.lock:
            self.jobs[job_id].update(values, _updated=time.monotonic())

    def _run(self, job_id, request):
        from services.analysis import analyze
        try:
            with analysis_slots:
                self._update(job_id, status='running')
                result = analyze(request, lambda step, message: self._update(job_id, step=step, message=message))
            self._update(job_id, status='complete', step=6, message='Phân tích hoàn tất', session_id=result['session_id'])
        except HTTPException as exc:
            self._update(job_id, status='failed', message=exc.detail if isinstance(exc.detail, str) else 'Dữ liệu chưa hợp lệ.')
        except Exception:
            logger.exception('Analysis job failed: %s', job_id)
            self._update(job_id, status='failed', message='Chưa thể hoàn tất phân tích. Hãy kiểm tra các cột số hoặc dùng file mẫu.')

    def get(self, job_id):
        with self.lock:
            job = self.jobs.get(job_id)
            if not job or (job['status'] in ('complete', 'failed') and time.monotonic() - job['_updated'] >= settings.job_ttl_seconds):
                raise HTTPException(404, 'Phiên xử lý đã hết hạn hoặc máy chủ đã khởi động lại.')
            return {k: v for k, v in job.items() if not k.startswith('_')}

    def shutdown(self):
        self.executor.shutdown(wait=True, cancel_futures=True)
