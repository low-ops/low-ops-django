import logging
import os

logger = logging.getLogger('lowops.database')

_database_available = False


def sqlite_database(base_dir):
    return {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(base_dir, 'db.sqlite3'),
    }


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
    if postgres:
        return {'default': postgres}
    return {'default': sqlite_database(base_dir)}


def _reset_connections(database_config):
    from django.conf import settings
    from django.db import connections

    connections.close_all()
    try:
        del connections['default']
    except Exception:
        pass

    settings.DATABASES = {'default': database_config}
    # ConnectionHandler.settings is a cached_property; clear it so DATABASES is re-read.
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
        _reset_connections(sqlite_database(base_dir))
        _database_available = False
        logger.warning(
            'Database is not configured (POSTGRES_* env vars missing). '
            'Falling back to in-memory users store.'
        )
        return False

    _reset_connections(postgres)

    try:
        from django.db import connections

        connection = connections['default']
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
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
        _reset_connections(sqlite_database(base_dir))
        logger.warning(
            'Database connection failed. Falling back to in-memory users store. Reason: %s',
            exc,
        )
        return False
