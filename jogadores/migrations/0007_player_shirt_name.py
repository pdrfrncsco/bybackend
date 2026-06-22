from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jogadores", "0006_alter_player_position"),
    ]

    operations = [
        migrations.AddField(
            model_name="player",
            name="shirt_name",
            field=models.CharField(max_length=15, blank=True),
        ),
    ]

