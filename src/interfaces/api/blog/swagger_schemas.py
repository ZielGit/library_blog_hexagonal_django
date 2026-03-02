"""
Schemas de drf-spectacular para documentar la API del blog.

Estos decoradores se agregan a las views para que Swagger
muestre correctamente los parámetros, request bodies, y responses.
"""
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers


# ═══════════════════════════════════════════════════════════════
# SERIALIZERS (para request/response schemas)
# ═══════════════════════════════════════════════════════════════

class CreatePostRequestSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200, help_text="Título del post")
    content = serializers.CharField(
        help_text="Contenido (mínimo 100 caracteres para poder publicar)"
    )
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Lista de tags (ej: ['django', 'python'])"
    )


class CreatePostResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    slug = serializers.CharField()
    title = serializers.CharField()


class AddCommentRequestSerializer(serializers.Serializer):
    body = serializers.CharField(
        max_length=1000,
        help_text="Contenido del comentario (máx 1000 caracteres)"
    )


class AddCommentResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    body = serializers.CharField()
    created_at = serializers.DateTimeField()


class MessageResponseSerializer(serializers.Serializer):
    message = serializers.CharField()


# ═══════════════════════════════════════════════════════════════
# SCHEMA DECORATORS
# ═══════════════════════════════════════════════════════════════

create_post_schema = extend_schema(
    summary="Crear post",
    description=(
        "Crea un nuevo post en estado **draft**. "
        "Para hacerlo visible, debes publicarlo con POST /api/posts/{id}/publish/.\n\n"
        "**Reglas:**\n"
        "- Requiere autenticación JWT\n"
        "- Content debe tener ≥100 caracteres para poder publicar después"
    ),
    request=CreatePostRequestSerializer,
    responses={
        201: CreatePostResponseSerializer,
        401: {"description": "No autenticado"},
        422: {"description": "Error de validación de dominio"},
    },
    examples=[
        OpenApiExample(
            "Post de ejemplo",
            value={
                "title": "Mi primer post en Django",
                "content": (
                    "Este es el contenido del post. Debe ser suficientemente "
                    "largo para cumplir con la regla de negocio que requiere "
                    "un mínimo de 100 caracteres antes de poder publicar."
                ),
                "tags": ["django", "hexagonal", "python"]
            },
            request_only=True,
        )
    ],
    tags=["Blog - Posts"],
)

publish_post_schema = extend_schema(
    summary="Publicar post",
    description=(
        "Cambia el estado del post de **draft** a **published**.\n\n"
        "**Reglas:**\n"
        "- Content debe tener ≥100 caracteres\n"
        "- No se puede publicar un post ya publicado\n"
        "- No se puede publicar un post archivado"
    ),
    request=None,  # No hay body
    responses={
        200: MessageResponseSerializer,
        401: {"description": "No autenticado"},
        404: {"description": "Post no encontrado"},
        422: {"description": "No se puede publicar (ej: ya publicado, content muy corto)"},
    },
    tags=["Blog - Posts"],
)

archive_post_schema = extend_schema(
    summary="Archivar post",
    description=(
        "Cambia el estado del post de **published** a **archived**.\n\n"
        "**Reglas:**\n"
        "- Solo el autor puede archivar su post\n"
        "- No se puede archivar un post en draft\n"
        "- El archivado es permanente (no se puede revertir)"
    ),
    request=None,
    responses={
        200: MessageResponseSerializer,
        401: {"description": "No autenticado"},
        403: {"description": "No eres el autor"},
        404: {"description": "Post no encontrado"},
        422: {"description": "No se puede archivar (ej: ya archivado)"},
    },
    tags=["Blog - Posts"],
)

add_comment_schema = extend_schema(
    summary="Agregar comentario",
    description=(
        "Añade un comentario a un post publicado.\n\n"
        "**Reglas:**\n"
        "- Máximo 1000 caracteres\n"
        "- No se puede comentar en posts archivados"
    ),
    request=AddCommentRequestSerializer,
    responses={
        201: AddCommentResponseSerializer,
        401: {"description": "No autenticado"},
        404: {"description": "Post no encontrado"},
        422: {"description": "No se puede comentar (ej: post archivado)"},
    },
    examples=[
        OpenApiExample(
            "Comentario simple",
            value={"body": "Excelente artículo, gracias por compartir!"},
            request_only=True,
        )
    ],
    tags=["Blog - Comentarios"],
)
