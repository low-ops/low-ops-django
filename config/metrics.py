import logging
import threading
import time
from wsgiref.simple_server import WSGIServer, make_server

from django.conf import settings
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, Counter, Gauge, Histogram, generate_latest

from config.env import get_metrics_bind_host, get_metrics_port

logger = logging.getLogger('lowops.metrics')

HTTP_REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'path', 'status'],
)
HTTP_ACTIVE_REQUESTS = Gauge(
    'http_active_requests',
    'Number of in-flight HTTP requests',
)
HTTP_ERRORS_TOTAL = Counter(
    'http_errors_total',
    'Total HTTP error responses',
    ['method', 'path', 'status'],
)
USERS_CREATED_TOTAL = Counter(
    'users_created_total',
    'Total users created',
)
AVATAR_UPLOADS_TOTAL = Counter(
    'avatar_uploads_total',
    'Total avatar upload attempts',
    ['status'],
)

_lock = threading.Lock()
_started = False
_server = None


def get_metrics_auth_token():
    import os

    return os.environ.get('METRICS_AUTH_TOKEN', '').strip()


def is_metrics_authorized(environ):
    expected = get_metrics_auth_token()
    if not expected:
        return settings.DEBUG

    authorization = environ.get('HTTP_AUTHORIZATION', '')
    if authorization == f'Bearer {expected}':
        return True

    query_token = environ.get('QUERY_STRING', '')
    for part in query_token.split('&'):
        if part.startswith('token=') and part[len('token='):] == expected:
            return True
    return False


def _metrics_wsgi_app(environ, start_response):
    if not is_metrics_authorized(environ):
        start_response(
            '401 Unauthorized',
            [('Content-Type', 'text/plain'), ('WWW-Authenticate', 'Bearer')],
        )
        return [b'Unauthorized\n']

    payload = generate_latest(REGISTRY)
    start_response(
        '200 OK',
        [('Content-Type', CONTENT_TYPE_LATEST), ('Content-Length', str(len(payload)))],
    )
    return [payload]


def start_metrics_server():
    global _started, _server

    with _lock:
        if _started:
            return

        if not settings.DEBUG and not get_metrics_auth_token():
            logger.error(
                'METRICS_AUTH_TOKEN must be set when DEBUG is false.'
            )
            return

        bind_host = get_metrics_bind_host()
        port = get_metrics_port()
        try:
            _server = make_server(bind_host, port, _metrics_wsgi_app, WSGIServer)
            thread = threading.Thread(
                target=_server.serve_forever,
                name='prometheus-metrics',
                daemon=True,
            )
            thread.start()
            _started = True
            logger.info(
                'Prometheus metrics server listening on %s:%s',
                bind_host,
                port,
            )
        except OSError as exc:
            logger.warning(
                'Metrics server could not bind to %s:%s: %s',
                bind_host,
                port,
                exc,
            )
            _started = True


def normalize_path(path):
    parts = path.strip('/').split('/')
    normalized = []
    for part in parts:
        if part.isdigit():
            normalized.append(':id')
        else:
            normalized.append(part)
    return '/' + '/'.join(normalized) if normalized and normalized != [''] else '/'


class PrometheusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path in {'/ready'}:
            return self.get_response(request)

        path = normalize_path(request.path)
        HTTP_ACTIVE_REQUESTS.inc()
        started = time.perf_counter()
        status = '500'
        try:
            response = self.get_response(request)
            status = str(response.status_code)
            return response
        finally:
            duration = time.perf_counter() - started
            HTTP_ACTIVE_REQUESTS.dec()
            HTTP_REQUEST_DURATION.labels(
                method=request.method,
                path=path,
                status=status,
            ).observe(duration)
            if status.startswith(('4', '5')) and status != '404':
                HTTP_ERRORS_TOTAL.labels(
                    method=request.method,
                    path=path,
                    status=status,
                ).inc()
