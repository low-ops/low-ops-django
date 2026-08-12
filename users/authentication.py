from rest_framework.authentication import SessionAuthentication as DRFSessionAuthentication

from users.auth_core import get_user_from_request


class SessionAuthentication(DRFSessionAuthentication):
    def authenticate(self, request):
        user = getattr(request, 'user_obj', None)
        if user is None:
            user = get_user_from_request(request)
            request.user_obj = user
        if user is None:
            return None
        self.enforce_csrf(request)
        return (user, None)
