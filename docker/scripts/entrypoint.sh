#!/bin/bash
# BOLAYETU — Backend Docker Entrypoint
# Waits for PostgreSQL, runs migrations and collectstatic, then execs CMD.

set -e

echo "======================================================"
echo "  BOLAYETU Backend — Starting up"
echo "  Django settings: ${DJANGO_SETTINGS_MODULE:-config.settings}"
echo "======================================================"

wait_for_postgres() {
  echo "[entrypoint] Waiting for PostgreSQL at ${POSTGRES_HOST:-db}:${POSTGRES_PORT:-5432}..."
  max_attempts="${POSTGRES_WAIT_MAX_ATTEMPTS:-30}"
  attempts=0
  until python -c "
import os, sys
import psycopg2
try:
    psycopg2.connect(
        dbname=os.environ.get('POSTGRES_DB', os.environ.get('DB_NAME', 'bolayetu')),
        user=os.environ.get('POSTGRES_USER', os.environ.get('DB_USER', 'postgres')),
        password=os.environ.get('POSTGRES_PASSWORD', os.environ.get('DB_PASSWORD', '')),
        host=os.environ.get('POSTGRES_HOST', os.environ.get('DB_HOST', 'db')),
        port=os.environ.get('POSTGRES_PORT', os.environ.get('DB_PORT', '5432')),
    )
    sys.exit(0)
except Exception:
    sys.exit(1)
"; do
    attempts=$((attempts + 1))
    if [ "$attempts" -ge "$max_attempts" ]; then
      echo "[entrypoint] PostgreSQL did not become ready after ${max_attempts} attempts."
      exit 1
    fi
    echo "[entrypoint] PostgreSQL not ready — retrying in 2s..."
    sleep 2
  done
  echo "[entrypoint] PostgreSQL is ready."
}

if [[ "$1" == "celery" ]]; then
  wait_for_postgres
  echo "[entrypoint] Starting Celery..."
  exec "$@"
fi

wait_for_postgres

echo "[entrypoint] Running database migrations..."
python manage.py migrate --noinput

echo "[entrypoint] Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "[entrypoint] Startup complete."
echo "======================================================"
exec "$@"
