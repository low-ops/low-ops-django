import hashlib
import os
import re
from urllib.parse import urlparse

DEFAULT_APPLICATION_URL = 'http://localhost:8000'
BUILD_TIME_SECRET_KEY = 'build-time-placeholder-secret-min-32-chars!!'


class EnvValidationError(Exception):
    pass


def get_secret_key():
    explicit = os.environ.get('SECRET_KEY', '').strip()
    if explicit:
        return explicit

    seed_parts = [
        os.environ.get('POSTGRES_PASSWORD', ''),
        os.environ.get('POSTGRES_DATABASE', ''),
        os.environ.get('APPLICATION_URL', ''),
    ]
    seed = '|'.join(seed_parts)
    if any(part.strip() for part in seed_parts):
        return hashlib.sha256(seed.encode()).hexdigest()

    return BUILD_TIME_SECRET_KEY


def get_postgres_config():
    required = {
        'POSTGRES_HOST': os.environ.get('POSTGRES_HOST', '').strip(),
        'POSTGRES_DATABASE': os.environ.get('POSTGRES_DATABASE', '').strip(),
        'POSTGRES_USER': os.environ.get('POSTGRES_USER', '').strip(),
        'POSTGRES_PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''),
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise EnvValidationError(
            f'Missing required PostgreSQL env vars: {", ".join(missing)}'
        )

    return {
        **required,
        'POSTGRES_PORT': os.environ.get('POSTGRES_PORT', '5432').strip() or '5432',
    }


def get_database_url():
    postgres = get_postgres_config()
    from urllib.parse import quote

    password = quote(postgres['POSTGRES_PASSWORD'], safe='')
    return (
        f"postgresql://{postgres['POSTGRES_USER']}:{password}"
        f"@{postgres['POSTGRES_HOST']}:{postgres['POSTGRES_PORT']}"
        f"/{postgres['POSTGRES_DATABASE']}"
    )


def normalize_s3_endpoint(value):
    trimmed = (value or '').strip().rstrip('/')
    if not trimmed:
        return trimmed

    if re.match(r'^https?://', trimmed, re.IGNORECASE):
        return trimmed

    is_local = (
        trimmed.startswith('localhost')
        or trimmed.startswith('127.0.0.1')
        or trimmed.startswith('minio')
        or ':9000' in trimmed
    )
    return f"{'http' if is_local else 'https'}://{trimmed}"


def get_s3_public_base_url(endpoint):
    return normalize_s3_endpoint(endpoint).rstrip('/')


def parse_s3_bucket_name(value):
    trimmed = (value or '').strip().strip('/')
    slash_index = trimmed.find('/')

    if slash_index == -1:
        return {'bucket': trimmed, 'prefix': ''}

    return {
        'bucket': trimmed[:slash_index],
        'prefix': trimmed[slash_index + 1 :].strip('/'),
    }


def resolve_s3_object_key(relative_key, prefix=''):
    normalized_key = relative_key.lstrip('/')
    normalized_prefix = prefix.strip('/')

    if not normalized_prefix:
        return normalized_key

    if (
        normalized_key == normalized_prefix
        or normalized_key.startswith(f'{normalized_prefix}/')
    ):
        return normalized_key

    return f'{normalized_prefix}/{normalized_key}'


def parse_boolean_env(value):
    if not value:
        return False
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


def resolve_s3_credentials():
    access_key_id = (
        os.environ.get('S3_ACCESS_KEY_ID', '').strip()
        or os.environ.get('AWS_ACCESS_KEY_ID', '').strip()
    )
    secret_access_key = (
        os.environ.get('S3_SECRET_ACCESS_KEY', '').strip()
        or os.environ.get('AWS_SECRET_ACCESS_KEY', '').strip()
    )
    return access_key_id, secret_access_key


def get_s3_config():
    access_key_id, secret_access_key = resolve_s3_credentials()
    required = {
        'S3_ENDPOINT': os.environ.get('S3_ENDPOINT', '').strip(),
        'S3_BUCKET_NAME': os.environ.get('S3_BUCKET_NAME', '').strip(),
        'S3_ACCESS_KEY_ID': access_key_id,
        'S3_SECRET_ACCESS_KEY': secret_access_key,
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise EnvValidationError(
            f'Missing required S3 env vars: {", ".join(missing)}'
        )

    bucket_parts = parse_s3_bucket_name(required['S3_BUCKET_NAME'])
    endpoint = normalize_s3_endpoint(required['S3_ENDPOINT'])

    return {
        'endpoint': endpoint,
        'bucket': bucket_parts['bucket'],
        'prefix': bucket_parts['prefix'],
        'public_base_url': get_s3_public_base_url(endpoint),
        'access_key_id': required['S3_ACCESS_KEY_ID'],
        'secret_access_key': required['S3_SECRET_ACCESS_KEY'],
        'region': (os.environ.get('S3_REGION') or 'us-east-1').strip() or 'us-east-1',
        'force_path_style': parse_boolean_env(
            os.environ.get('S3_FORCE_PATH_STYLE', 'true')
        ),
    }


def get_s3_object_url(key):
    config = get_s3_config()
    object_key = resolve_s3_object_key(key, config['prefix'])
    return f"{config['public_base_url']}/{config['bucket']}/{object_key}"


def get_app_port():
    try:
        port = int(os.environ.get('PORT', '8000'))
    except ValueError:
        return 8000
    return port if port > 0 else 8000


def get_metrics_port():
    try:
        port = int(os.environ.get('METRICS_PORT', '8001'))
    except ValueError:
        return 8001
    return port if port > 0 else 8001


def get_metrics_bind_host():
    return (os.environ.get('METRICS_BIND_HOST') or '127.0.0.1').strip() or '127.0.0.1'


def normalize_app_url(value):
    trimmed = (value or '').strip()
    if not trimmed:
        return None

    with_protocol = (
        trimmed
        if trimmed.startswith('http://') or trimmed.startswith('https://')
        else f'https://{trimmed}'
    )

    try:
        parsed = urlparse(with_protocol)
        pathname = parsed.path.rstrip('/')
        host = parsed.netloc
        if not host:
            return None
        base = f'{parsed.scheme}://{host}'
        if pathname and pathname != '/':
            base += pathname
        return base
    except Exception:
        return None


def get_application_url():
    return normalize_app_url(os.environ.get('APPLICATION_URL'))


def get_application_hostname():
    application_url = get_application_url()
    if not application_url:
        return None
    return urlparse(application_url).hostname


def get_otel_config():
    endpoint = (os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT') or '').strip()
    service_name = (os.environ.get('OTEL_SERVICE_NAME') or '').strip()

    if not endpoint or not service_name:
        return None

    return {
        'endpoint': endpoint.rstrip('/'),
        'service_name': service_name,
    }
