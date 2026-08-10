#!/bin/sh
set -e

PORT="${PORT:-8000}"

python -c "
from config.env import validate_runtime_env
try:
    validate_runtime_env()
except Exception as exc:
    import json, sys
    print(json.dumps({'level': 'error', 'message': str(exc)}))
    sys.exit(1)
"

echo "{\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"level\":\"info\",\"message\":\"Runtime environment validated\"}"

echo "{\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"level\":\"info\",\"message\":\"Attempting database migrations\"}"
attempt=0
max_attempts=30
until python manage.py migrate --noinput --fake-initial; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge "$max_attempts" ]; then
    echo "{\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"level\":\"error\",\"message\":\"Database migrations failed after ${max_attempts} attempts\"}"
    exit 1
  fi
  sleep 1
done
echo "{\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"level\":\"info\",\"message\":\"Database migrations complete\"}"
python manage.py seed || true

if [ "$#" -eq 0 ] || [ "$1" = "gunicorn" ]; then
  exec gunicorn wsgi:application \
    --bind "0.0.0.0:${PORT}" \
    --workers "${WEB_CONCURRENCY:-1}" \
    --graceful-timeout "${GUNICORN_GRACEFUL_TIMEOUT:-30}" \
    --timeout "${GUNICORN_TIMEOUT:-60}" \
    --access-logfile - \
    --error-logfile -
fi

exec "$@"
