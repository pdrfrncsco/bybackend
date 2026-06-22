# BOLAYETU Backend — Dockerfile
# Skill: BOLAYETU_DOCKER_DEVOPS_SKILL
#
# Multi-stage build:
#   Stage 1 (builder): Install Python dependencies
#   Stage 2 (runtime): Lean production image
#
# Rules:
# - Never assume local execution
# - Always use Docker
# - Logs to stdout/stderr (container friendly)


# ─── Stage 1: Builder ────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies for psycopg2, Pillow, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt requirements.txt

RUN pip install --upgrade pip \
    && pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels \
        -r requirements.txt


# ─── Stage 2: Runtime ────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Security: run as non-root user
RUN groupadd -r bolayetu && useradd -r -g bolayetu bolayetu

WORKDIR /app

# Install only runtime system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libjpeg62-turbo \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels and install
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy application code
COPY --chown=bolayetu:bolayetu . .

# Static files will be collected at startup
RUN mkdir -p /app/staticfiles /app/media \
    && chown -R bolayetu:bolayetu /app/staticfiles /app/media

# Entrypoint script
COPY --chown=bolayetu:bolayetu docker/scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER bolayetu

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health/')" || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "gthread", \
     "--threads", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]
