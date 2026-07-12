from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("media_assets", "0002_alter_mediaasset_owner_type_and_more"),
        ("players", "0003_playerregistrationrequest"),
    ]

    operations = [
        migrations.AddField(
            model_name="playerachievement",
            name="certificate_asset",
            field=models.ForeignKey(
                blank=True,
                help_text="Uploaded certificate via DAM",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="player_achievement_certificates",
                to="media_assets.mediaasset",
                verbose_name="Certificate Asset",
            ),
        ),
        migrations.AddField(
            model_name="playerachievement",
            name="trophy_asset",
            field=models.ForeignKey(
                blank=True,
                help_text="Uploaded trophy image via DAM",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="player_achievement_trophies",
                to="media_assets.mediaasset",
                verbose_name="Trophy Asset",
            ),
        ),
    ]
