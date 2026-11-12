"""Application composition and backwards-compatible entry points."""
import logging
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings, UPLOADS_DIR
from database import init_database
from routers import upload, analysis, dashboard, model_eval, research
from schemas.analysis import AnalyzeRequest, DatasetRequest
from services import catalog
from services.jobs import JobManager
from core.request_limits import RequestLimiter
from core.security import SecurityHeadersMiddleware, apply_security_headers

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    settings.validate_runtime()
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    app.state.jobs = JobManager()
    yield
    app.state.jobs.shutdown()


app = FastAPI(title='MARKETWISE API', version='2.0.0', lifespan=lifespan,
              docs_url=None if settings.environment == 'production' else '/docs',
              redoc_url=None if settings.environment == 'production' else '/redoc',
              openapi_url=None if settings.environment == 'production' else '/openapi.json')
request_limiter = RequestLimiter()
app.include_router(research.router)


@app.middleware('http')
async def request_limits(request: Request, call_next):
    # Multipart framing allowance; individual files also have a streaming limit.
    max_bytes = settings.max_upload_mb * 1024**2 + 65536
    length = request.headers.get('content-length')
    response = None
    if length and (len(length) > 20 or not length.isdigit() or int(length) > max_bytes):
        response = JSONResponse(status_code=413, content={'detail': 'File quá lớn. Hãy chia nhỏ dữ liệu.'})
    expensive = request.method == 'POST' or request.url.path in ('/api/market-overview', '/api/search')
    if response is None and settings.environment == 'production' and expensive:
        allowed, retry = request_limiter.allow(request.client.host if request.client else 'unknown', settings.rate_limit_requests, settings.rate_limit_window_seconds)
        if not allowed:
            response = JSONResponse(status_code=429, content={'detail': 'Đã đạt giới hạn yêu cầu của bản demo. Vui lòng chờ rồi thử lại.'}, headers={'Retry-After': str(retry)})
    if response is None:
        response = await call_next(request)
    return response


class BodyLimitMiddleware:
    """Bound streamed/chunked bodies even when Content-Length is absent."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        received = 0
        exceeded = False
        rejected = False
        async def limited_receive():
            nonlocal received, exceeded
            message = await receive()
            received += len(message.get('body', b''))
            if received > settings.max_upload_mb * 1024**2 + 65536:
                from starlette.formparsers import MultiPartException
                exceeded = True
                # The multipart parser closes its temporary files on this exception.
                raise MultiPartException('File quá lớn. Hãy chia nhỏ dữ liệu.')
            return message
        async def limited_send(message):
            nonlocal rejected
            if exceeded:
                if not rejected and message['type'] == 'http.response.start':
                    rejected = True
                    response = JSONResponse(status_code=413, content={'detail': 'File quá lớn. Hãy chia nhỏ dữ liệu.'})
                    await response(scope, receive, send)
                return
            await send(message)
        await self.app(scope, limited_receive, limited_send)


app.add_middleware(BodyLimitMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins,
                   allow_credentials=False, allow_methods=['GET', 'POST'],
                   allow_headers=['Content-Type'], expose_headers=['X-Request-ID'])
app.add_middleware(SecurityHeadersMiddleware)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, 'request_id', uuid.uuid4().hex)
    logger.error('Unhandled error request_id=%s', request_id, exc_info=exc)
    response = JSONResponse(status_code=500, content={
        'detail': 'Hệ thống chưa thể xử lý yêu cầu. Vui lòng thử lại sau.', 'request_id': request_id})
    request.scope.setdefault('state', {})['request_id'] = request_id
    apply_security_headers(response.headers, request.scope)
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Never return validation input, exception context, filesystem paths or secrets.
    return JSONResponse(status_code=422, content={'detail': 'Dữ liệu đầu vào không hợp lệ. Hãy kiểm tra tên sản phẩm và dataset.',
        'errors': [{'field': '.'.join(map(str, e['loc'])), 'type': e['type']} for e in exc.errors()]})


@app.get('/')
def read_root():
    if settings.static_dir:
        return FileResponse(settings.static_path / 'index.html')
    return {'system': 'MarketWiseJu', 'status': 'online', 'version': '2.0.0'}


@app.get('/api/health')
def health():
    return {'status': 'ok', 'public_demo': settings.public_demo}


@app.get('/api/config')
def public_config():
    return {'public_demo': settings.public_demo, 'max_upload_mb': settings.max_upload_mb}


for router in (upload.router, dashboard.router, analysis.router, model_eval.router):
    app.include_router(router)

# Preserve the direct-import contract of the original regression scripts.
init_database()
get_categories = catalog.get_categories
get_datasets = catalog.get_datasets
get_dataset_products = catalog.get_dataset_products
search_market_data = catalog.search_market_data
find_best_market_mapping = catalog.find_best_market_mapping
remove_accents = catalog.remove_accents
get_dashboard = catalog.get_dashboard
run_market_analysis = analysis.run_market_analysis
get_analysis_by_id = analysis.get_analysis_by_id


async def get_market_overview(q=''):
    return catalog.get_market_overview(q)


async def upload_dataset(file, category='Custom Upload'):
    from starlette.concurrency import run_in_threadpool
    return await run_in_threadpool(upload.upload_dataset, file, category)


def validate_dataset_endpoint(payload):
    return upload.validate_dataset_endpoint(DatasetRequest.model_validate(payload))


# One web service serves the built frontend and API from the same origin.
if settings.static_dir:
    app.mount('/', StaticFiles(directory=settings.static_path, html=True), name='frontend')
