import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.password_validation import validate_password as django_validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone

from users.login_throttle import check_login_allowed, clear_login_attempts, record_login_failure
from users.models import Account, Session, User, Verification
from users.token_hashing import hash_token

SESSION_COOKIE = 'session_token'
SESSION_DAYS = 30


def is_admin_role(role):
    if not role:
        return False
    return 'admin' in [part.strip() for part in str(role).split(',')]


def validate_password(password):
    try:
        django_validate_password(password)
    except ValidationError as exc:
        return ' '.join(exc.messages)
    return None


def get_user_from_request(request):
    token = request.COOKIES.get(SESSION_COOKIE)
    if not token:
        return None

    token_hash = hash_token(token)
    try:
        session = Session.objects.select_related('user').get(token=token_hash)
    except Session.DoesNotExist:
        return None

    if session.expires_at <= timezone.now():
        session.delete()
        return None

    user = session.user
    if user.banned:
        if user.ban_expires and user.ban_expires <= timezone.now():
            user.banned = False
            user.ban_reason = None
            user.ban_expires = None
            user.save(update_fields=['banned', 'ban_reason', 'ban_expires', 'updated_at'])
        else:
            return None

    request.session_obj = session
    return user


def create_session(request, user):
    token = secrets.token_urlsafe(32)
    token_hash = hash_token(token)
    expires_at = timezone.now() + timedelta(days=SESSION_DAYS)
    session = Session.objects.create(
        token=token_hash,
        expires_at=expires_at,
        user=user,
        ip_address=_client_ip(request),
        user_agent=(request.META.get('HTTP_USER_AGENT') or '')[:500],
    )
    return session, token


def clear_session(request, response):
    token = request.COOKIES.get(SESSION_COOKIE)
    if token:
        Session.objects.filter(token=hash_token(token)).delete()
    response.delete_cookie(SESSION_COOKIE)


def attach_session_cookie(response, token):
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_DAYS * 86400,
        httponly=True,
        samesite='Lax',
        secure=not settings.DEBUG,
    )
    return response


def sign_in_with_password(request, email, password):
    email = (email or '').strip().lower()

    lockout_error = check_login_allowed(email)
    if lockout_error:
        return None, lockout_error

    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        record_login_failure(email)
        return None, 'Invalid email or password.'

    account = Account.objects.filter(user=user, provider_id='credential').first()
    if account is None or not account.password:
        record_login_failure(email)
        return None, 'Invalid email or password.'

    if not check_password(password, account.password):
        record_login_failure(email)
        return None, 'Invalid email or password.'

    if user.banned:
        if user.ban_expires and user.ban_expires <= timezone.now():
            user.banned = False
            user.ban_reason = None
            user.ban_expires = None
            user.save(update_fields=['banned', 'ban_reason', 'ban_expires', 'updated_at'])
        else:
            reason = user.ban_reason or 'Your account has been banned.'
            return None, reason

    if not user.email_verified and settings.EMAIL_VERIFICATION_ENABLED:
        return None, 'Please verify your email before signing in.'

    clear_login_attempts(email)
    session, token = create_session(request, user)
    return {'user': user, 'session': session, 'token': token}, None


def create_credential_user(name, email, password, *, email_verified=False, role='user'):
    email = (email or '').strip().lower()
    user = User.objects.create(
        name=name.strip(),
        email=email,
        email_verified=email_verified,
        role=role,
    )
    Account.objects.create(
        account_id=email,
        provider_id='credential',
        user=user,
        password=make_password(password),
    )
    return user


def revoke_user_sessions(user_id, except_token=None):
    qs = Session.objects.filter(user_id=user_id)
    if except_token:
        qs = qs.exclude(token=hash_token(except_token))
    return qs.delete()[0]


def create_verification_token(identifier):
    Verification.objects.filter(identifier=identifier).delete()
    token = secrets.token_urlsafe(32)
    expires_at = timezone.now() + timedelta(hours=24)
    Verification.objects.create(
        identifier=identifier,
        value=hash_token(token),
        expires_at=expires_at,
    )
    return token


def verify_email_token(token):
    if not token:
        return None, 'Invalid or expired verification link.'

    try:
        record = Verification.objects.get(value=hash_token(token))
    except Verification.DoesNotExist:
        return None, 'Invalid or expired verification link.'

    if record.expires_at <= timezone.now():
        record.delete()
        return None, 'Invalid or expired verification link.'

    try:
        user = User.objects.get(email__iexact=record.identifier)
    except User.DoesNotExist:
        record.delete()
        return None, 'User not found.'

    user.email_verified = True
    user.save(update_fields=['email_verified', 'updated_at'])
    record.delete()
    return user, None


def serialize_user(user):
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'emailVerified': user.email_verified,
        'image': user.image,
        'role': user.role or 'user',
        'banned': bool(user.banned),
        'banReason': user.ban_reason,
        'banExpires': user.ban_expires.isoformat() if user.ban_expires else None,
        'createdAt': user.created_at.isoformat(),
    }


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
