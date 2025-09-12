from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.vary import vary_on_cookie
from django.db.models import Q
from django.conf import settings
from django.core.cache import cache

from .models import Snippet, AccessLog
from .serializers import SnippetSerializer, SnippetCreateSerializer, SnippetListSerializer
from .permissions import IsOwnerOrReadOnly

class SnippetViewSet(viewsets.ModelViewSet):
    """
    ViewSet untuk mengelola Snippet.
    """
    queryset = Snippet.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SnippetCreateSerializer
        elif self.action == 'list':
            return SnippetListSerializer
        return SnippetSerializer
    
    def get_queryset(self):
        """
        Mengembalikan queryset yang difilter berdasarkan visibility dan user.
        Untuk user terautentikasi, tampilkan semua snippet milik mereka plus public.
        Untuk user anonymous, hanya tampilkan snippet public.
        """
        user = self.request.user
        queryset = Snippet.objects.select_related('user').prefetch_related('access_logs')
        
        # Filter out expired snippets
        queryset = queryset.filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        )
        
        if user.is_authenticated:
            # Untuk user terautentikasi, tampilkan semua milik mereka plus public
            return queryset.filter(Q(visibility='public') | Q(user=user))
        else:
            # Untuk anonymous user, hanya tampilkan public
            return queryset.filter(visibility='public')
    
    def list(self, request, *args, **kwargs):
        cache_key = f"snippets_list_{request.get_full_path()}"
        data = cache.get(cache_key)

        if not data:
            # ambil data normal (pakai super().list)
            response = super().list(request, *args, **kwargs)
            data = response.data

            # simpan ke cache 5 menit
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
        # Log access
        snippet = self.get_object()
        
        # Buat access log
        AccessLog.objects.create(
            snippet=snippet,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return super().retrieve(request, *args, **kwargs)
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Endpoint untuk mendapatkan analytics snippet"""
        snippet = self.get_object()
        
        # Cek permission
        if snippet.user != request.user and snippet.visibility != 'public':
            return Response(
                {"detail": "You do not have permission to access this resource."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        access_logs = snippet.access_logs.all()
        total_views = access_logs.count()
        
        # Hitung views per hari (7 hari terakhir)
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