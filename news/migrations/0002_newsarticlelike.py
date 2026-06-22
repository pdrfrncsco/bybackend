from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0001_initial'),
        ('news', '0003_alter_newsarticle_category'),
    ]

    operations = [
        migrations.CreateModel(
            name='NewsArticleLike',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='article_likes', to='news.newsarticle')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='news_likes', to='usuarios.user')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='newsarticlelike',
            unique_together={('article', 'user')},
        ),
    ]
