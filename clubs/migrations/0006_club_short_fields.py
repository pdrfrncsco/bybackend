from django.db import migrations, models
from django.core.validators import RegexValidator


class Migration(migrations.Migration):

    dependencies = [
        ("clubs", "0005_club_active_players_club_stadium_capacity_staff"),
    ]

    operations = [
        migrations.AddField(
            model_name="club",
            name="acronym",
            field=models.CharField(
                max_length=3,
                blank=True,
                validators=[
                    RegexValidator(
                        regex=r"^[A-Z]{3}$",
                        message="A sigla deve ter exatamente 3 letras maiúsculas.",
                        code="invalid_acronym",
                    )
                ],
            ),
        ),
        migrations.AddField(
            model_name="club",
            name="short_name",
            field=models.CharField(max_length=12, blank=True),
        ),
    ]

