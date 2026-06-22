from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clubes', '0004_alter_club_stadium_name'),
        ('torneios', '0004_alter_tournament_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='tournament',
            name='champion_club',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='tournaments_won',
                to='clubes.club',
            ),
        ),
        migrations.AddField(
            model_name='tournament',
            name='runner_up_club',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='tournaments_runner_up',
                to='clubes.club',
            ),
        ),
    ]

