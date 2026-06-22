from django.db import models
from django.conf import settings
from core.models import BaseModel, Tenant

class NewsArticle(BaseModel):
    CATEGORY_CHOICES = (
        ('Comunicado', 'Comunicado'),
        ('Jogo', 'Jogo'),
        ('Transferência', 'Transferência'),
        ('Clube', 'Clube'),
        ('Entrevista', 'Entrevista'),
        ('Notícias', 'Notícias'),
        ('Outros', 'Outros'),
    )

    STATUS_CHOICES = (
        ('draft', 'Rascunho'),
        ('published', 'Publicado'),
    )

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='news')
    title = models.CharField(max_length=255)
    summary = models.TextField()
    content = models.TextField()
    image_url = models.URLField(max_length=500, blank=True, null=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Comunicado')
    author = models.CharField(max_length=100)
    published_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Engagement Metrics
    views = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return self.title


class NewsArticleLike(BaseModel):
    article = models.ForeignKey(NewsArticle, on_delete=models.CASCADE, related_name='article_likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='news_likes')

    class Meta:
        unique_together = ('article', 'user')
