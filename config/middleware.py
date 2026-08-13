from django.utils.deprecation import MiddlewareMixin


from config.hosts import _is_internal_probe_host


class InternalProbeMiddleware:
    """Treat in-cluster HTTP probes as HTTPS behind the ingress."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.META.get('HTTP_HOST', '')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if _is_internal_probe_host(host) or user_agent.startswith('kube-probe/'):
            request.META['HTTP_X_FORWARDED_PROTO'] = 'https'
        return self.get_response(request)


class NoCacheMiddleware(MiddlewareMixin):
    """Add no-cache headers to HTML and dynamic JSON responses."""

    def process_response(self, request, response):
        if response.has_header('Cache-Control'):
            return response

        path = request.path or ''
        if path.startswith('/static/'):
            return response

        content_type = response.get('Content-Type', '')
        if 'text/html' in content_type or 'application/json' in content_type:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate'
            response['Pragma'] = 'no-cache'
        return response
