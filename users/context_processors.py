from users.auth_core import is_admin_role


def current_user(request):
    user = getattr(request, 'user_obj', None)
    return {
        'current_user': user,
        'is_admin': is_admin_role(getattr(user, 'role', None)) if user else False,
    }
