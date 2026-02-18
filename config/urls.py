"""URLs raíz del proyecto — incluye Blog, Library y Auth."""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("src.interfaces.api.users.urls")),
    path("api/", include("src.interfaces.api.blog.urls")),
]
