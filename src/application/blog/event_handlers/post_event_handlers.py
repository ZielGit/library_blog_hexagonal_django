"""
EVENT HANDLERS del módulo Blog.

Reaccionan a Domain Events emitidos por el PostAggregate.
Son parte de la capa Application — coordinan efectos secundarios
sin contaminar el dominio con esas responsabilidades.

Principio: el dominio solo ANUNCIA lo que ocurrió.
Los event handlers DECIDEN qué hacer al respecto.

Ejemplos de reacciones:
  PostPublished  → enviar email al autor, invalidar cache, notificar RSS
  CommentAdded   → notificar al autor del post, moderar contenido
  PostArchived   → limpiar cache, registrar en auditoría
"""
import logging
from src.domain.blog.events import PostPublished, CommentAdded, PostArchived, PostCreated

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# POST PUBLISHED HANDLER
# ─────────────────────────────────────────────────────────────
class OnPostPublished:
    """
    Reacciona cuando un post es publicado.
    Responsabilidades:
      - Notificar al autor por email
      - Invalidar caché de la lista de posts
      - Disparar indexación en buscador (ej: Elasticsearch)
    """

    def __init__(self, email_service=None, cache_service=None):
        self._email_service = email_service
        self._cache_service = cache_service

    def handle(self, event: PostPublished) -> None:
        logger.info(
            f"[OnPostPublished] post_id={event.post_id}, slug={event.slug}"
        )

        # 1. Invalidar caché de listado de posts
        if self._cache_service:
            self._cache_service.invalidate("posts:published:*")
            self._cache_service.invalidate(f"posts:slug:{event.slug}")

        # 2. Notificación al autor (stub — implementar con SendGrid/SES)
        if self._email_service:
            self._email_service.send_post_published_notification(
                post_id=event.post_id,
                slug=event.slug,
            )

        logger.info(f"[OnPostPublished] Efectos secundarios completados para {event.post_id}")


# ─────────────────────────────────────────────────────────────
# COMMENT ADDED HANDLER
# ─────────────────────────────────────────────────────────────
class OnCommentAdded:
    """
    Reacciona cuando se añade un comentario.
    Responsabilidades:
      - Notificar al autor del post
      - Moderar el comentario (anti-spam)
    """

    def __init__(self, notification_service=None, moderation_service=None):
        self._notifications = notification_service
        self._moderation = moderation_service

    def handle(self, event: CommentAdded) -> None:
        logger.info(
            f"[OnCommentAdded] post_id={event.post_id}, "
            f"comment_id={event.comment_id}"
        )

        # 1. Moderación anti-spam (stub)
        if self._moderation:
            self._moderation.check_comment(event.comment_id)

        # 2. Notificar al autor del post (stub)
        if self._notifications:
            self._notifications.notify_new_comment(
                post_id=event.post_id,
                comment_id=event.comment_id,
            )


# ─────────────────────────────────────────────────────────────
# POST ARCHIVED HANDLER
# ─────────────────────────────────────────────────────────────
class OnPostArchived:
    """
    Reacciona cuando un post es archivado.
    Responsabilidades:
      - Limpiar caché
      - Registrar en log de auditoría
    """

    def __init__(self, cache_service=None, audit_log=None):
        self._cache_service = cache_service
        self._audit_log = audit_log

    def handle(self, event: PostArchived) -> None:
        logger.info(f"[OnPostArchived] post_id={event.post_id}")

        if self._cache_service:
            self._cache_service.invalidate(f"posts:id:{event.post_id}")
            self._cache_service.invalidate("posts:published:*")

        if self._audit_log:
            self._audit_log.record(
                action="post_archived",
                entity_id=str(event.post_id),
                occurred_at=event.occurred_at,
            )


# ─────────────────────────────────────────────────────────────
# POST CREATED HANDLER
# ─────────────────────────────────────────────────────────────
class OnPostCreated:
    """
    Reacciona cuando un post es creado (en borrador).
    Responsabilidades:
      - Registrar en analytics
    """

    def __init__(self, analytics_service=None):
        self._analytics = analytics_service

    def handle(self, event: PostCreated) -> None:
        logger.info(
            f"[OnPostCreated] post_id={event.post_id}, author={event.author_id}"
        )
        if self._analytics:
            self._analytics.track_post_created(
                post_id=event.post_id,
                author_id=event.author_id,
            )
