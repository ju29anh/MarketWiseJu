"""Browser protections also applied to early errors and CORS responses."""
import uuid
from starlette.datastructures import MutableHeaders
from core.config import settings


CONTENT_SECURITY_POLICY = "; ".join((
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "font-src 'self' https://fonts.gstatic.com",
    "img-src 'self' data: https:",
    "media-src 'self' data: blob:",
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'none'",
    "frame-ancestors 'none'",
    "form-action 'self'",
))


def apply_security_headers(headers, scope):
    headers['X-Request-ID'] = scope['state']['request_id']
    headers['X-Content-Type-Options'] = 'nosniff'
    headers['Referrer-Policy'] = 'no-referrer'
    headers['Cache-Control'] = 'no-store'
    headers['X-Frame-Options'] = 'DENY'
    headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    if settings.environment == 'production':
        headers['Content-Security-Policy'] = CONTENT_SECURITY_POLICY
    # Only the ASGI scheme (set by a trusted proxy) can enable HSTS.
    if scope.get('scheme') == 'https':
        headers['Strict-Transport-Security'] = 'max-age=31536000'


class SecurityHeadersMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        scope.setdefault('state', {})['request_id'] = uuid.uuid4().hex

        async def secured_send(message):
            if message['type'] == 'http.response.start':
                apply_security_headers(MutableHeaders(scope=message), scope)
            await send(message)

        await self.app(scope, receive, secured_send)
