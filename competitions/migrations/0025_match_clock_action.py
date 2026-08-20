from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("competitions", "0024_match_extra_time_periods"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MatchClockAction",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("action", models.CharField(max_length=64)),
                ("status_before", models.CharField(blank=True, default="", max_length=20)),
                ("status_after", models.CharField(blank=True, default="", max_length=20)),
                ("period_before", models.CharField(blank=True, default="", max_length=32)),
                ("period_after", models.CharField(blank=True, default="", max_length=32)),
                ("minute_before", models.PositiveSmallIntegerField(default=0)),
                ("minute_after", models.PositiveSmallIntegerField(default=0)),
                ("clock_version", models.PositiveIntegerField(default=0)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="match_clock_actions", to=settings.AUTH_USER_MODEL)),
                ("match", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="clock_actions", to="competitions.match")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="match_clock_actions", to="core.tenant")),
            ],
            options={"ordering": ["-created_at"], "verbose_name": "Match Clock Action", "verbose_name_plural": "Match Clock Actions"},
        ),
    ]
