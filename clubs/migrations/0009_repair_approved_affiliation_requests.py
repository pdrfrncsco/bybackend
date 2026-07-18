from django.db import migrations
from django.utils.text import slugify


def _unique_slug(Club, tenant_id, name):
    base = slugify(name) or "club"
    slug = base
    counter = 1

    while Club.objects.filter(tenant_id=tenant_id, slug=slug).exists():
        slug = f"{base}-{counter}"
        counter += 1

    return slug


def repair_approved_affiliation_requests(apps, schema_editor):
    Club = apps.get_model("clubs", "Club")
    ClubAffiliationRequest = apps.get_model("clubs", "ClubAffiliationRequest")
    ClubMember = apps.get_model("clubs", "ClubMember")

    requests = ClubAffiliationRequest.objects.filter(
        status="approved",
        club__isnull=True,
    ).select_related("tenant", "submitted_by")

    for request in requests:
        club = Club.objects.filter(
            tenant_id=request.tenant_id,
            name__iexact=request.name,
        ).first()

        if club is None:
            club = Club.objects.create(
                tenant_id=request.tenant_id,
                name=request.name,
                slug=_unique_slug(Club, request.tenant_id, request.name),
                short_name=request.short_name,
                founded_year=request.founded_year,
                city=request.city,
                country=request.country,
                email=request.email,
                phone=request.phone,
                website=request.website,
                description=request.description,
                primary_color=request.primary_color,
                secondary_color=request.secondary_color,
                stadium_name=request.stadium_name,
                stadium_capacity=request.stadium_capacity,
                status="active",
                is_public=True,
                is_verified=False,
            )
        elif club.status != "active":
            club.status = "active"
            club.save(update_fields=["status", "updated_at"])

        if request.submitted_by_id:
            ClubMember.objects.update_or_create(
                club_id=club.id,
                user_id=request.submitted_by_id,
                defaults={
                    "role": "president",
                    "is_active": True,
                },
            )

        request.club_id = club.id
        request.save(update_fields=["club", "updated_at"])


class Migration(migrations.Migration):
    dependencies = [
        ("clubs", "0008_add_transfer_model"),
    ]

    operations = [
        migrations.RunPython(repair_approved_affiliation_requests, migrations.RunPython.noop),
    ]
