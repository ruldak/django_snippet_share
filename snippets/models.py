from django.db import models
from django.utils import timezone
import uuid
from django.contrib.auth.models import User

class Snippet(models.Model):
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('unlisted', 'Unlisted')
    ]
    
    LANGUAGE_CHOICES = [
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('java', 'Java'),
        ('cpp', 'C++'),
        ('html', 'HTML'),
        ('css', 'CSS'),
        ('elixir', 'Elixir'),
        ('php', 'PHP'),
        ('vue', 'Vue'),
        ('laravel', 'Laravel'),
        ('phoenix', 'Phoenix'),
        ('django', 'Django'),
        ('plaintext', 'Plain Text')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='snippets')
    title = models.CharField(max_length=255)
    content = models.TextField()
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default='plaintext')
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'snippets'
        indexes = [
            models.Index(fields=['user', 'visibility']),
            models.Index(fields=['created_at']),
            models.Index(fields=['expires_at']),
        ]
    
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

class AccessLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    snippet = models.ForeignKey(Snippet, on_delete=models.CASCADE, related_name='access_logs')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    accessed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'access_logs'
        indexes = [
            models.Index(fields=['snippet', 'accessed_at']),
        ]