#!/bin/sh
set -e

if [ -n "$POSTGRES_HOST" ] && [ -n "$POSTGRES_DATABASE" ] && [ -n "$POSTGRES_USER" ] && [ -n "$POSTGRES_PASSWORD" ]; then
  echo "[INFO] Attempting database migrations..."
  if python manage.py migrate --noinput; then
    echo "[INFO] Database migrations complete."
  else
    echo "[WARNING] Database migrations failed. Continuing with available fallback."
  fi
else
  echo "[WARNING] POSTGRES_* env vars not set. Skipping migrations and using in-memory fallback."
fi

exec "$@"
