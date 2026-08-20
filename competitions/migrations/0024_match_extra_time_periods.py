from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("competitions", "0023_match_penalty_scores")]

    operations = [
        migrations.AlterField(
            model_name="match",
            name="current_period",
            field=models.CharField(
                blank=True,
                choices=[
                    ("first_half", "1º Tempo"),
                    ("second_half", "2º Tempo"),
                    ("extra_time", "Prorrogação"),
                    ("extra_first_half", "1º período do prolongamento"),
                    ("extra_halftime", "Intervalo do prolongamento"),
                    ("extra_second_half", "2º período do prolongamento"),
                    ("penalties", "Penaltis"),
                    ("halftime", "Intervalo"),
                    ("fulltime", "Fim de jogo"),
                ],
                default=None,
                max_length=20,
                null=True,
                verbose_name="Current Period",
            ),
        ),
    ]
