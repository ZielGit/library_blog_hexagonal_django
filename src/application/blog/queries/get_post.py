"""
QUERY: GetPost
Obtiene el detalle completo de un post por slug o por ID.
"""
from dataclasses import dataclass
from uuid import UUID

from src.domain.blog.repositories import PostReadRepository
from src.domain.blog.exceptions import PostNotFoundError
from src.application.dtos import PostDetailDTO, CommentDTO


def _to_detail_dto(post) -> PostDetailDTO:
    return PostDetailDTO(
        id=post.id,
        title=post.title.value,
        slug=post.slug.value,
        content=post.content.value,
        excerpt=post.content.excerpt(),
        status=post.status.value,
        author_id=post.author_id,
        category_id=post.category_id,
        tags=post.tags,
        comments=[
            CommentDTO(
                id=c.id,
                body=c.body,
                author_id=c.author_id,
                created_at=c.created_at,
            )
            for c in post.comments
        ],
        created_at=post.created_at,
        published_at=post.published_at,
        word_count=post.content.word_count,
    )


# ── Por Slug ─────────────────────────────────────────────────
@dataclass(frozen=True)
class GetPostBySlugQuery:
    slug: str


class GetPostBySlugQueryHandler:

    def __init__(self, read_repo: PostReadRepository):
        self._repo = read_repo

    def handle(self, query: GetPostBySlugQuery) -> PostDetailDTO:
        post = self._repo.find_by_slug(query.slug)
        if post is None:
            raise PostNotFoundError(query.slug)
        return _to_detail_dto(post)


# ── Por ID ───────────────────────────────────────────────────
@dataclass(frozen=True)
class GetPostByIdQuery:
    post_id: UUID


class GetPostByIdQueryHandler:

    def __init__(self, read_repo: PostReadRepository):
        self._repo = read_repo

    def handle(self, query: GetPostByIdQuery) -> PostDetailDTO:
        post = self._repo.get_by_id(query.post_id)
        if post is None:
            raise PostNotFoundError(str(query.post_id))
        return _to_detail_dto(post)
