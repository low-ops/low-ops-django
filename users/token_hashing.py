import hashlib
import hmac

from django.conf import settings


def hash_token(token):
    return hmac.new(
        settings.SECRET_KEY.encode(),
        token.encode(),
        hashlib.sha256,
    ).hexdigest()
