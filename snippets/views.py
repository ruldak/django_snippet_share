from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.vary import vary_on_cookie
from django.db.models import Q, Count
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.db import DatabaseError

from .models import Snippet, AccessLog
from .serializers import SnippetSerializer, SnippetCreateSerializer, SnippetListSerializer
from .permissions import IsOwnerOrReadOnly

class SnippetDetailView(RetrieveAPIView):
    queryset = Snippet.objects.all()
    serializer_class = SnippetSerializer
    lookup_field = "id"

    def get(self, request, *args, **kwargs):
        snippet = self.get_object()
        
        try:
            log = AccessLog.objects.create(
                snippet=snippet,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            cache.clear()
        except DatabaseError as e:
            print("Failed to create access log:", str(e))
        
        return super().get(request, *args, **kwargs)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class SnippetSearchAPIView(ListAPIView):
    serializer_class = SnippetListSerializer
    queryset = Snippet.objects.all()
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'title', 'access_log_count']

    def get_queryset(self):
        query = self.request.query_params.get("q", "")
        language = self.request.query_params.get('language')
        visibility = self.request.query_params.get('visibility')

        qs = Snippet.objects.select_related('user').prefetch_related('access_logs')
        qs = qs.annotate(access_log_count=Count('access_logs'))

        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(content__icontains=query) | Q(language__icontains=query))
        if language:
            qs = qs.filter(language=language)
        if visibility:
            qs = qs.filter(visibility=visibility)

        return qs

    def get(self, request, *args, **kwargs):
        query_params = request.query_params.urlencode()
        cache_key = f"snippet_search_{query_params}"
        data = cache.get(cache_key)

        if not data:
            response = super().get(request, *args, **kwargs)
            data = response.data
            cache.set(cache_key, data, timeout=300)

        return Response(data)

class SnippetViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for managing Snippets.
    """
    queryset = Snippet.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'title', 'access_log_count']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SnippetCreateSerializer
        elif self.action == 'list':
            return SnippetListSerializer
        return SnippetSerializer
    
    def get_queryset(self):
        """
        Returns a filtered queryset based on visibility and user.
        For authenticated users, it shows all their snippets.
        For anonymous users, it only shows public snippets.
        """
        user = self.request.user
        queryset = Snippet.objects.select_related('user').prefetch_related('access_logs')
        language = self.request.query_params.get('language')
        visibility = self.request.query_params.get('visibility')

        queryset = queryset.annotate(access_log_count=Count('access_logs'))

        if language:
            queryset = queryset.filter(language=language)
        if visibility:
            queryset = queryset.filter(visibility=visibility)
        
        queryset = queryset.filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        )
        
        if user.is_authenticated:
            return queryset.filter(user=user)
        else:
            return queryset.filter(visibility='public')
    
    def list(self, request, *args, **kwargs):
        query_params = request.query_params.urlencode()
        cache_key = f"snippets_list_{request.user.username}_{query_params}"
        data = cache.get(cache_key)

        if not data:
            response = super().list(request, *args, **kwargs)
            data = response.data

            cache.set(cache_key, data, timeout=300) 

        return Response(data)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        cache.clear()
        return response

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        cache.clear()
        return response

    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        cache.clear()
        return response
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        cache.clear()
    
    def retrieve(self, request, *args, **kwargs):
        snippet = self.get_object()
        
        try:
            log = AccessLog.objects.create(
                snippet=snippet,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            cache.clear()
        except DatabaseError as e:
            print("Failed to create access log:", str(e))
        
        return super().retrieve(request, *args, **kwargs)
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Endpoint to get snippet analytics."""
        snippet = self.get_object()
        
        if snippet.user != request.user and snippet.visibility != 'public':
            return Response(
                {"detail": "You do not have permission to access this resource."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        access_logs = snippet.access_logs.all()
        total_views = access_logs.count()
        
        from django.db.models.functions import TruncDate
        from django.db.models import Count
        from datetime import timedelta
        
        date_from = timezone.now() - timedelta(days=7)
        daily_views = (
            access_logs.filter(accessed_at__gte=date_from)
            .annotate(date=TruncDate('accessed_at'))
            .values('date')
            .annotate(views=Count('id'))
            .order_by('date')
        )
        
        return Response({
            'total_views': total_views,
            'daily_views': daily_views
        })
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip