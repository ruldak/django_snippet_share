from rest_framework import serializers
from .models import Snippet, AccessLog
from django.utils import timezone

class SnippetSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = Snippet
        fields = ['id', 'user', 'title', 'content', 'language', 
                 'visibility', 'expires_at', 'created_at', 'updated_at', 'is_expired']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'is_expired']
    
    def validate(self, data):
        # Validasi expires_at harus di masa depan jika disediakan
        expires_at = data.get('expires_at')
        if expires_at and expires_at <= timezone.now():
            raise serializers.ValidationError("Expiration date must be in the future")
        return data

class SnippetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Snippet
        fields = ['title', 'content', 'language', 'visibility', 'expires_at']

class SnippetListSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    preview = serializers.SerializerMethodField()
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = Snippet
        fields = ['id', 'user', 'title', 'preview', 'language', 
                 'visibility', 'created_at', 'is_expired']
    
    def get_preview(self, obj):
        # Hanya mengambil 100 karakter pertama sebagai preview
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content