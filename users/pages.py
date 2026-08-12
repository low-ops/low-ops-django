from django.shortcuts import redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie

from users.auth_core import is_admin_role, verify_email_token
from users.registration import is_registration_open
from users.services.users import avatar_url


def landing(request):
    if request.user_obj:
        if is_admin_role(request.user_obj.role):
            return redirect('/admin/users/')
        return redirect('/admin/settings/')
    if is_registration_open():
        return redirect('/auth/sign-up/')
    return redirect('/auth/sign-in/')


@ensure_csrf_cookie
def sign_in(request):
    if is_registration_open():
        return redirect('/auth/sign-up/')
    if request.user_obj:
        return redirect('/admin/')
    return render(request, 'auth/sign_in.html')


@ensure_csrf_cookie
def sign_up(request):
    if not is_registration_open():
        return redirect('/auth/sign-in/')
    if request.user_obj:
        return redirect('/admin/')
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
