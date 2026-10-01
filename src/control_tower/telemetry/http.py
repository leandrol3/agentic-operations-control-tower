"""One SERVER span per request. Pure ASGI keeps context through response and threadpool."""
from opentelemetry.trace import SpanKind
from . import tracing
from .propagation import extract


class HTTPTracing:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or not tracing.enabled():
            return await self.app(scope, receive, send)
        headers = {k.decode().lower(): v.decode() for k, v in scope.get('headers', [])}
        method = scope['method']
        with tracing.operation('http ' + method, kind=SpanKind.SERVER, context=extract(headers),
                attributes={'http.request.method': method}) as span:
            async def traced_send(message):
                if message['type'] == 'http.response.start':
                    route = getattr(scope.get('route'), 'path', 'unmatched')
                    span.update_name(f'http {method} {route}')
                    span.set_attribute('http.route', route)
                    span.set_attribute('http.response.status_code', message['status'])
                    if message['status'] >= 500:
                        tracing.mark_error(span, 'http_server_error')
                    message.setdefault('headers', []).append((b'x-request-trace-id',
                        tracing.identifiers()['trace_id'].encode()))
                await send(message)
            await self.app(scope, receive, traced_send)
