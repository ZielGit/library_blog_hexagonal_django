"""
QUERY: ListPosts
Lista posts con paginación, filtros por tag, autor y estado.
"""
from dataclasses import dataclass
from uuid import UUID

from src.domain.blog.repositories import PostReadRepository
from src.application.dtos import PostListDTO, PostSummaryDTO


def _to_summary_dto(post) -> PostSummaryDTO:
    return PostSummaryDTO(
        id=post.id,
        title=post.title.value,
        slug=post.slug.value,
        excerpt=post.content.excerpt(),
        status=post.status.value,
        author_id=post.author_id,
        category_id=post.category_id,
        tags=post.tags,
        created_at=post.created_at,
        published_at=post.published_at,
    )


# ── Listar publicados ────────────────────────────────────────
@dataclass(frozen=True)
class ListPublishedPostsQuery:
    page: int = 1
    page_size: int = 10
    tag: str | None = None


class ListPublishedPostsQueryHandler:

    def __init__(self, read_repo: PostReadRepository):
        self._repo = read_repo

    def handle(self, query: ListPublishedPostsQuery) -> PostListDTO:
        posts, total = self._repo.find_published(
            page=query.page,
            page_size=query.page_size,
            tag=query.tag,
        )
        return PostListDTO(
            items=[_to_summary_dto(p) for p in posts],
            total=total,
            page=query.page,
            page_size=query.page_size,
        )


# ── Posts por autor ──────────────────────────────────────────
@dataclass(frozen=True)
class ListPostsByAuthorQuery:
    author_id: UUID
    page: int = 1
    page_size: int = 10


class ListPostsByAuthorQueryHandler:

    def __init__(self, read_repo: PostReadRepository):
        self._repo = read_repo

    def handle(self, query: ListPostsByAuthorQuery) -> PostListDTO:
        posts, total = self._repo.find_by_author(
            author_id=query.author_id,
            page=query.page,
            page_size=query.page_size,
        )
        return PostListDTO(
            items=[_to_summary_dto(p) for p in posts],
            total=total,
            page=query.page,
            page_size=query.page_size,
        )
