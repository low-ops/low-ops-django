from django.utils.deprecation import MiddlewareMixin


class NoCacheMiddleware(MiddlewareMixin):
    """Add no-cache headers to HTML and dynamic JSON responses."""

    def process_response(self, request, response):
        if response.has_header('Cache-Control'):
            return response

        path = request.path or ''
        if path.startswith('/static/') or path.startswith('/media/'):
            return response

        content_type = response.get('Content-Type', '')
        if 'text/html' in content_type or 'application/json' in content_type:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate'
            response['Pragma'] = 'no-cache'
        return response
