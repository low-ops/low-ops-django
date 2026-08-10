import json
import logging
import os
import urllib.error
import urllib.request

logger = logging.getLogger('lowops.email')


def is_email_verification_enabled():
    return bool(os.environ.get('RESEND_API_KEY', '').strip())


def send_email(*, to, subject, text):
    api_key = os.environ.get('RESEND_API_KEY', '').strip()
    if not api_key:
        logger.info('Skipping email to %s (RESEND_API_KEY not set)', to)
        return False

    payload = json.dumps({
        'from': 'Low-Ops <onboarding@resend.dev>',
        'to': [to],
        'subject': subject,
        'text': text,
    }).encode('utf-8')

    request = urllib.request.Request(
        'https://api.resend.com/emails',
        data=payload,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            response.read()
        return True
    except urllib.error.HTTPError as exc:
        body = exc.read().decode('utf-8', errors='replace')
        logger.error('Resend API error %s: %s', exc.code, body)
        return False
    except Exception as exc:
        logger.error('Failed to send email: %s', exc)
        return False


def send_verification_email(user, verify_url):
    return send_email(
        to=user.email,
        subject='Verify your email address',
        text=f'Click the link to verify your email: {verify_url}',
    )
