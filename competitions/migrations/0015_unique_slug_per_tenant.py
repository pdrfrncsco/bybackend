from django.db import migrations
from django.db.models import Count, UniqueConstraint


def fix_duplicate_slugs(apps, schema_editor):
    Competition = apps.get_model('competitions', 'Competition')

    # Find (tenant, slug) groups with more than 1 competition
    duplicates = (
        Competition.objects
        .values('tenant_id', 'slug')
        .annotate(cnt=Count('id'))
        .filter(slug__isnull=False)
        .filter(cnt__gt=1)
    )

    for dup in duplicates:
        tenant_id = dup['tenant_id']
        slug = dup['slug']

        comps = list(
            Competition.objects.filter(tenant_id=tenant_id, slug=slug).order_by('created_at', 'id')
        )
        # Keep first; rename others
        for comp in comps[1:]:
            base = f"{slug}-{str(comp.id)[:8]}"
            candidate = base
            suffix = 1
            while Competition.objects.filter(tenant_id=tenant_id, slug=candidate).exists():
                candidate = f"{base}-{suffix}"
                suffix += 1
            comp.slug = candidate
            comp.save(update_fields=['slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0014_fix_competition_slugs'),
    ]

    operations = [
        migrations.RunPython(fix_duplicate_slugs, reverse_code=migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='competition',
            constraint=UniqueConstraint(fields=['tenant', 'slug'], name='unique_competition_slug_per_tenant'),
        ),
    ]
