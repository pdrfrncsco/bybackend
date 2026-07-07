# BOLAYETU_BACKEND_SKILL.md

Stack:

* Django
* Django REST Framework
* PostgreSQL
* JWT
* Cloudflare R2
* Redis
* Celery

Rules:

Never place business rules inside serializers.

Never place business rules inside ViewSets.

Business rules belong inside Services.

Queries belong inside Selectors.

ViewSets orchestrate only.

Always create:

* Model
* Serializer
* Service
* Selector
* Permissions
* Tests

When creating endpoints:

Provide:

* Pagination
* Search
* Ordering
* Filtering

All endpoints must be multi-tenant aware.

Always validate tenant ownership.

Never expose data across tenants.
