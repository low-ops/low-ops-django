from django.conf import settings
from django.shortcuts import redirect, render

from users.auth_core import is_admin_role, verify_email_token
from users.services.users import avatar_url


def landing(request):
    if request.user_obj:
        if is_admin_role(request.user_obj.role):
            return redirect('/admin/users/')
        return redirect('/admin/settings/')
    return redirect('/auth/sign-in/')


def sign_in(request):
    if request.user_obj:
        return redirect('/admin/')
    return render(request, 'auth/sign_in.html')


def sign_up(request):
    if request.user_obj:
        return redirect('/admin/')
    if not settings.ALLOW_PUBLIC_SIGN_UP:
        return redirect('/auth/sign-in/')
    return render(request, 'auth/sign_up.html')


def verify_email(request):
    token = request.GET.get('token')
    if token:
        user, error = verify_email_token(token)
        return render(request, 'auth/verify.html', {'success': user is not None, 'error': error})
    return render(request, 'auth/verify.html', {'success': None, 'error': None})


def admin_index(request):
    if is_admin_role(request.user_obj.role):
        return redirect('/admin/users/')
    return redirect('/admin/settings/')


def admin_users(request):
    if not is_admin_role(request.user_obj.role):
        return render(request, 'admin/access_denied.html', {'admin_breadcrumb': 'Users'})
    return render(request, 'admin/users.html', {'admin_breadcrumb': 'Users'})


def admin_settings(request):
    user = request.user_obj
    context = {
        'user': user,
        'avatar_url': avatar_url(user.id, user.image),
        'admin_breadcrumb': 'Settings',
    }
    return render(request, 'admin/settings.html', context)
