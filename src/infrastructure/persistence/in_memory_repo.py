"""
REPOSITORIOS EN MEMORIA — para tests y desarrollo local.

Implementan los mismos Puertos que DjangoPostRepository,
pero sin base de datos. Permiten tests ultrarrápidos sin setup.

Regla LSP (Liskov Substitution Principle):
  InMemoryPostRepository y DjangoPostRepository son
  intercambiables — ambos respetan exactamente el mismo contrato.
"""
from uuid import UUID

from src.domain.blog.aggregates import PostAggregate
from src.domain.blog.entities import PostStatus
from src.domain.blog.repositories import PostRepository, PostReadRepository


class InMemoryPostRepository(PostRepository, PostReadRepository):
    """
    Implementa AMBAS interfaces (write + read) con un dict en memoria.
    Perfecto para unit tests — cero setup, cero teardown.

    Uso en tests:
        repo = InMemoryPostRepository()
        handler = CreatePostCommandHandler(repo, bus)
        handler.handle(command)
        saved = repo.get_by_id(result.id)
        assert saved is not None
    """

    def __init__(self):
        self._store: dict[UUID, PostAggregate] = {}

    # ── PostRepository (write) ───────────────────────────────
    def save(self, post: PostAggregate) -> None:
        self._store[post.id] = post

    def get_by_id(self, post_id: UUID) -> PostAggregate | None:
        return self._store.get(post_id)

    def delete(self, post_id: UUID) -> None:
        self._store.pop(post_id, None)

    # ── PostReadRepository (read) ────────────────────────────
    def find_by_slug(self, slug: str) -> PostAggregate | None:
        return next(
            (p for p in self._store.values() if p.slug.value == slug),
            None
        )

    def find_published(
        self,
        page: int = 1,
        page_size: int = 10,
        tag: str | None = None,
    ) -> tuple[list[PostAggregate], int]:
        published = [
            p for p in self._store.values()
            if p.status == PostStatus.PUBLISHED
        ]
        if tag:
            published = [p for p in published if tag.lower() in p.tags]

        published.sort(key=lambda p: p.published_at or p.created_at, reverse=True)

        start = (page - 1) * page_size
        end = start + page_size
        return published[start:end], len(published)

    def find_by_author(
        self,
        author_id: UUID,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[PostAggregate], int]:
        author_posts = [
            p for p in self._store.values()
            if p.author_id == author_id
        ]
        author_posts.sort(key=lambda p: p.created_at, reverse=True)
        start = (page - 1) * page_size
        end = start + page_size
        return author_posts[start:end], len(author_posts)

    def slug_exists(self, slug: str) -> bool:
        return any(p.slug.value == slug for p in self._store.values())

    # ── Helpers de test ──────────────────────────────────────
    def count(self) -> int:
        return len(self._store)

    def all(self) -> list[PostAggregate]:
        return list(self._store.values())

    def clear(self) -> None:
        self._store.clear()


# ══════════════════════════════════════════════════════════════
# USER REPOSITORY
# ══════════════════════════════════════════════════════════════

from src.domain.users.entities import User
from src.domain.users.repositories import UserRepository


class InMemoryUserRepository(UserRepository):
    """
    Repositorio en memoria para User.
    Ideal para tests sin base de datos.
    """

    def __init__(self):
        self._store: dict[UUID, User] = {}

    def save(self, user: User) -> None:
        self._store[user.id] = user

    def get_by_id(self, user_id: UUID) -> User | None:
        return self._store.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        return next(
            (u for u in self._store.values() if u.email == email),
            None
        )

    def get_by_username(self, username: str) -> User | None:
        return next(
            (u for u in self._store.values() if u.username == username),
            None
        )

    def email_exists(self, email: str) -> bool:
        return any(u.email == email for u in self._store.values())

    def username_exists(self, username: str) -> bool:
        return any(u.username == username for u in self._store.values())
