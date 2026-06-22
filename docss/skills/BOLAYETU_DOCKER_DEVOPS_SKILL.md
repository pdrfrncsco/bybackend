# BOLAYETU_DOCKER_DEVOPS_SKILL.md

Bolayetu is a containerized platform.

All services must run inside Docker containers.

Never assume local installation.

---

# CONTAINERS

Backend

Frontend

PostgreSQL

Redis

Celery Worker

Celery Beat

Nginx

---

# REQUIRED STRUCTURE

```text
bolayetu/

backend/
frontend/

docker/

docker-compose.yml

docker-compose.prod.yml

.env
.env.production
```

---

# BACKEND CONTAINER

Must support:

* Django
* Gunicorn
* PostgreSQL
* Redis

Expose:

8000

---

# FRONTEND CONTAINER

Must support:

* React
* Vite

Build static assets.

Serve through Nginx.

---

# NGINX

Responsibilities:

* Reverse Proxy
* SSL
* Static Files
* Compression
* Security Headers

---

# POSTGRESQL

Containerized PostgreSQL.

Never assume SQLite.

Forbidden:

sqlite3

Always use:

PostgreSQL

---

# REDIS

Use Redis for:

Caching

Celery

Rate Limiting

Future Realtime Features

---

# CELERY

Use Celery for:

Notifications

Emails

PDF Generation

Reports

Media Processing

Scheduled Jobs

---

# DEPLOYMENT

Target:

Ubuntu VPS

Deployment flow:

GitHub
↓
Pull
↓
Docker Build
↓
Docker Compose
↓
Health Check
↓
Production

---

# HEALTH CHECKS

Every service must provide:

Docker Healthcheck

API Health Endpoint

Example:

/api/health/

---

# LOGGING

Logs must be container friendly.

Use:

stdout

stderr

Avoid file-based logs.

---

# ENVIRONMENT VARIABLES

Never hardcode:

Secrets

Tokens

Passwords

API Keys

Always use:

.env

or

Docker Secrets

---

# DOCKERFILES

Every service must contain:

Dockerfile

.dockerignore

Optimized layers

Multi-stage builds when possible

---

# SCALABILITY

Architecture must support future migration to:

Kubernetes

AWS

Azure

Google Cloud

Without major refactoring.

Design containers stateless whenever possible.
