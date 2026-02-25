"""
MODELOS Django ORM — el único lugar con imports de Django en la infraestructura.

Estos modelos son el esquema de base de datos.
Son DISTINTOS de las Entidades de dominio.

Módulos:
  - Blog:    PostModel, CommentModel, CategoryModel
  - Library: BookModel, AuthorModel, LoanModel
  - Users:   UserModel
"""
import uuid
from django.db import models


# ══════════════════════════════════════════════════════════════
# BLOG MODELS
# ══════════════════════════════════════════════════════════════

class CategoryModel(models.Model):
    """Tabla de Categorías para posts."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, db_index=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "persistence"
        db_table = "blog_categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class PostModel(models.Model):
    """Tabla de Posts del blog."""

    STATUS_CHOICES = [
        ("draft", "Borrador"),
        ("published", "Publicado"),
        ("archived", "Archivado"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, db_index=True)
    content = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
        db_index=True,
    )
    author_id = models.UUIDField(db_index=True)
    category = models.ForeignKey(
        CategoryModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
    )
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        app_label = "persistence"
        db_table = "blog_posts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-published_at"]),
            models.Index(fields=["author_id", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.title} [{self.status}]"


class CommentModel(models.Model):
    """Tabla de Comentarios. Siempre pertenece a un Post."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(
        PostModel,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    body = models.TextField(max_length=1000)
    author_id = models.UUIDField(db_index=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "persistence"
        db_table = "blog_comments"
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author_id} on post {self.post_id}"
