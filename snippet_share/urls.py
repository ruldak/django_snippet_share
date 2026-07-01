from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from snippets.views import SnippetViewSet
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from users.views import RegisterView, UserProfileView
from snippets.views import SnippetSearchAPIView, SnippetDetailView

router = DefaultRouter()
router.register(r'snippets', SnippetViewSet, basename='snippet')

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path("api/profile/", UserProfileView.as_view(), name="user-profile"),
    path('api/', include(router.urls)),
    path("api/search/", SnippetSearchAPIView.as_view(), name="snippets-search"),
    path("api/snippet/detail/<uuid:id>/", SnippetDetailView.as_view(), name="snippet-detail"),
]
