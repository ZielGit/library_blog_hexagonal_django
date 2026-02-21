"""
DTOs (Data Transfer Objects) de la capa Application.

Los DTOs son objetos simples que transportan datos entre capas.
NO tienen lógica de negocio. Son la "moneda de cambio" entre
la capa de aplicación y la capa de interfaces (API, Admin).
"""
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


# ─────────────────────────────────────────────────────────────
# BLOG DTOs
# ─────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class PostCreatedDTO:
    """Resultado de CreatePostCommand."""
    id: UUID
    slug: str
    title: str


@dataclass(frozen=True)
class CommentDTO:
    id: UUID
    body: str
    author_id: UUID
    created_at: datetime


@dataclass(frozen=True)
class PostDetailDTO:
    """DTO completo para mostrar un post con todos sus detalles."""
    id: UUID
    title: str
    slug: str
    content: str
    excerpt: str
    status: str
    author_id: UUID
    tags: list[str]
    comments: list[CommentDTO]
    created_at: datetime
    published_at: datetime | None
    word_count: int


@dataclass(frozen=True)
class PostSummaryDTO:
    """DTO reducido para listar posts (sin content completo ni comments)."""
    id: UUID
    title: str
    slug: str
    excerpt: str
    status: str
    author_id: UUID
    tags: list[str]
    created_at: datetime
    published_at: datetime | None


@dataclass(frozen=True)
class PostListDTO:
    """Resultado paginado de ListPostsQuery."""
    items: list[PostSummaryDTO]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        if self.page_size == 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        return self.page > 1


# ─────────────────────────────────────────────────────────────
# LIBRARY DTOs
# ─────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class BookCreatedDTO:
    id: UUID
    isbn: str
    title: str


@dataclass(frozen=True)
class BookDetailDTO:
    id: UUID
    isbn: str
    title: str
    author_name: str
    description: str
    available_copies: int
    published_year: int
