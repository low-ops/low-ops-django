#!/bin/sh
set -e

PORT="${PORT:-8000}"
WEB_CONCURRENCY="${WEB_CONCURRENCY:-2}"

if [ "$#" -eq 0 ] || [ "$1" = "gunicorn" ]; then
  exec gunicorn wsgi:application \
    --bind "0.0.0.0:${PORT}" \
    --preload \
    --workers "${WEB_CONCURRENCY}" \
    --graceful-timeout "${GUNICORN_GRACEFUL_TIMEOUT:-30}" \
    --timeout "${GUNICORN_TIMEOUT:-60}" \
    --access-logfile - \
    --error-logfile -
fi

exec "$@"
