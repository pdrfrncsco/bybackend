from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clubes', '0002_clubhistory'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='club',
            name='stadium_capacity',
        ),
    ]
