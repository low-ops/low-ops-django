from config.dotenv import load_dotenv_file

load_dotenv_file()

import os

from django.core.exceptions import ImproperlyConfigured

from config.database import configure_databases
from config.env import (
    BUILD_TIME_SECRET_KEY,
    DEFAULT_APPLICATION_URL,
    get_application_url,
    get_secret_key,
)
from config.hosts import (
    build_allowed_hosts,
    build_csrf_trusted_origins,
    patch_validate_host_for_kubernetes,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SECRET_KEY = get_secret_key()
DEBUG = os.environ.get('DEBUG', 'false').lower() in {'1', 'true', 'yes', 'on'}

ALLOWED_HOSTS = build_allowed_hosts(debug=DEBUG)
patch_validate_host_for_kubernetes()

if not DEBUG and SECRET_KEY == BUILD_TIME_SECRET_KEY:
    raise ImproperlyConfigured(
        'SECRET_KEY must be set to a unique value when DEBUG is false.'
    )

ROOT_URLCONF = 'urls'
WSGI_APPLICATION = 'wsgi.application'

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_spectacular',
    'corsheaders',
    'users.apps.UsersConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'users.middleware.AuthMiddleware',
    'config.metrics.PrometheusMiddleware',
    'config.middleware.NoCacheMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.template.context_processors.csrf',
                'users.context_processors.current_user',
            ],
        },
    },
]

DATABASES = configure_databases(BASE_DIR)
USE_TZ = True
TIME_ZONE = 'UTC'

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'assets')]
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

MAX_LOGIN_ATTEMPTS = int(os.environ.get('MAX_LOGIN_ATTEMPTS', '5'))
LOGIN_LOCKOUT_MINUTES = int(os.environ.get('LOGIN_LOCKOUT_MINUTES', '15'))

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'users.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'UNAUTHENTICATED_USER': None,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Low-Ops Django Template API',
    'DESCRIPTION': (
        'Custom API routes for the Low-Ops Django starter template. '
        'Env vars and platform endpoints follow the '
        'Low-Ops application specification.'
    ),
    'VERSION': '1.0.0',
}

APPLICATION_URL = get_application_url() or DEFAULT_APPLICATION_URL
EMAIL_VERIFICATION_ENABLED = bool(os.environ.get('RESEND_API_KEY', '').strip())

if get_application_url():
    CORS_ALLOWED_ORIGINS = [get_application_url()]
else:
    CORS_ALLOW_ALL_ORIGINS = DEBUG

CSRF_TRUSTED_ORIGINS = build_csrf_trusted_origins(debug=DEBUG)

if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    if os.environ.get('SECURE_SSL_REDIRECT', 'true').lower() in {'1', 'true', 'yes', 'on'}:
        SECURE_SSL_REDIRECT = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'config.json_logging.JsonFormatter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'lowops': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
