from rest_framework import serializers
from .models import NewsArticle

class NewsArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsArticle
        fields = [
            'id', 
            'title', 
            'summary', 
            'content', 
            'image_url', 
            'category', 
            'author', 
            'published_at', 
            'status',
            'views',
            'likes',
            'shares',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'views', 'likes', 'shares']

    def create(self, validated_data):
        # Assign tenant from context if needed, or handle in view
        request = self.context.get('request')
        if request and hasattr(request.user, 'tenant') and request.user.tenant:
             validated_data['tenant'] = request.user.tenant
        return super().create(validated_data)
