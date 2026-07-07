# BOLAYETU_MULTITENANT_SKILL.md

Bolayetu is a Multi-Tenant SaaS.

Tenants are Organizations.

Examples:

faf.bolayetu.com

girabola.bolayetu.com

apf-luanda.bolayetu.com

Rules:

Every entity must belong to a tenant.

Never return records from another tenant.

All queries must be tenant scoped.

The frontend must detect:

window.location.hostname

The backend must resolve:

request.tenant

Every dashboard must be tenant aware.

Future white-label support must be considered.
