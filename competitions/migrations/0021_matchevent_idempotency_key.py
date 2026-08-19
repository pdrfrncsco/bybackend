from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("competitions", "0020_match_archived_status")]

    operations = [
        migrations.AddField(
            model_name="matchevent",
            name="idempotency_key",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="Client-generated key used to safely retry event submission.",
                max_length=128,
                null=True,
            ),
        ),
    ]
