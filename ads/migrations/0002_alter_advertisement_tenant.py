from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('ads', '0001_initial'),
        ('core', '0002_tenant_country_tenant_description_tenant_email_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='advertisement',
            name='tenant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='advertisements', to='core.tenant'),
        ),
    ]
