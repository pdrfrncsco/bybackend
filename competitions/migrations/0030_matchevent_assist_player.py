from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0001_initial'),
        ('competitions', '0029_competition_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='matchevent',
            name='assist_player',
            field=models.ForeignKey(
                blank=True,
                help_text='Only used for GOAL / PENALTY_SCORED — the player who provided the assist.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='assist_events',
                to='players.player',
                verbose_name='Assist Player',
            ),
        ),
    ]
