"""URLs raíz del proyecto — incluye Blog, Library y Auth."""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    # Admin Django
    path("admin/", admin.site.urls),
    
    # API Endpoints
    path("api/auth/", include("src.interfaces.api.users.urls")),
    path("api/", include("src.interfaces.api.blog.urls")),
    
    # Library API
    path("api/library/", include("src.interfaces.api.library.urls")),
    
    # OpenAPI Schema & Docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
