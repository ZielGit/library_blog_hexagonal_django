"""
ENTIDADES del módulo Blog: Post, Category, Comment.

En esta arquitectura separamos:
  - entities.py  → las entidades "puras" (Post, Category, Comment)
  - aggregates.py → el PostAggregate que los orquesta y protege

¿Por qué separarlos?
  Las entidades definen QUÉS son los objetos.
  El aggregate define CÓMO interactúan con consistencia garantizada.

Regla: estas entidades NO deben usarse directamente desde fuera
del dominio. Siempre pasa por el PostAggregate.
"""
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from src.domain.shared.base import Entity
from src.domain.blog.value_objects import Title, Slug, Content
from src.domain.blog.exceptions import (
    ValidationError,
    CommentNotAllowedError,
    UnauthorizedPostActionError,
)


# ─────────────────────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────────────────────
class PostStatus(Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


# ─────────────────────────────────────────────────────────────
# CATEGORY ENTITY
# ─────────────────────────────────────────────────────────────
class Category(Entity):
    """
    Categoría a la que puede pertenecer un Post.
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        category_id: UUID | None = None,
    ):
        super().__init__(category_id)
        if not name or not name.strip():
            raise ValidationError("El nombre de la categoría no puede estar vacío.")
        if len(name) > 100:
            raise ValidationError("El nombre de la categoría no puede exceder 100 chars.")

        self._name = name.strip()
        self._slug = Slug(value=Title(value=name).to_slug().value)
        self._description = description
        self._created_at = datetime.now(timezone.utc)

    @property
    def name(self) -> str:
        return self._name

    @property
    def slug(self) -> Slug:
        return self._slug

    @property
    def description(self) -> str:
        return self._description

    def update(self, name: str, description: str = "") -> None:
        if not name or not name.strip():
            raise ValidationError("El nombre de la categoría no puede estar vacío.")
        self._name = name.strip()
        self._slug = Slug(value=Title(value=name).to_slug().value)
        self._description = description

    def __repr__(self) -> str:
        return f"Category(id={self._id}, name={self._name!r})"


# ─────────────────────────────────────────────────────────────
# COMMENT ENTITY
# ─────────────────────────────────────────────────────────────
class Comment(Entity):
    """
    Entidad Comment. Solo existe dentro de un PostAggregate.

    Importante: No tiene repositorio propio. Se persiste
    y se accede SIEMPRE a través del PostAggregate.
    """
    MAX_LENGTH = 1000

    def __init__(
        self,
        body: str,
        author_id: UUID,
        comment_id: UUID | None = None,
    ):
        super().__init__(comment_id)
        self._validate_body(body)
        self._body = body.strip()
        self._author_id = author_id
        self._created_at = datetime.now(timezone.utc)
        self._is_deleted = False

    @staticmethod
    def _validate_body(body: str) -> None:
        if not body or not body.strip():
            raise ValidationError("El cuerpo del comentario no puede estar vacío.")
        if len(body) > Comment.MAX_LENGTH:
            raise ValidationError(
                f"El comentario no puede exceder {Comment.MAX_LENGTH} caracteres "
                f"(actual: {len(body)})."
            )

    @property
    def body(self) -> str:
        return self._body

    @property
    def author_id(self) -> UUID:
        return self._author_id

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def is_deleted(self) -> bool:
        return self._is_deleted

    def soft_delete(self, requesting_user_id: UUID) -> None:
        """Marca el comentario como eliminado (soft delete)."""
        if requesting_user_id != self._author_id:
            raise UnauthorizedPostActionError("eliminar comentario")
        self._is_deleted = True
        self._body = "[comentario eliminado]"

    def __repr__(self) -> str:
        return f"Comment(id={self._id}, author={self._author_id})"


# ─────────────────────────────────────────────────────────────
# POST ENTITY
# ─────────────────────────────────────────────────────────────
class Post(Entity):
    """
    Entidad Post — el núcleo del módulo Blog.

    Contiene el estado y las propiedades del post, pero
    la orquestación de reglas de negocio complejas
    (publicar, archivar, coordinar comentarios) vive en PostAggregate.
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
        self._title = title
        self._slug = title.to_slug()
        self._content = content
        self._author_id = author_id
        self._category_id = category_id
        self._status = PostStatus.DRAFT
        self._tags: list[str] = []
        self._created_at = datetime.now(timezone.utc)
        self._updated_at = datetime.now(timezone.utc)
        self._published_at: datetime | None = None

    # ── Propiedades ──────────────────────────────────────────
    @property
    def title(self) -> Title:
        return self._title

    @property
    def slug(self) -> Slug:
        return self._slug

    @property
    def content(self) -> Content:
        return self._content

    @property
    def author_id(self) -> UUID:
        return self._author_id

    @property
    def category_id(self) -> UUID | None:
        return self._category_id

    @property
    def status(self) -> PostStatus:
        return self._status

    @property
    def tags(self) -> list[str]:
        return list(self._tags)

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def published_at(self) -> datetime | None:
        return self._published_at

    @property
    def is_published(self) -> bool:
        return self._status == PostStatus.PUBLISHED

    @property
    def is_draft(self) -> bool:
        return self._status == PostStatus.DRAFT

    @property
    def is_archived(self) -> bool:
        return self._status == PostStatus.ARCHIVED

    # ── Mutaciones (solo el Aggregate las llama directamente) ─
    def _set_status(self, status: PostStatus) -> None:
        self._status = status
        self._updated_at = datetime.now(timezone.utc)

    def _set_published_at(self, dt: datetime) -> None:
        self._published_at = dt

    def _update_content(self, title: Title, content: Content) -> None:
        self._title = title
        self._slug = title.to_slug()
        self._content = content
        self._updated_at = datetime.now(timezone.utc)

    def _add_tag(self, tag: str) -> None:
        normalized = tag.lower().strip()
        if normalized and normalized not in self._tags:
            self._tags.append(normalized)

    def _set_category(self, category_id: UUID | None) -> None:
        self._category_id = category_id

    def __repr__(self) -> str:
        return f"Post(id={self._id}, slug={self._slug.value!r}, status={self._status.value})"
