from rest_framework.permissions import BasePermission

from users.auth_core import is_admin_role


class IsAuthenticated(BasePermission):
    def has_permission(self, request, view):
        return getattr(request, 'user_obj', None) is not None


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, 'user_obj', None)
        return user is not None and is_admin_role(user.role)
