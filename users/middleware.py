from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin

from users.auth_core import SESSION_COOKIE, get_user_from_request, is_admin_role


PUBLIC_PREFIXES = (
    '/ready',
    '/static/',
    '/api/docs/',
    '/api/schema/',
    '/auth/',
    '/api/auth/',
)

PUBLIC_EXACT = {'/'}


class AuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.user_obj = get_user_from_request(request)
        path = request.path or ''

        if path in PUBLIC_EXACT or any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES):
            if path.startswith('/auth/') and request.user_obj and path != '/auth/verify/':
                return redirect('/admin/')
            return None

        if path.startswith('/admin') or path.startswith('/api/admin') or path.startswith('/api/user'):
            if request.user_obj is None:
                if path.startswith('/api/'):
                    from django.http import JsonResponse
                    return JsonResponse({'error': 'Unauthorized'}, status=401)
                return redirect('/auth/sign-in/')

        if path.startswith('/admin/users') and request.user_obj and not is_admin_role(request.user_obj.role):
            return None

        return None
