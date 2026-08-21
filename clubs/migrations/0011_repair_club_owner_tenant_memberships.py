from django.db import migrations


def repair_club_owner_tenant_memberships(apps, schema_editor):
    ClubMember = apps.get_model("clubs", "ClubMember")
    TenantMembership = apps.get_model("accounts", "TenantMembership")

    owners = ClubMember.objects.filter(
        role="president",
        is_active=True,
        club__status="active",
    ).values("user_id", "club__tenant_id")

    for owner in owners.iterator():
        TenantMembership.objects.update_or_create(
            user_id=owner["user_id"],
            tenant_id=owner["club__tenant_id"],
            defaults={"role": "member", "is_active": True},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_user_profile_type"),
        ("clubs", "0010_alter_clubaffiliationrequest_status"),
    ]

    operations = [
        migrations.RunPython(
            repair_club_owner_tenant_memberships,
            migrations.RunPython.noop,
        ),
    ]
