from django.middleware.csrf import CsrfViewMiddleware
from rest_framework.exceptions import PermissionDenied


def enforce_csrf(request):
    if request.method in {'GET', 'HEAD', 'OPTIONS', 'TRACE'}:
        return

    def get_response(request):
        return None

    middleware = CsrfViewMiddleware(get_response)
    rejected = middleware.process_view(request, None, (), {})
    if rejected is not None:
        raise PermissionDenied('CSRF token missing or incorrect.')
