"""
PUERTOS (interfaces) del repositorio Blog.

Los puertos son contratos abstractos — el dominio declara
QUÉ necesita, sin saber CÓMO se implementa.

Analogía del enchufe:
  - Puerto  = la forma del enchufe en la pared
  - Adaptador = el dispositivo que se conecta (Django ORM, MongoDB, etc.)

ISP (Interface Segregation Principle):
  Separamos lectura y escritura en dos interfaces distintas.
  El QueryHandler solo necesita leer → depende de PostReadRepository.
  El CommandHandler solo necesita escribir → depende de PostRepository.
"""
from abc import ABC, abstractmethod
from uuid import UUID

from .aggregates import PostAggregate


# ─────────────────────────────────────────────────────────────
# WRITE REPOSITORY (Command side)
# ─────────────────────────────────────────────────────────────
class PostRepository(ABC):
    """
    Puerto de escritura.
    Usado por CommandHandlers para persistir cambios de estado.
    """

    @abstractmethod
    def save(self, post: PostAggregate) -> None:
        """Crea o actualiza el post (upsert)."""
        ...

    @abstractmethod
    def get_by_id(self, post_id: UUID) -> PostAggregate | None:
        """Recupera un post por su ID (para aplicar comandos)."""
        ...

    @abstractmethod
    def delete(self, post_id: UUID) -> None:
        """Elimina el post."""
        ...


# ─────────────────────────────────────────────────────────────
# READ REPOSITORY (Query side — CQRS)
# ─────────────────────────────────────────────────────────────
class PostReadRepository(ABC):
    """
    Puerto de lectura.
    Usado por QueryHandlers — puede tener un modelo de datos
    distinto y optimizado para consultas (ej: vistas desnormalizadas).
    """

    @abstractmethod
    def find_by_slug(self, slug: str) -> PostAggregate | None:
        ...

    @abstractmethod
    def find_published(
        self,
        page: int = 1,
        page_size: int = 10,
        tag: str | None = None,
    ) -> tuple[list[PostAggregate], int]:
        """Retorna (posts, total_count)."""
        ...

    @abstractmethod
    def find_by_author(
        self,
        author_id: UUID,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[PostAggregate], int]:
        ...

    @abstractmethod
    def slug_exists(self, slug: str) -> bool:
        ...
