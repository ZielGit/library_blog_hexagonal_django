"""
Migración inicial — crea todas las tablas del proyecto.

Generada automáticamente para:
  - blog_categories
  - blog_posts
  - blog_comments
  - library_authors
  - library_books
  - library_loans
  - users
"""
import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        # ── BLOG: Categories ──────────────────────────────────
        migrations.CreateModel(
            name="CategoryModel",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("name", models.CharField(max_length=100, unique=True)),
                ("slug", models.SlugField(max_length=120, unique=True)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "blog_categories",
                "ordering": ["name"],
            },
        ),

        # ── BLOG: Posts ───────────────────────────────────────
        migrations.CreateModel(
            name="PostModel",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("title", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=220, unique=True)),
                ("content", models.TextField()),
                ("status", models.CharField(
                    choices=[("draft","Borrador"),("published","Publicado"),("archived","Archivado")],
                    default="draft",
                    max_length=20,
                )),
                ("author_id", models.UUIDField()),
                ("category", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="posts",
                    to="persistence.categorymodel",
                )),
                ("tags", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": "blog_posts",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="postmodel",
            index=models.Index(fields=["status", "-published_at"], name="blog_posts_status_pub_idx"),
        ),
        migrations.AddIndex(
            model_name="postmodel",
            index=models.Index(fields=["author_id", "-created_at"], name="blog_posts_author_idx"),
        ),

        # ── BLOG: Comments ────────────────────────────────────
        migrations.CreateModel(
            name="CommentModel",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("post", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="comments",
                    to="persistence.postmodel",
                )),
                ("body", models.TextField(max_length=1000)),
                ("author_id", models.UUIDField()),
                ("is_deleted", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "blog_comments",
                "ordering": ["created_at"],
            },
        ),

        # ── LIBRARY: Authors ──────────────────────────────────
        migrations.CreateModel(
            name="AuthorModel",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("name", models.CharField(max_length=200)),
                ("bio", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "library_authors",
                "ordering": ["name"],
            },
        ),

        # ── LIBRARY: Books ────────────────────────────────────
        migrations.CreateModel(
            name="BookModel",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("isbn", models.CharField(max_length=13, unique=True)),
                ("title", models.CharField(max_length=300)),
                ("author", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="books",
                    to="persistence.authormodel",
                )),
                ("description", models.TextField(blank=True)),
                ("total_copies", models.PositiveIntegerField(default=1)),
                ("available_copies", models.PositiveIntegerField(default=1)),
                ("published_year", models.PositiveIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "library_books",
                "ordering": ["title"],
            },
        ),

        # ── LIBRARY: Loans ────────────────────────────────────
        migrations.CreateModel(
            name="LoanModel",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("book", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="loans",
                    to="persistence.bookmodel",
                )),
                ("user_id", models.UUIDField()),
                ("status", models.CharField(
                    choices=[("active","Activo"),("returned","Devuelto"),("overdue","Vencido")],
                    default="active",
                    max_length=20,
                )),
                ("loaned_at", models.DateTimeField()),
                ("due_date", models.DateTimeField()),
                ("returned_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": "library_loans",
                "ordering": ["-loaned_at"],
            },
        ),
        migrations.AddIndex(
            model_name="loanmodel",
            index=models.Index(fields=["user_id", "status"], name="loans_user_status_idx"),
        ),
        migrations.AddIndex(
            model_name="loanmodel",
            index=models.Index(fields=["status", "due_date"], name="loans_status_due_idx"),
        ),

        # ── USERS ─────────────────────────────────────────────
        migrations.CreateModel(
            name="UserModel",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("email", models.EmailField(unique=True)),
                ("username", models.CharField(max_length=50, unique=True)),
                ("hashed_password", models.CharField(max_length=255)),
                ("role", models.CharField(
                    choices=[("admin","Administrador"),("editor","Editor"),("reader","Lector")],
                    default="reader",
                    max_length=20,
                )),
                ("status", models.CharField(
                    choices=[("active","Activo"),("inactive","Inactivo"),("banned","Baneado")],
                    default="active",
                    max_length=20,
                )),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_login", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": "users",
                "ordering": ["-created_at"],
            },
        ),
    ]
