from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("competitions", "0016_tacticalpositions_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="lineupsubmission",
            name="review_notes",
            field=models.TextField(blank=True, default="", verbose_name="Review Notes"),
        ),
        migrations.AddField(
            model_name="lineupsubmission",
            name="reviewed_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Reviewed At"),
        ),
        migrations.AddField(
            model_name="lineupsubmission",
            name="reviewed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="lineup_submissions_reviewed",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Reviewed By",
            ),
        ),
    ]
