from rest_framework.authentication import BaseAuthentication

from users.auth_core import get_user_from_request


class SessionAuthentication(BaseAuthentication):
    def authenticate(self, request):
        user = getattr(request, 'user_obj', None)
        if user is None:
            user = get_user_from_request(request)
            request.user_obj = user
        if user is None:
            return None
        return (user, None)
