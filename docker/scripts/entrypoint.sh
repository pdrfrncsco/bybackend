#!/bin/bash
# BOLAYETU — Backend Docker Entrypoint
# Skill: BOLAYETU_DOCKER_DEVOPS_SKILL
#
# Runs before the main CMD:
# 1. Wait for PostgreSQL
# 2. Run migrations
# 3. Collect static files
# 4. Start Gunicorn (or Celery if CMD overridden)

set -e

echo "======================================================"
echo "  BOLAYETU Backend — Starting up"
echo "  Django settings: ${DJANGO_SETTINGS_MODULE}"
echo "======================================================"

# Skip migrations and collectstatic for Celery or background worker containers
if [[ "$1" == "celery" ]]; then
  echo "[entrypoint] Celery worker detected. Waiting for DB and skipping migrations/collectstatic..."
  echo "[entrypoint] Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
  until python -c "
import psycopg2, os, sys
try:
    psycopg2.connect(
        dbname=os.environ['POSTGRES_DB'],
        user=os.environ['POSTGRES_USER'],
        password=os.environ['POSTGRES_PASSWORD'],
        host=os.environ.get('POSTGRES_HOST', 'db'),
        port=os.environ.get('POSTGRES_PORT', '5432'),
    )
    sys.exit(0)
except Exception:
    sys.exit(1)
"; do
    sleep 2
  done
  echo "[entrypoint] PostgreSQL is ready. Starting Celery..."
  exec "$@"
fi

echo "[entrypoint] Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT}..."

until python -c "
import psycopg2, os, sys
try:
    psycopg2.connect(
        dbname=os.environ['POSTGRES_DB'],
        user=os.environ['POSTGRES_USER'],
        password=os.environ['POSTGRES_PASSWORD'],
        host=os.environ.get('POSTGRES_HOST', 'db'),
        port=os.environ.get('POSTGRES_PORT', '5432'),
    )
    sys.exit(0)
except Exception:
    sys.exit(1)
"; do
  echo "[entrypoint] PostgreSQL not ready — retrying in 2s..."
  sleep 2
done

echo "[entrypoint] PostgreSQL is ready."

# ─── Run Migrations ──────────────────────────────────────
echo "[entrypoint] Running database migrations..."
python manage.py migrate --noinput

# ─── Collect Static Files ────────────────────────────────
echo "[entrypoint] Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "[entrypoint] Startup complete. Starting server..."
echo "======================================================"

# ─── Execute CMD ─────────────────────────────────────────
exec "$@"
