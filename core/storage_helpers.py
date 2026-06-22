import os
import unicodedata
import re
from django.utils.text import slugify


def _sanitize_filename(filename: str) -> str:
    name = unicodedata.normalize("NFKD", filename).encode("ascii", "ignore").decode("ascii")
    name = re.sub(r"[^A-Za-z0-9.\-_]+", "_", name)
    return name[:255]


def _tenant_slug_from_instance(instance) -> str:
    # Common patterns: instance.tenant.slug, instance.club.tenant.slug, instance.club.slug
    # Fallbacks: instance.tenant_id or instance.pk
    for attr in ("tenant", "club", "team", "organization", "company", "owner"):
        obj = getattr(instance, attr, None)
        if obj:
            slug = getattr(obj, "slug", None) or getattr(obj, "code", None) or getattr(obj, "id", None) or getattr(obj, "pk", None)
            if slug:
                return slugify(str(slug))
    slug = getattr(instance, "slug", None) or getattr(instance, "id", None) or getattr(instance, "pk", None)
    return slugify(str(slug)) if slug else "public"


def player_upload(instance, filename: str) -> str:
    tenant = _tenant_slug_from_instance(instance) or "public"
    filename = _sanitize_filename(filename)
    # optional per-instance directory
    pk_part = getattr(instance, 'pk', None) or getattr(instance, 'id', None)
    if pk_part:
        return os.path.join(tenant, "players", str(pk_part), filename)
    return os.path.join(tenant, "players", filename)


def club_logo_upload(instance, filename: str) -> str:
    tenant = _tenant_slug_from_instance(instance) or "public"
    filename = _sanitize_filename(filename)
    return os.path.join(tenant, "logos", filename)


def stadium_upload(instance, filename: str) -> str:
    tenant = _tenant_slug_from_instance(instance) or "public"
    filename = _sanitize_filename(filename)
    return os.path.join(tenant, "stadiums", filename)


def news_upload(instance, filename: str) -> str:
    tenant = _tenant_slug_from_instance(instance) or "public"
    filename = _sanitize_filename(filename)
    return os.path.join(tenant, "news", filename)


def report_upload(instance, filename: str) -> str:
    tenant = _tenant_slug_from_instance(instance) or "public"
    filename = _sanitize_filename(filename)
    # Use timestamp for generated reports to avoid collisions
    return os.path.join(tenant, "reports", filename)


def onboarding_upload(instance, filename: str) -> str:
    tenant = _tenant_slug_from_instance(instance) or "public"
    filename = _sanitize_filename(filename)
    return os.path.join(tenant, "onboarding", filename)


def documents_upload(instance, filename: str) -> str:
    tenant = _tenant_slug_from_instance(instance) or "public"
    filename = _sanitize_filename(filename)
    return os.path.join(tenant, "documents", filename)
