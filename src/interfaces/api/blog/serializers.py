"""
SERIALIZERS de Django REST Framework para el módulo Blog.

Los serializers son parte de la capa de interfaces.
Su responsabilidad: validar y transformar datos de entrada HTTP
antes de crear Commands, y dar formato a los DTOs de salida.

NO contienen lógica de negocio — eso vive en el dominio.
"""
from rest_framework import serializers


# ─────────────────────────────────────────────────────────────
# INPUT SERIALIZERS (validan datos de entrada)
# ─────────────────────────────────────────────────────────────
class CreatePostInputSerializer(serializers.Serializer):
    """Valida el body del POST /api/posts/"""
    title = serializers.CharField(
        max_length=200,
        min_length=3,
        error_messages={
            "blank": "El título no puede estar vacío.",
            "max_length": "El título no puede exceder 200 caracteres.",
        }
    )
    content = serializers.CharField(
        min_length=1,
        error_messages={"blank": "El contenido no puede estar vacío."}
    )
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        default=list,
        max_length=10,
    )
    category_id = serializers.UUIDField(required=False, allow_null=True, default=None)


class AddCommentInputSerializer(serializers.Serializer):
    """Valida el body del POST /api/posts/{id}/comments/"""
    body = serializers.CharField(
        max_length=1000,
        min_length=1,
        error_messages={
            "blank": "El comentario no puede estar vacío.",
            "max_length": "El comentario no puede exceder 1000 caracteres.",
        }
    )


class UpdatePostInputSerializer(serializers.Serializer):
    """Valida el body del PATCH /api/posts/{id}/"""
    title = serializers.CharField(max_length=200, min_length=3, required=False)
    content = serializers.CharField(min_length=1, required=False)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
    )


# ─────────────────────────────────────────────────────────────
# OUTPUT SERIALIZERS (formatean DTOs para la respuesta)
# ─────────────────────────────────────────────────────────────
class CommentOutputSerializer(serializers.Serializer):
    """Formatea un CommentDTO para la respuesta JSON."""
    id = serializers.UUIDField()
    body = serializers.CharField()
    author_id = serializers.UUIDField()
    created_at = serializers.DateTimeField()


class PostDetailOutputSerializer(serializers.Serializer):
    """Formatea un PostDetailDTO para la respuesta JSON."""
    id = serializers.UUIDField()
    title = serializers.CharField()
    slug = serializers.CharField()
    content = serializers.CharField()
    excerpt = serializers.CharField()
    status = serializers.CharField()
    author_id = serializers.UUIDField()
    category_id = serializers.UUIDField(allow_null=True)
    tags = serializers.ListField(child=serializers.CharField())
    word_count = serializers.IntegerField()
    comments = CommentOutputSerializer(many=True)
    created_at = serializers.DateTimeField()
    published_at = serializers.DateTimeField(allow_null=True)


class PostSummaryOutputSerializer(serializers.Serializer):
    """Formatea un PostSummaryDTO para listados."""
    id = serializers.UUIDField()
    title = serializers.CharField()
    slug = serializers.CharField()
    excerpt = serializers.CharField()
    status = serializers.CharField()
    author_id = serializers.UUIDField()
    tags = serializers.ListField(child=serializers.CharField())
    created_at = serializers.DateTimeField()
    published_at = serializers.DateTimeField(allow_null=True)


class PostListOutputSerializer(serializers.Serializer):
    """Formatea un PostListDTO con paginación."""
    items = PostSummaryOutputSerializer(many=True)
    total = serializers.IntegerField()
    page = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    has_next = serializers.BooleanField()
    has_previous = serializers.BooleanField()
