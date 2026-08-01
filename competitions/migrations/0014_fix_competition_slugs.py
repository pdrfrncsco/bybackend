"""
Migration to fix truncated or invalid competition slugs.

This migration regenerates slugs for all competitions to ensure they are unique
per tenant+season and not truncated.
"""

from django.db import migrations
from django.utils.text import slugify


def regenerate_slugs(apps, schema_editor):
    """Regenerate slugs for all competitions."""
    Competition = apps.get_model('competitions', 'Competition')
    
    for comp in Competition.objects.all():
        old_slug = comp.slug
        base = slugify(comp.name) or "competition"
        comp.slug = base
        
        # Check for collisions and append counter if needed
        counter = 1
        original_slug = base
        
        while (
            Competition.objects.filter(
                tenant=comp.tenant,
                slug=comp.slug,
                season=comp.season
            ).exclude(id=comp.id).exists()
        ):
            comp.slug = f"{original_slug}-{counter}"
            counter += 1
            
            if counter > 100:
                comp.slug = f"{original_slug}-{comp.id}"
                break
        
        if comp.slug != old_slug:
            comp.save(update_fields=['slug'])
            print(f"Updated slug: {old_slug} → {comp.slug}")


def reverse_migration(apps, schema_editor):
    """Reverse is not applicable as we can't recover original truncated slugs."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0013_alter_matchevent_event_type'),
    ]

    operations = [
        migrations.RunPython(regenerate_slugs, reverse_migration),
    ]
