from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("competitions", "0022_match_clock_state")]

    operations = [
        migrations.AddField(
            model_name="match",
            name="home_penalty_score",
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Home Penalty Shootout Score"),
        ),
        migrations.AddField(
            model_name="match",
            name="away_penalty_score",
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Away Penalty Shootout Score"),
        ),
    ]
