import os
import re
from urllib.parse import urlparse

from config.env import (
    get_s3_config as get_spec_s3_config,
    normalize_s3_endpoint,
    parse_s3_bucket_name,
    resolve_s3_credentials,
)

MENIX_S3_SERVICE = 'com.mendix.storage.s3'
AWS_REGION_PATTERN = re.compile(r'^[a-z]{2}(?:-[a-z]+)+-\d+$')


def parse_boolean_env(value):
    if not value:
        return False
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


def is_likely_aws_region(value):
    if not value:
        return False
    return bool(AWS_REGION_PATTERN.match(value.strip()))


def extract_region_from_endpoint(endpoint):
    try:
        host = urlparse(normalize_s3_endpoint(endpoint)).hostname or ''
        host = host.lower()
        match = re.search(r'\.s3[.-]([a-z0-9-]+)\.amazonaws\.com$', host) or re.search(
            r'^s3[.-]([a-z0-9-]+)\.amazonaws\.com$', host
        )
        if match and match.group(1) != 'dualstack' and is_likely_aws_region(match.group(1)):
            return match.group(1)
        if host == 's3.amazonaws.com' or host.endswith('.s3.amazonaws.com'):
            return 'us-east-1'
    except Exception:
        return None
    return None


def resolve_s3_region(endpoint, default_region):
    for candidate in (
        os.environ.get('S3_REGION'),
        os.environ.get('S3_SERVICE_NAME'),
    ):
        if is_likely_aws_region(candidate):
            return candidate.strip()
    return extract_region_from_endpoint(endpoint) or default_region


def has_s3_config():
    service_name = (os.environ.get('S3_SERVICE_NAME') or '').strip()
    if (
        service_name.startswith('com.mendix.storage.')
        and service_name != MENIX_S3_SERVICE
    ):
        return False

    access_key_id, secret_access_key = resolve_s3_credentials()
    return bool(
        access_key_id
        and secret_access_key
        and os.environ.get('S3_BUCKET_NAME')
        and os.environ.get('S3_ENDPOINT')
    )


def resolve_s3_config():
    if not has_s3_config():
        return None

    try:
        spec = get_spec_s3_config()
    except Exception:
        return None

    bucket_parts = parse_s3_bucket_name(os.environ['S3_BUCKET_NAME'])
    if not bucket_parts['bucket']:
        return None

    endpoint = spec['endpoint']
    region = resolve_s3_region(endpoint, spec['region'])

    return {
        'access_key_id': spec['access_key_id'],
        'secret_access_key': spec['secret_access_key'],
        'bucket': spec['bucket'],
        'prefix': spec['prefix'],
        'endpoint': endpoint,
        'public_base_url': spec['public_base_url'],
        'region': region,
        'force_path_style': spec['force_path_style'],
        'perform_delete': parse_boolean_env(os.environ.get('S3_PERFORM_DELETE')),
        'service_name': (os.environ.get('S3_SERVICE_NAME') or 's3').strip() or 's3',
    }
