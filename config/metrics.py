import os
import threading
import time

from prometheus_client import Counter, Gauge, Histogram, start_http_server

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


def start_metrics_server():
    global _started
    with _lock:
        if _started:
            return
        port = int(os.environ.get('METRICS_PORT', '8001'))
        try:
            start_http_server(port)
            _started = True
        except OSError:
            # Another worker already bound the metrics port.
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
