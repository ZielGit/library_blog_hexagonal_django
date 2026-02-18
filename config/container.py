"""
COMPOSITION ROOT — ensambla todas las dependencias del proyecto.

Es el único archivo que conoce:
  - Adaptadores concretos (Django ORM, Redis, Celery, JWT)
  - Qué implementación usar según el entorno

Regla: ningún otro módulo importa adaptadores directamente.
Solo este archivo los conoce.
"""
import os

DJANGO_ENV = os.getenv("DJANGO_ENV", "development")


# ─────────────────────────────────────────────────────────────
# INFRAESTRUCTURA BASE
# ─────────────────────────────────────────────────────────────
def get_event_bus():
    if DJANGO_ENV == "test":
        from src.infrastructure.messaging.event_bus_adapters import InMemoryEventBus
        return InMemoryEventBus()
    elif DJANGO_ENV == "production":
        from src.infrastructure.messaging.celery_event_bus import CeleryEventBus
        return CeleryEventBus()
    else:
        from src.infrastructure.messaging.event_bus_adapters import LoggingEventBus
        return LoggingEventBus()


def get_post_repo():
    if DJANGO_ENV == "test":
        from src.infrastructure.persistence.in_memory_repo import InMemoryPostRepository
        return InMemoryPostRepository()
    from src.infrastructure.persistence.django_blog_repo import DjangoPostRepository
    return DjangoPostRepository()


def get_cache_service():
    if DJANGO_ENV == "test":
        from src.infrastructure.cache.redis_cache import InMemoryCacheService
        return InMemoryCacheService()
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    from src.infrastructure.cache.redis_cache import RedisCacheService
    return RedisCacheService(redis_url=redis_url)


def get_password_hasher():
    """Usa bcrypt en producción, Django hasher en dev/test."""
    if DJANGO_ENV == "production":
        from src.infrastructure.auth.jwt_service import BcryptPasswordHasher
        return BcryptPasswordHasher()
    from src.infrastructure.auth.jwt_service import DjangoPasswordHasher
    return DjangoPasswordHasher()


def get_token_service():
    from src.infrastructure.auth.jwt_service import JWTTokenService
    return JWTTokenService(
        secret_key=os.getenv("JWT_SECRET_KEY", "dev-insecure-jwt-secret"),
        access_expire_minutes=int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES", "30")),
        refresh_expire_days=int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7")),
    )


def get_user_repo():
    if DJANGO_ENV == "test":
        from src.infrastructure.persistence.in_memory_repo import InMemoryUserRepository
        return InMemoryUserRepository()
    from src.infrastructure.persistence.django_user_repo import DjangoUserRepository
    return DjangoUserRepository()


# ─────────────────────────────────────────────────────────────
# BLOG — COMMAND HANDLERS
# ─────────────────────────────────────────────────────────────
def get_create_post_handler():
    from src.application.blog.commands.create_post import CreatePostCommandHandler
    return CreatePostCommandHandler(repo=get_post_repo(), event_bus=get_event_bus())


def get_publish_post_handler():
    from src.application.blog.commands.publish_post import PublishPostCommandHandler
    return PublishPostCommandHandler(repo=get_post_repo(), event_bus=get_event_bus())


def get_add_comment_handler():
    from src.application.blog.commands.add_comment import AddCommentCommandHandler
    return AddCommentCommandHandler(repo=get_post_repo(), event_bus=get_event_bus())


def get_archive_post_handler():
    from src.application.blog.commands.archive_post import ArchivePostCommandHandler
    return ArchivePostCommandHandler(repo=get_post_repo(), event_bus=get_event_bus())


# ─────────────────────────────────────────────────────────────
# BLOG — QUERY HANDLERS
# ─────────────────────────────────────────────────────────────
def get_post_by_slug_handler():
    from src.application.blog.queries.get_post import GetPostBySlugQueryHandler
    return GetPostBySlugQueryHandler(read_repo=get_post_repo())


def get_post_by_id_handler():
    from src.application.blog.queries.get_post import GetPostByIdQueryHandler
    return GetPostByIdQueryHandler(read_repo=get_post_repo())


def get_list_posts_handler():
    from src.application.blog.queries.list_posts import ListPublishedPostsQueryHandler
    return ListPublishedPostsQueryHandler(read_repo=get_post_repo())


def get_posts_by_author_handler():
    from src.application.blog.queries.list_posts import ListPostsByAuthorQueryHandler
    return ListPostsByAuthorQueryHandler(read_repo=get_post_repo())


# ─────────────────────────────────────────────────────────────
# USERS — COMMAND HANDLERS
# ─────────────────────────────────────────────────────────────
def get_register_handler():
    from src.application.users.commands.auth_commands import RegisterUserCommandHandler
    return RegisterUserCommandHandler(
        user_repo=get_user_repo(),
        password_hasher=get_password_hasher(),
    )


def get_login_handler():
    from src.application.users.commands.auth_commands import LoginCommandHandler
    return LoginCommandHandler(
        user_repo=get_user_repo(),
        password_hasher=get_password_hasher(),
        token_service=get_token_service(),
    )


def get_refresh_token_handler():
    from src.application.users.commands.auth_commands import RefreshTokenCommandHandler
    return RefreshTokenCommandHandler(
        user_repo=get_user_repo(),
        token_service=get_token_service(),
    )
