from django.contrib import admin
from .models import NewsArticle
# Register your models here.
@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'published_at', 'status')
    list_filter = ('category', 'status', 'published_at')
    search_fields = ('title', 'content', 'author')
    date_hierarchy = 'published_at'
    ordering = ('-published_at',)
