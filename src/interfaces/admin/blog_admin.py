"""
DJANGO ADMIN customizado para el módulo Blog.

El Admin de Django es otro Adaptador Primario, igual que las Views API.
Proporciona una interfaz gráfica para gestionar Posts, Categorías y Comentarios.

Buenas prácticas en Admin con arquitectura hexagonal:
  - El Admin trabaja con los MODELOS ORM (no con el dominio directamente)
  - Para acciones complejas (publicar, archivar), llama a los CommandHandlers
  - No duplica lógica de negocio — la delega al dominio
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse

from src.infrastructure.persistence.models import PostModel, CommentModel


# ─────────────────────────────────────────────────────────────
# COMMENT INLINE
# ─────────────────────────────────────────────────────────────
class CommentInline(admin.TabularInline):
    """Muestra los comentarios inline dentro del Post."""
    model = CommentModel
    extra = 0
    readonly_fields = ("id", "author_id", "created_at")
    fields = ("id", "body", "author_id", "created_at")
    can_delete = True

    def has_add_permission(self, request, obj=None):
        return False  # Los comentarios se crean vía API, no desde Admin


# ─────────────────────────────────────────────────────────────
# POST ADMIN
# ─────────────────────────────────────────────────────────────
@admin.register(PostModel)
class PostAdmin(admin.ModelAdmin):
    """
    Admin customizado para Posts.
    Incluye acciones bulk para publicar/archivar posts.
    """

    # ── Listado ──────────────────────────────────────────────
    list_display = (
        "title",
        "status_badge",
        "author_id",
        "created_at",
        "published_at",
        "comment_count",
    )
    list_filter = ("status", "created_at", "published_at")
    search_fields = ("title", "slug", "author_id")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    # ── Detalle ──────────────────────────────────────────────
    readonly_fields = ("id", "slug", "created_at", "published_at")
    fieldsets = (
        ("📝 Contenido", {
            "fields": ("title", "slug", "content", "tags")
        }),
        ("📊 Estado", {
            "fields": ("status", "author_id", "created_at", "published_at")
        }),
    )
    inlines = [CommentInline]

    # ── Acciones ─────────────────────────────────────────────
    actions = ["publish_posts", "archive_posts"]

    @admin.action(description="✅ Publicar posts seleccionados")
    def publish_posts(self, request, queryset):
        """
        Acción bulk: usa el CommandHandler para publicar
        (respeta las reglas de negocio del dominio).
        """
        from config.container import get_publish_post_handler
        from src.application.blog.commands.publish_post import PublishPostCommand

        published = 0
        errors = 0
        for post_model in queryset.filter(status="draft"):
            try:
                command = PublishPostCommand(
                    post_id=post_model.id,
                    requesting_author_id=post_model.author_id,
                )
                get_publish_post_handler().handle(command)
                published += 1
            except Exception as e:
                errors += 1
                self.message_user(
                    request,
                    f"Error publicando '{post_model.title}': {e}",
                    level="error"
                )

        if published:
            self.message_user(request, f"✅ {published} posts publicados.")
        if errors:
            self.message_user(
                request,
                f"⚠️ {errors} posts no pudieron publicarse.",
                level="warning"
            )

    @admin.action(description="📦 Archivar posts seleccionados")
    def archive_posts(self, request, queryset):
        from config.container import get_archive_post_handler
        from src.application.blog.commands.archive_post import ArchivePostCommand

        archived = 0
        for post_model in queryset.exclude(status="archived"):
            try:
                command = ArchivePostCommand(
                    post_id=post_model.id,
                    requesting_author_id=post_model.author_id,
                )
                get_archive_post_handler().handle(command)
                archived += 1
            except Exception as e:
                self.message_user(request, f"Error: {e}", level="error")

        if archived:
            self.message_user(request, f"📦 {archived} posts archivados.")

    # ── Campos personalizados ────────────────────────────────
    @admin.display(description="Estado", ordering="status")
    def status_badge(self, obj):
        """Muestra el estado con colores en el listado."""
        colors = {
            "draft": "#6c757d",
            "published": "#28a745",
            "archived": "#dc3545",
        }
        icons = {
            "draft": "📝",
            "published": "✅",
            "archived": "📦",
        }
        color = colors.get(obj.status, "#000")
        icon = icons.get(obj.status, "")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_status_display()
        )

    @admin.display(description="Comentarios")
    def comment_count(self, obj):
        count = obj.comments.count()
        return format_html(
            '<span style="color: #007bff;">💬 {}</span>', count
        )


# ─────────────────────────────────────────────────────────────
# COMMENT ADMIN
# ─────────────────────────────────────────────────────────────
@admin.register(CommentModel)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("__str__", "post", "author_id", "created_at")
    list_filter = ("created_at",)
    search_fields = ("body", "author_id")
    readonly_fields = ("id", "post", "author_id", "created_at")
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False  # Comentarios solo se crean vía API
