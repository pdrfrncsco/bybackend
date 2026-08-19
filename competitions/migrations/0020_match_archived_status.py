from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("competitions", "0019_match_current_minute_match_current_period")]

    operations = [
        migrations.AlterField(
            model_name="match",
            name="status",
            field=models.CharField(
                choices=[
                    ("scheduled", "Agendado"), ("pre_match", "Pré-jogo"),
                    ("live", "Em Curso"), ("halftime", "Intervalo"),
                    ("finished", "Concluído"), ("archived", "Arquivado"),
                    ("postponed", "Adiado"), ("cancelled", "Cancelado"),
                    ("walkover", "Walkover"),
                ],
                default="scheduled", max_length=20, verbose_name="Status",
            ),
        ),
    ]
