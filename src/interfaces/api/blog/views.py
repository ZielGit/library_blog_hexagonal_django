"""
VISTAS Django REST Framework — Adaptadores Primarios (Puerto de Entrada).

Las vistas son el "lado izquierdo" del hexágono.
Su única responsabilidad: traducir HTTP ↔ Commands/Queries.

NO deben contener lógica de negocio. Si ves un if/else de negocio
aquí, es una señal de que debe moverse al dominio o la application.

Flujo de un request:
  HTTP Request
    → View (valida formato HTTP, autentica)
      → Command/Query (datos limpios)
        → Handler (lógica de aplicación)
          → Domain (lógica de negocio)
            → Repository (persistencia)
          ← DTO
        ← DTO
      ← Response JSON
    ← HTTP Response
"""
from uuid import UUID

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from .swagger_schemas import (
    create_post_schema,
    publish_post_schema,
    archive_post_schema,
    add_comment_schema,
)

from config.container import (
    get_create_post_handler,
    get_publish_post_handler,
    get_add_comment_handler,
    get_archive_post_handler,
    get_post_by_slug_handler,
    get_list_posts_handler,
    get_posts_by_author_handler,
)
from src.application.blog.commands.create_post import CreatePostCommand
from src.application.blog.commands.publish_post import PublishPostCommand
from src.application.blog.commands.add_comment import AddCommentCommand
from src.application.blog.commands.archive_post import ArchivePostCommand
from src.application.blog.queries.get_post import GetPostBySlugQuery
from src.application.blog.queries.list_posts import ListPublishedPostsQuery, ListPostsByAuthorQuery
from src.domain.shared.base import DomainError, NotFoundError
from src.infrastructure.auth.drf_jwt_authentication import JWTAuthentication as JWTAuth


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def handle_domain_error(exc: Exception) -> Response:
    """Convierte excepciones de dominio a respuestas HTTP."""
    if isinstance(exc, NotFoundError):
        return Response({"error": str(exc)}, status=status.HTTP_404_NOT_FOUND)
    if isinstance(exc, DomainError):
        return Response({"error": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    raise exc


# ─────────────────────────────────────────────────────────────
# POST VIEWS
# ─────────────────────────────────────────────────────────────
class PostListCreateView(APIView):
    """
    GET  /api/posts/         → Lista posts publicados (paginado)
    POST /api/posts/         → Crea un nuevo post (requiere auth JWT)
    """
    authentication_classes = [JWTAuth]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        query = ListPublishedPostsQuery(
            page=int(request.query_params.get("page", 1)),
            page_size=int(request.query_params.get("page_size", 10)),
            tag=request.query_params.get("tag"),
        )
        handler = get_list_posts_handler()
        result = handler.handle(query)

        return Response({
            "items": [
                {
                    "id": str(p.id),
                    "title": p.title,
                    "slug": p.slug,
                    "excerpt": p.excerpt,
                    "tags": p.tags,
                    "published_at": p.published_at.isoformat() if p.published_at else None,
                }
                for p in result.items
            ],
            "total": result.total,
            "page": result.page,
            "total_pages": result.total_pages,
            "has_next": result.has_next,
            "has_previous": result.has_previous,
        })

    @create_post_schema
    def post(self, request):
        try:
            command = CreatePostCommand(
                title=request.data.get("title", ""),
                content=request.data.get("content", ""),
                author_id=UUID(str(request.user.id)),
                tags=request.data.get("tags", []),
            )
            handler = get_create_post_handler()
            result = handler.handle(command)

            return Response(
                {"id": str(result.id), "slug": result.slug, "title": result.title},
                status=status.HTTP_201_CREATED,
            )
        except (DomainError, NotFoundError) as e:
            return handle_domain_error(e)
        except (ValueError, KeyError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PostDetailView(APIView):
    """
    GET  /api/posts/<slug>/         → Detalle de un post
    """
    permission_classes = [AllowAny]

    def get(self, request, slug: str):
        try:
            query = GetPostBySlugQuery(slug=slug)
            handler = get_post_by_slug_handler()
            result = handler.handle(query)

            return Response({
                "id": str(result.id),
                "title": result.title,
                "slug": result.slug,
                "content": result.content,
                "excerpt": result.excerpt,
                "status": result.status,
                "author_id": str(result.author_id),
                "tags": result.tags,
                "word_count": result.word_count,
                "comments": [
                    {
                        "id": str(c.id),
                        "body": c.body,
                        "author_id": str(c.author_id),
                        "created_at": c.created_at.isoformat(),
                    }
                    for c in result.comments
                ],
                "created_at": result.created_at.isoformat(),
                "published_at": result.published_at.isoformat() if result.published_at else None,
            })
        except (DomainError, NotFoundError) as e:
            return handle_domain_error(e)


class PostPublishView(APIView):
    """
    POST /api/posts/<post_id>/publish/  → Publica un post
    """
    authentication_classes = [JWTAuth]
    permission_classes = [IsAuthenticated]

    @publish_post_schema
    def post(self, request, post_id):
        try:
            command = PublishPostCommand(
                post_id=post_id,
                requesting_author_id=request.user.id,
            )
            handler = get_publish_post_handler()
            handler.handle(command)
            return Response({"message": "Post publicado exitosamente."})
        except (DomainError, NotFoundError) as e:
            return handle_domain_error(e)


class PostArchiveView(APIView):
    """
    POST /api/posts/<post_id>/archive/  → Archiva un post
    """
    authentication_classes = [JWTAuth]
    permission_classes = [IsAuthenticated]

    @archive_post_schema
    def post(self, request, post_id):  # ← ya viene como UUID
        try:
            command = ArchivePostCommand(
                post_id=post_id,  # ← ya es UUID
                requesting_author_id=request.user.id,  # ← ya es UUID
            )
            handler = get_archive_post_handler()
            handler.handle(command)
            return Response({"message": "Post archivado."})
        except (DomainError, NotFoundError) as e:
            return handle_domain_error(e)


class CommentCreateView(APIView):
    """
    POST /api/posts/<post_id>/comments/  → Añade comentario
    """
    authentication_classes = [JWTAuth]
    permission_classes = [IsAuthenticated]

    @add_comment_schema
    def post(self, request, post_id):  # ← ya viene como UUID
        try:
            command = AddCommentCommand(
                post_id=post_id,  # ← ya es UUID
                body=request.data.get("body", ""),
                commenter_id=request.user.id,  # ← ya es UUID
            )
            handler = get_add_comment_handler()
            result = handler.handle(command)

            return Response(
                {
                    "id": str(result.id),
                    "body": result.body,
                    "created_at": result.created_at.isoformat(),
                },
                status=status.HTTP_201_CREATED,
            )
        except (DomainError, NotFoundError) as e:
            return handle_domain_error(e)


class AuthorPostsView(APIView):
    """
    GET /api/authors/<author_id>/posts/  → Posts de un autor
    """
    permission_classes = [AllowAny]

    def get(self, request, author_id):  # ← ya viene como UUID
        try:
            query = ListPostsByAuthorQuery(
                author_id=author_id,  # ← ya es UUID
                page=int(request.query_params.get("page", 1)),
                page_size=int(request.query_params.get("page_size", 10)),
            )
            handler = get_posts_by_author_handler()
            result = handler.handle(query)

            return Response({
                "items": [
                    {
                        "id": str(p.id),
                        "title": p.title,
                        "slug": p.slug,
                        "status": p.status,
                        "created_at": p.created_at.isoformat(),
                    }
                    for p in result.items
                ],
                "total": result.total,
                "page": result.page,
            })
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
