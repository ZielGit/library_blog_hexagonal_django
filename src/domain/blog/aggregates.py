"""
AGREGADOS del módulo Blog.

El PostAggregate es la RAÍZ DEL AGREGADO (Aggregate Root).
Controla el acceso a Post + Comments + Categories relacionadas,
garantizando que todas las invariantes de negocio se cumplan.

Regla de oro: NUNCA accedas a un Comment directamente desde fuera.
Siempre pasa por PostAggregate.aggregate.add_comment(...)

¿Cuándo usar un Aggregate?
  Cuando tienes un grupo de entidades que deben cambiar juntas
  para mantener consistencia. Si Post.publish() requiere verificar
  sus Comments o su Category, todo debe estar en el mismo aggregate.
"""
from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.domain.shared.base import AggregateRoot
from src.domain.blog.entities import Post, Comment, PostStatus, Category
from src.domain.blog.value_objects import Title, Content
from src.domain.blog.events import (
    PostCreated, PostPublished, PostArchived,
    CommentAdded, PostUpdated,
)
from src.domain.blog.exceptions import (
    PostAlreadyPublishedError,
    PostArchivedError,
    InvalidPostContentError,
    UnauthorizedPostActionError,
    CommentNotAllowedError,
    ValidationError,
)


class PostAggregate(AggregateRoot):
    """
    Agregado raíz que coordina Post + Comments.

    Invariantes garantizadas:
      ① No se puede publicar un post con contenido < 100 chars
      ② No se puede comentar en un post archivado
      ③ Solo el autor puede archivar/actualizar su post
      ④ Un post ya publicado no puede volver a publicarse
      ⑤ Un post archivado no puede publicarse ni editarse
    """

    def __init__(
        self,
        title: Title,
        content: Content,
        author_id: UUID,
        category_id: UUID | None = None,
        post_id: UUID | None = None,
    ):
        super().__init__(post_id)

        # La entidad Post vive dentro del aggregate
        self._post = Post(
            title=title,
            content=content,
            author_id=author_id,
            category_id=category_id,
            post_id=self._id,
        )
        self._comments: list[Comment] = []

        # Emitir evento de creación
        self._record_event(PostCreated(
            post_id=self._id,
            author_id=author_id,
            title=title.value,
        ))

    # ── Propiedades (delegamos a Post) ───────────────────────
    @property
    def post(self) -> Post:
        """Acceso de solo lectura a la entidad Post interna."""
        return self._post

    @property
    def id(self) -> UUID:
        return self._post.id

    @property
    def title(self) -> Title:
        return self._post.title

    @property
    def slug(self):
        return self._post.slug

    @property
    def content(self) -> Content:
        return self._post.content

    @property
    def author_id(self) -> UUID:
        return self._post.author_id

    @property
    def status(self) -> PostStatus:
        return self._post.status

    @property
    def tags(self) -> list[str]:
        return self._post.tags

    @property
    def category_id(self) -> UUID | None:
        return self._post.category_id

    @property
    def created_at(self) -> datetime:
        return self._post.created_at

    @property
    def published_at(self) -> datetime | None:
        return self._post.published_at

    @property
    def comments(self) -> list[Comment]:
        """Copia defensiva — no exponemos la lista interna."""
        return [c for c in self._comments if not c.is_deleted]

    @property
    def all_comments(self) -> list[Comment]:
        """Incluye comentarios eliminados (para auditoría)."""
        return list(self._comments)

    # ── Comandos de Dominio ──────────────────────────────────

    def publish(self) -> None:
        """
        Publica el post.
        Invariantes:
          - El post debe estar en DRAFT
          - El contenido debe tener al menos 100 chars
        """
        if self._post.is_published:
            raise PostAlreadyPublishedError()

        if self._post.is_archived:
            raise PostArchivedError("publicar")

        if not self._post.content.is_publishable:
            raise InvalidPostContentError(
                current_length=len(self._post.content.value),
                min_length=Content.MIN_LENGTH_TO_PUBLISH,
            )

        self._post._set_status(PostStatus.PUBLISHED)
        self._post._set_published_at(datetime.now(timezone.utc))

        self._record_event(PostPublished(
            post_id=self._id,
            slug=self._post.slug.value,
        ))

    def archive(self, requesting_author_id: UUID) -> None:
        """
        Archiva el post. Solo el autor puede hacerlo.
        """
        if requesting_author_id != self._post.author_id:
            raise UnauthorizedPostActionError("archivar")

        if self._post.is_archived:
            raise PostArchivedError("archivar nuevamente")

        self._post._set_status(PostStatus.ARCHIVED)
        self._record_event(PostArchived(post_id=self._id))

    def update(
        self,
        new_title: Title,
        new_content: Content,
        requesting_author_id: UUID,
    ) -> None:
        """
        Actualiza título y contenido. Solo el autor puede editar.
        Los posts archivados no pueden editarse.
        """
        if requesting_author_id != self._post.author_id:
            raise UnauthorizedPostActionError("editar")

        if self._post.is_archived:
            raise PostArchivedError("editar")

        self._post._update_content(new_title, new_content)
        self._record_event(PostUpdated(
            post_id=self._id,
            new_title=new_title.value,
        ))

    def add_comment(self, body: str, commenter_id: UUID) -> Comment:
        """
        Añade un comentario al post.
        Invariante: no se puede comentar en posts archivados.
        """
        if self._post.is_archived:
            raise CommentNotAllowedError("el post está archivado")

        comment = Comment(body=body, author_id=commenter_id)
        self._comments.append(comment)

        self._record_event(CommentAdded(
            post_id=self._id,
            comment_id=comment.id,
            author_id=commenter_id,
        ))
        return comment

    def remove_comment(self, comment_id: UUID, requesting_user_id: UUID) -> None:
        """Elimina (soft delete) un comentario."""
        comment = next(
            (c for c in self._comments if c.id == comment_id),
            None
        )
        if comment is None:
            raise ValidationError(f"Comentario {comment_id} no encontrado en este post.")

        comment.soft_delete(requesting_user_id)

    def add_tags(self, tags: list[str]) -> None:
        """Agrega tags únicos. Normaliza a minúsculas."""
        for tag in tags:
            self._post._add_tag(tag)

    def set_category(self, category_id: UUID | None) -> None:
        """Asigna o desasigna una categoría al post."""
        self._post._set_category(category_id)

    # ── Factory Method (reconstituir desde persistencia) ─────
    @classmethod
    def reconstitute(
        cls,
        post_id: UUID,
        title: Title,
        content: Content,
        author_id: UUID,
        status: PostStatus,
        created_at: datetime,
        published_at: datetime | None,
        tags: list[str],
        category_id: UUID | None,
        comments: list[Comment],
    ) -> "PostAggregate":
        """
        Reconstruye el aggregate desde datos persistidos.
        NO emite eventos (ya ocurrieron en el pasado).
        """
        agg = cls.__new__(cls)
        AggregateRoot.__init__(agg, post_id)

        post = Post.__new__(Post)
        from src.domain.shared.base import Entity
        Entity.__init__(post, post_id)
        post._title = title
        post._slug = title.to_slug()
        post._content = content
        post._author_id = author_id
        post._category_id = category_id
        post._status = status
        post._tags = tags
        post._created_at = created_at
        post._updated_at = created_at
        post._published_at = published_at

        agg._post = post
        agg._comments = comments
        agg._domain_events = []
        return agg

    def __repr__(self) -> str:
        return (
            f"PostAggregate("
            f"id={self._id}, "
            f"slug={self._post.slug.value!r}, "
            f"status={self._post.status.value})"
        )
