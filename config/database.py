import logging
import os
import time

from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger('lowops.database')

_database_available = False


def build_postgres_database():
    user = os.environ.get('POSTGRES_USER')
    password = os.environ.get('POSTGRES_PASSWORD')
    host = os.environ.get('POSTGRES_HOST')
    port = os.environ.get('POSTGRES_PORT') or '5432'
    database = os.environ.get('POSTGRES_DATABASE')

    if not all([user, password, host, database]):
        return None

    return {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': database,
        'USER': user,
        'PASSWORD': password,
        'HOST': host,
        'PORT': port,
    }


def configure_databases(base_dir):
    postgres = build_postgres_database()
    if not postgres:
        raise ImproperlyConfigured(
            'PostgreSQL is required. Set POSTGRES_HOST, POSTGRES_PORT, '
            'POSTGRES_USER, POSTGRES_PASSWORD, and POSTGRES_DATABASE '
            'in your environment or .env file (copy .env.example to .env).'
        )
    return {'default': postgres}


def _reset_connections(database_config):
    from django.conf import settings
    from django.db import connections

    connections.close_all()
    try:
        del connections['default']
    except Exception:
        pass

    settings.DATABASES = {'default': database_config}
    connections._settings = None
    connections.__dict__.pop('settings', None)


def is_database_available():
    from config.backends import ensure_backends

    ensure_backends()
    return _database_available


def init_database(base_dir):
    global _database_available

    postgres = build_postgres_database()
    if not postgres:
        _database_available = False
        logger.error(
            'PostgreSQL is not configured (POSTGRES_* env vars missing).'
        )
        return False

    _reset_connections(postgres)

    max_attempts = int(os.environ.get('DB_CONNECT_ATTEMPTS', '30'))

    try:
        from django.core.management import call_command
        from django.db import connections

        connection = connections['default']
        for attempt in range(1, max_attempts + 1):
            try:
                connection.ensure_connection()
                with connection.cursor() as cursor:
                    cursor.execute('SELECT 1')
                break
            except Exception as exc:
                if attempt >= max_attempts:
                    raise exc
                logger.info(
                    'Waiting for PostgreSQL (attempt %s/%s)',
                    attempt,
                    max_attempts,
                )
                time.sleep(1)

        call_command('migrate', '--noinput', '--fake-initial', verbosity=0)

        try:
            call_command('seed', verbosity=0)
        except Exception as exc:
            logger.warning('Database seed failed: %s', exc)

        _database_available = True
        logger.info(
            'Database connection established (%s:%s/%s)',
            postgres['HOST'],
            postgres['PORT'],
            postgres['NAME'],
        )
        return True
    except Exception as exc:
        _database_available = False
        logger.error('Database connection failed: %s', exc)
        return False
