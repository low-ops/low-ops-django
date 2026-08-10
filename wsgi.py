import os

from config.dotenv import load_dotenv_file

load_dotenv_file()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

from django.core.wsgi import get_wsgi_application

from config.otel import setup_otel  # noqa: E402

setup_otel()

application = get_wsgi_application()

from config.backends import ensure_backends  # noqa: E402
from config.metrics import start_metrics_server  # noqa: E402

ensure_backends()
start_metrics_server()
