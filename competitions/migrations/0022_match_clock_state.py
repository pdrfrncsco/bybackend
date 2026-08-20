from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("competitions", "0021_matchevent_idempotency_key"),
    ]

    operations = [
        migrations.AddField(
            model_name="match",
            name="clock_elapsed_seconds",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Elapsed seconds in the current period when the clock is paused or last synchronised.",
                verbose_name="Clock Elapsed Seconds",
            ),
        ),
        migrations.AddField(
            model_name="match",
            name="clock_running",
            field=models.BooleanField(default=False, verbose_name="Clock Running"),
        ),
        migrations.AddField(
            model_name="match",
            name="clock_started_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Clock Started At"),
        ),
        migrations.AddField(
            model_name="match",
            name="clock_version",
            field=models.PositiveIntegerField(default=0, verbose_name="Clock Version"),
        ),
        migrations.AddField(
            model_name="match",
            name="stoppage_time_minutes",
            field=models.PositiveSmallIntegerField(default=0, verbose_name="Stoppage Time Minutes"),
        ),
    ]
