import json

from django.http import JsonResponse

from config.database import is_database_available
from storage import s3 as s3_storage


def ready(request):
    checks = {
        'postgres': 'ok' if is_database_available() else 'error',
        's3': 'ok' if s3_storage.is_s3_available() else 'error',
    }
    healthy = all(value == 'ok' for value in checks.values())
    payload = {
        'status': 'ready' if healthy else 'not_ready',
        'checks': checks,
    }
    return JsonResponse(payload, status=200 if healthy else 503)
