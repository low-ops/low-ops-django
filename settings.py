from config.dotenv import load_dotenv_file

load_dotenv_file()

import os

from config.database import configure_databases
from config.env import DEFAULT_APPLICATION_URL, get_application_url

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Django requires this internally for sessions/signing; optional SECRET_KEY env override.
SECRET_KEY = (
    os.environ.get('SECRET_KEY', '').strip()
    or 'build-time-placeholder-secret-min-32-chars!!'
)
DEBUG = os.environ.get('DEBUG', 'true').lower() in {'1', 'true', 'yes', 'on'}
ALLOWED_HOSTS = ['*']

ROOT_URLCONF = 'urls'
WSGI_APPLICATION = 'wsgi.application'

INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_spectacular',
    'corsheaders',
    'users.apps.UsersConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
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

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'users.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
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
ALLOW_PUBLIC_SIGN_UP = os.environ.get('ALLOW_PUBLIC_SIGN_UP', 'false').lower() in {
    '1', 'true', 'yes', 'on',
}
if get_application_url():
    CORS_ALLOWED_ORIGINS = [get_application_url()]
else:
    CORS_ALLOW_ALL_ORIGINS = DEBUG

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
