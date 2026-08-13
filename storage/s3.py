import logging

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from config.env import resolve_s3_object_key
from config.s3_config import MENIX_S3_SERVICE, resolve_s3_config

logger = logging.getLogger('lowops.s3')

_available = False
_client = None
_config = None


def is_s3_available():
    from config.backends import ensure_backends

    ensure_backends()
    return _available


def get_s3_config():
    from config.backends import ensure_backends

    ensure_backends()
    return _config


def _build_s3_client(config, *, force_path_style):
    service_name = config['service_name']
    if service_name.startswith('com.mendix.storage.'):
        service_name = 's3'

    client_kwargs = {
        'service_name': service_name,
        'region_name': config['region'],
        'endpoint_url': config['endpoint'],
        'aws_access_key_id': config['access_key_id'],
        'aws_secret_access_key': config['secret_access_key'],
        'config': Config(
            signature_version='s3v4',
            s3={'addressing_style': 'path' if force_path_style else 'auto'},
            request_checksum_calculation='when_required',
            response_checksum_validation='when_required',
        ),
    }
    session_token = (config.get('session_token') or '').strip()
    if session_token:
        client_kwargs['aws_session_token'] = session_token

    return boto3.client(**client_kwargs)


def _activate_s3(client, config, force_path_style, *, verified):
    global _available, _client, _config

    active_config = {**config, 'force_path_style': force_path_style}
    _client = client
    _config = active_config
    _available = True
    location = (
        f"{active_config['bucket']}/{active_config['prefix']}"
        if active_config['prefix']
        else active_config['bucket']
    )
    if verified:
        logger.info(
            'S3 connection established (bucket: %s, region: %s, path_style: %s)',
            location,
            active_config['region'],
            force_path_style,
        )
    else:
        logger.warning(
            'S3 configured for bucket=%s prefix=%s (startup probe skipped; '
            'credentials appear scoped without bucket-level permissions).',
            active_config['bucket'],
            active_config['prefix'] or '(none)',
        )
    return True


def _is_access_denied(error):
    return isinstance(error, ClientError) and _s3_error_code(error) in {
        '403',
        'AccessDenied',
    }


def init_s3():
    global _available, _client, _config

    config = resolve_s3_config()
    if not config:
        import os

        service_name = (os.environ.get('S3_SERVICE_NAME') or '').strip()
        if (
            service_name.startswith('com.mendix.storage.')
            and service_name != MENIX_S3_SERVICE
        ):
            logger.error(
                'Storage service "%s" is not S3-compatible.',
                service_name,
            )
        else:
            logger.error(
                'S3 is not configured. Set S3_ENDPOINT, S3_BUCKET_NAME, '
                'S3_ACCESS_KEY_ID, and S3_SECRET_ACCESS_KEY.'
            )
        _available = False
        _client = None
        _config = None
        return False

    if not config['bucket']:
        logger.error('S3_BUCKET_NAME is empty after parsing.')
        _available = False
        _client = None
        _config = None
        return False

    path_styles = [config['force_path_style']]
    if config['force_path_style']:
        path_styles.append(False)

    last_error = None
    last_client = None
    last_path_style = config['force_path_style']

    for force_path_style in path_styles:
        client = _build_s3_client(config, force_path_style=force_path_style)
        last_client = client
        last_path_style = force_path_style
        try:
            _verify_connection(client, config)
            return _activate_s3(
                client,
                config,
                force_path_style,
                verified=True,
            )
        except (BotoCoreError, ClientError, Exception) as exc:
            last_error = exc
            if _is_access_denied(exc):
                logger.debug(
                    'S3 probe access denied with path_style=%s',
                    force_path_style,
                )
                continue
            logger.debug(
                'S3 probe failed with path_style=%s: %s',
                force_path_style,
                exc,
            )

    if last_client is not None and _is_access_denied(last_error):
        preferred_style = config['force_path_style']
        return _activate_s3(
            _build_s3_client(config, force_path_style=preferred_style),
            config,
            preferred_style,
            verified=False,
        )

    _available = False
    _client = None
    _config = None
    logger.error('S3 connection failed: %s', last_error)
    return False


def _probe_object_key(config):
    return resolve_s3_object_key('.healthcheck', config.get('prefix', ''))


def _s3_error_code(error):
    if not isinstance(error, ClientError):
        return ''
    return error.response.get('Error', {}).get('Code', '')


def _verify_connection(client, config):
    try:
        client.head_bucket(Bucket=config['bucket'])
    except ClientError as head_error:
        if _s3_error_code(head_error) not in {'403', 'AccessDenied'}:
            raise
        logger.debug(
            'HeadBucket access denied, trying object probe (%s)',
            head_error,
        )

    probe_key = _probe_object_key(config)
    probe_body = b'ok'
    client.put_object(
        Bucket=config['bucket'],
        Key=probe_key,
        Body=probe_body,
        ContentType='text/plain',
        ContentLength=len(probe_body),
    )


def build_object_key(relative_key):
    if not _config:
        raise RuntimeError('S3 is not available')
    return resolve_s3_object_key(relative_key, _config.get('prefix', ''))


def _put_object(key, body, content_type):
    _client.put_object(
        Bucket=_config['bucket'],
        Key=key,
        Body=body,
        ContentType=content_type,
        ContentLength=len(body),
    )


def upload_bytes(key, body, content_type):
    global _client, _config

    if not _available or not _client or not _config:
        raise RuntimeError('S3 is not available')

    if isinstance(body, memoryview):
        body = body.tobytes()
    elif not isinstance(body, (bytes, bytearray)):
        body = bytes(body)

    try:
        _put_object(key, body, content_type)
    except ClientError as exc:
        if not _is_access_denied(exc):
            logger.error(
                'S3 upload failed for bucket=%s key=%s: %s',
                _config['bucket'],
                key,
                exc,
            )
            raise

        alternate_style = not _config['force_path_style']
        logger.warning(
            'S3 upload access denied with path_style=%s; retrying with path_style=%s',
            _config['force_path_style'],
            alternate_style,
        )
        _client = _build_s3_client(_config, force_path_style=alternate_style)
        _config = {**_config, 'force_path_style': alternate_style}
        try:
            _put_object(key, body, content_type)
        except ClientError as retry_exc:
            logger.error(
                'S3 upload failed for bucket=%s key=%s: %s',
                _config['bucket'],
                key,
                retry_exc,
            )
            raise
    return key


def get_object(key):
    if not _available or not _client or not _config:
        raise RuntimeError('S3 is not available')
    result = _client.get_object(Bucket=_config['bucket'], Key=key)
    body = result['Body'].read()
    return {
        'body': body,
        'content_type': result.get('ContentType') or 'application/octet-stream',
        'content_length': result.get('ContentLength', len(body)),
    }


def delete_object(key):
    if not key or not _available or not _client or not _config:
        return
    if not _config['perform_delete']:
        return
    try:
        _client.delete_object(Bucket=_config['bucket'], Key=key)
    except (BotoCoreError, ClientError, Exception) as exc:
        logger.warning('Failed to delete S3 object "%s": %s', key, exc)
