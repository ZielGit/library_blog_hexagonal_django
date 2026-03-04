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


# ══════════════════════════════════════════════════════════════
# LIBRARY MODELS
# ══════════════════════════════════════════════════════════════

class AuthorModel(models.Model):
    """Tabla de Autores de libros."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "persistence"
        db_table = "library_authors"
        ordering = ["name"]

    def __str__(self):
        return self.name


class BookModel(models.Model):
    """Tabla de Libros de la biblioteca."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    isbn = models.CharField(max_length=13, unique=True, db_index=True)
    title = models.CharField(max_length=300)
    author = models.ForeignKey(
        AuthorModel,
        on_delete=models.PROTECT,
        related_name="books",
    )
    description = models.TextField(blank=True)
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    published_year = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "persistence"
        db_table = "library_books"
        ordering = ["title"]
        indexes = [
            models.Index(fields=["available_copies"]),
        ]

    def __str__(self):
        return f"{self.title} (ISBN: {self.isbn})"


class LoanModel(models.Model):
    """Tabla de Préstamos de libros."""

    STATUS_CHOICES = [
        ("active", "Activo"),
        ("returned", "Devuelto"),
        ("overdue", "Vencido"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    book = models.ForeignKey(
        BookModel,
        on_delete=models.PROTECT,
        related_name="loans",
    )
    user_id = models.UUIDField(db_index=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
        db_index=True,
    )
    loaned_at = models.DateTimeField()
    due_date = models.DateTimeField(db_index=True)
    returned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "persistence"
        db_table = "library_loans"
        ordering = ["-loaned_at"]
        indexes = [
            models.Index(fields=["user_id", "status"]),
            models.Index(fields=["status", "due_date"]),
        ]

    def __str__(self):
        return f"Loan {self.id} — book {self.book_id} to user {self.user_id} [{self.status}]"


# ══════════════════════════════════════════════════════════════
# USER MODELS
# ══════════════════════════════════════════════════════════════

class UserModel(models.Model):
    """
    Tabla de usuarios del sistema.
    No usa AbstractUser de Django — gestionamos auth con JWT propio.
    Si prefieres usar Django auth, puedes extender AbstractUser aquí.
    """

    ROLE_CHOICES = [
        ("admin", "Administrador"),
        ("editor", "Editor"),
        ("reader", "Lector"),
    ]

    STATUS_CHOICES = [
        ("active", "Activo"),
        ("inactive", "Inactivo"),
        ("banned", "Baneado"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(max_length=50, unique=True, db_index=True)
    hashed_password = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="reader")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "persistence"
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.username} <{self.email}> [{self.role}]"
