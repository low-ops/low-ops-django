from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from users.models import LoginAttempt

MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_MINUTES = 15


def _lockout_duration():
    minutes = getattr(settings, 'LOGIN_LOCKOUT_MINUTES', LOGIN_LOCKOUT_MINUTES)
    return timedelta(minutes=minutes)


def _max_attempts():
    return getattr(settings, 'MAX_LOGIN_ATTEMPTS', MAX_LOGIN_ATTEMPTS)


def check_login_allowed(email):
    normalized = (email or '').strip().lower()
    if not normalized:
        return None

    try:
        attempt = LoginAttempt.objects.get(email=normalized)
    except LoginAttempt.DoesNotExist:
        return None

    if attempt.locked_until and attempt.locked_until > timezone.now():
        remaining = attempt.locked_until - timezone.now()
        minutes = max(int(remaining.total_seconds() // 60), 1)
        return f'Too many failed attempts. Try again in {minutes} minute(s).'

    if attempt.locked_until and attempt.locked_until <= timezone.now():
        attempt.failures = 0
        attempt.locked_until = None
        attempt.save(update_fields=['failures', 'locked_until', 'updated_at'])

    return None


def record_login_failure(email):
    normalized = (email or '').strip().lower()
    if not normalized:
        return

    attempt, _created = LoginAttempt.objects.get_or_create(
        email=normalized,
        defaults={'failures': 0},
    )
    attempt.failures += 1
    if attempt.failures >= _max_attempts():
        attempt.locked_until = timezone.now() + _lockout_duration()
    attempt.save(update_fields=['failures', 'locked_until', 'updated_at'])


def clear_login_attempts(email):
    normalized = (email or '').strip().lower()
    if not normalized:
        return
    LoginAttempt.objects.filter(email=normalized).delete()
