"""
UNIT TESTS - Blog Application

Tests unitarios de la capa Application del módulo Blog:
- Command Handlers (CreatePost, PublishPost, ArchivePost, AddComment)
- Query Handlers (GetPostBySlug, GetPostById, ListPublishedPosts, ListPostsByAuthor)
- Event Handlers (OnPostPublished, OnCommentAdded, OnPostArchived, OnPostCreated)

No tocan la base de datos; se usan mocks de repositorios y event bus.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock
from uuid import uuid4

from src.domain.blog.aggregates import PostAggregate
from src.domain.blog.entities import PostStatus
from src.domain.blog.value_objects import Title, Content
from src.domain.blog.exceptions import (
    PostNotFoundError,
    PostAlreadyPublishedError,
    UnauthorizedPostActionError,
    InvalidPostContentError,
)
from src.domain.blog.events import PostPublished, CommentAdded, PostArchived, PostCreated

from src.application.blog.commands.create_post import (
    CreatePostCommand,
    CreatePostCommandHandler,
)
from src.application.blog.commands.publish_post import (
    PublishPostCommand,
    PublishPostCommandHandler,
)
from src.application.blog.commands.archive_post import (
    ArchivePostCommand,
    ArchivePostCommandHandler,
)
from src.application.blog.commands.add_comment import (
    AddCommentCommand,
    AddCommentCommandHandler,
)
from src.application.blog.queries.get_post import (
    GetPostBySlugQuery,
    GetPostBySlugQueryHandler,
    GetPostByIdQuery,
    GetPostByIdQueryHandler,
)
from src.application.blog.queries.list_posts import (
    ListPublishedPostsQuery,
    ListPublishedPostsQueryHandler,
    ListPostsByAuthorQuery,
    ListPostsByAuthorQueryHandler,
)
from src.application.blog.event_handlers.post_event_handlers import (
    OnPostPublished,
    OnCommentAdded,
    OnPostArchived,
    OnPostCreated,
)
from src.application.dtos import (
    PostCreatedDTO,
    PostDetailDTO,
    PostSummaryDTO,
    PostListDTO,
    CommentDTO,
)


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def _long_content(min_len: int = 100) -> str:
    return "Contenido válido con más de cien caracteres para poder publicar. " * 2


def _make_draft_post(author_id=None):
    author_id = author_id or uuid4()
    return PostAggregate(
        title=Title("Post de prueba"),
        content=Content(_long_content()),
        author_id=author_id,
    )


def _make_published_post(author_id=None):
    post = _make_draft_post(author_id=author_id)
    post.publish()
    return post


# ─────────────────────────────────────────────────────────────
# CREATE POST
# ─────────────────────────────────────────────────────────────
class TestCreatePostCommandHandler:
    """Tests del handler CreatePost."""

    def test_handle_creates_post_and_returns_dto(self):
        """Crear post persiste, publica eventos y retorna PostCreatedDTO."""
        repo = Mock()
        event_bus = Mock()
        handler = CreatePostCommandHandler(repo=repo, event_bus=event_bus)
        author_id = uuid4()

        cmd = CreatePostCommand(
            title="Mi nuevo post",
            content=_long_content(),
            author_id=author_id,
            tags=["django", "python"],
        )
        result = handler.handle(cmd)

        assert isinstance(result, PostCreatedDTO)
        # Title value object normaliza a title case
        assert result.title == "Mi Nuevo Post"
        assert result.slug == "mi-nuevo-post"
        assert result.id is not None

        repo.save.assert_called_once()
        saved_post = repo.save.call_args[0][0]
        assert saved_post.title.value == "Mi Nuevo Post"
        assert saved_post.status == PostStatus.DRAFT
        assert saved_post.tags == ["django", "python"]

        event_bus.publish_many.assert_called_once()
        events = event_bus.publish_many.call_args[0][0]
        assert len(events) >= 1

    def test_handle_with_category_id(self):
        """CreatePost acepta category_id opcional."""
        repo = Mock()
        event_bus = Mock()
        handler = CreatePostCommandHandler(repo=repo, event_bus=event_bus)
        author_id = uuid4()
        category_id = uuid4()

        cmd = CreatePostCommand(
            title="Post con categoría",
            content=_long_content(),
            author_id=author_id,
            category_id=category_id,
        )
        result = handler.handle(cmd)

        saved_post = repo.save.call_args[0][0]
        assert saved_post.category_id == category_id
        assert result.id is not None


# ─────────────────────────────────────────────────────────────
# PUBLISH POST
# ─────────────────────────────────────────────────────────────
class TestPublishPostCommandHandler:
    """Tests del handler PublishPost."""

    def test_handle_post_not_found_raises(self):
        """Si el post no existe se lanza PostNotFoundError."""
        repo = Mock()
        repo.get_by_id.return_value = None
        event_bus = Mock()
        handler = PublishPostCommandHandler(repo=repo, event_bus=event_bus)
        post_id = uuid4()
        author_id = uuid4()

        cmd = PublishPostCommand(post_id=post_id, requesting_author_id=author_id)

        with pytest.raises(PostNotFoundError):
            handler.handle(cmd)

        event_bus.publish_many.assert_not_called()

    def test_handle_publish_success_saves_and_publishes_events(self):
        """Publicar post guarda y publica eventos."""
        post = _make_draft_post()
        repo = Mock()
        repo.get_by_id.return_value = post
        event_bus = Mock()
        handler = PublishPostCommandHandler(repo=repo, event_bus=event_bus)

        cmd = PublishPostCommand(
            post_id=post.id,
            requesting_author_id=post.author_id,
        )
        handler.handle(cmd)

        assert post.status == PostStatus.PUBLISHED
        repo.save.assert_called_once_with(post)
        event_bus.publish_many.assert_called_once()

    def test_handle_publish_already_published_raises(self):
        """Publicar un post ya publicado lanza PostAlreadyPublishedError."""
        post = _make_published_post()
        repo = Mock()
        repo.get_by_id.return_value = post
        event_bus = Mock()
        handler = PublishPostCommandHandler(repo=repo, event_bus=event_bus)

        cmd = PublishPostCommand(
            post_id=post.id,
            requesting_author_id=post.author_id,
        )

        with pytest.raises(PostAlreadyPublishedError):
            handler.handle(cmd)

    def test_handle_publish_short_content_raises(self):
        """Publicar post con contenido corto lanza InvalidPostContentError."""
        short_content = "Muy corto"
        post = PostAggregate(
            title=Title("Corto"),
            content=Content(short_content),
            author_id=uuid4(),
        )
        repo = Mock()
        repo.get_by_id.return_value = post
        event_bus = Mock()
        handler = PublishPostCommandHandler(repo=repo, event_bus=event_bus)

        cmd = PublishPostCommand(
            post_id=post.id,
            requesting_author_id=post.author_id,
        )

        with pytest.raises(InvalidPostContentError):
            handler.handle(cmd)


# ─────────────────────────────────────────────────────────────
# ARCHIVE POST
# ─────────────────────────────────────────────────────────────
class TestArchivePostCommandHandler:
    """Tests del handler ArchivePost."""

    def test_handle_post_not_found_raises(self):
        """Si el post no existe se lanza PostNotFoundError."""
        repo = Mock()
        repo.get_by_id.return_value = None
        event_bus = Mock()
        handler = ArchivePostCommandHandler(repo=repo, event_bus=event_bus)
        post_id = uuid4()
        author_id = uuid4()

        cmd = ArchivePostCommand(post_id=post_id, requesting_author_id=author_id)

        with pytest.raises(PostNotFoundError):
            handler.handle(cmd)

    def test_handle_archive_success(self):
        """Archivar post (autor) guarda y publica eventos."""
        post = _make_published_post()
        repo = Mock()
        repo.get_by_id.return_value = post
        event_bus = Mock()
        handler = ArchivePostCommandHandler(repo=repo, event_bus=event_bus)

        cmd = ArchivePostCommand(
            post_id=post.id,
            requesting_author_id=post.author_id,
        )
        handler.handle(cmd)

        assert post.status == PostStatus.ARCHIVED
        repo.save.assert_called_once_with(post)
        event_bus.publish_many.assert_called_once()

    def test_handle_archive_unauthorized_raises(self):
        """Solo el autor puede archivar; otro usuario lanza UnauthorizedPostActionError."""
        author_id = uuid4()
        other_id = uuid4()
        post = _make_published_post(author_id=author_id)
        repo = Mock()
        repo.get_by_id.return_value = post
        event_bus = Mock()
        handler = ArchivePostCommandHandler(repo=repo, event_bus=event_bus)

        cmd = ArchivePostCommand(
            post_id=post.id,
            requesting_author_id=other_id,
        )

        with pytest.raises(UnauthorizedPostActionError):
            handler.handle(cmd)


# ─────────────────────────────────────────────────────────────
# ADD COMMENT
# ─────────────────────────────────────────────────────────────
class TestAddCommentCommandHandler:
    """Tests del handler AddComment."""

    def test_handle_post_not_found_raises(self):
        """Si el post no existe se lanza PostNotFoundError."""
        repo = Mock()
        repo.get_by_id.return_value = None
        event_bus = Mock()
        handler = AddCommentCommandHandler(repo=repo, event_bus=event_bus)
        post_id = uuid4()
        commenter_id = uuid4()

        cmd = AddCommentCommand(
            post_id=post_id,
            body="Un comentario",
            commenter_id=commenter_id,
        )

        with pytest.raises(PostNotFoundError):
            handler.handle(cmd)

    def test_handle_add_comment_returns_comment_dto(self):
        """Añadir comentario persiste y retorna CommentDTO."""
        post = _make_published_post()
        repo = Mock()
        repo.get_by_id.return_value = post
        event_bus = Mock()
        handler = AddCommentCommandHandler(repo=repo, event_bus=event_bus)
        commenter_id = uuid4()

        cmd = AddCommentCommand(
            post_id=post.id,
            body="Excelente artículo!",
            commenter_id=commenter_id,
        )
        result = handler.handle(cmd)

        assert isinstance(result, CommentDTO)
        assert result.body == "Excelente artículo!"
        assert result.author_id == commenter_id
        assert result.id is not None
        assert result.created_at is not None
        repo.save.assert_called_once_with(post)
        event_bus.publish_many.assert_called_once()


# ─────────────────────────────────────────────────────────────
# GET POST BY SLUG
# ─────────────────────────────────────────────────────────────
class TestGetPostBySlugQueryHandler:
    """Tests del handler GetPostBySlug."""

    def test_handle_slug_not_found_raises(self):
        """Slug inexistente lanza PostNotFoundError."""
        read_repo = Mock()
        read_repo.find_by_slug.return_value = None
        handler = GetPostBySlugQueryHandler(read_repo=read_repo)

        query = GetPostBySlugQuery(slug="no-existe")

        with pytest.raises(PostNotFoundError):
            handler.handle(query)

    def test_handle_returns_post_detail_dto(self):
        """Post encontrado por slug retorna PostDetailDTO."""
        post = _make_published_post()
        post.add_tags(["python"])
        read_repo = Mock()
        read_repo.find_by_slug.return_value = post
        handler = GetPostBySlugQueryHandler(read_repo=read_repo)

        query = GetPostBySlugQuery(slug=post.slug.value)
        result = handler.handle(query)

        assert isinstance(result, PostDetailDTO)
        assert result.id == post.id
        assert result.title == post.title.value
        assert result.slug == post.slug.value
        assert result.content == post.content.value
        assert result.status == post.status.value
        assert result.author_id == post.author_id
        assert result.category_id == post.category_id
        assert result.tags == post.tags
        assert result.word_count == post.content.word_count
        read_repo.find_by_slug.assert_called_once_with("post-de-prueba")


# ─────────────────────────────────────────────────────────────
# GET POST BY ID
# ─────────────────────────────────────────────────────────────
class TestGetPostByIdQueryHandler:
    """Tests del handler GetPostById."""

    def test_handle_id_not_found_raises(self):
        """ID inexistente lanza PostNotFoundError."""
        read_repo = Mock()
        read_repo.get_by_id.return_value = None
        handler = GetPostByIdQueryHandler(read_repo=read_repo)
        post_id = uuid4()

        query = GetPostByIdQuery(post_id=post_id)

        with pytest.raises(PostNotFoundError):
            handler.handle(query)

    def test_handle_returns_post_detail_dto(self):
        """Post encontrado por ID retorna PostDetailDTO."""
        post = _make_published_post()
        read_repo = Mock()
        read_repo.get_by_id.return_value = post
        handler = GetPostByIdQueryHandler(read_repo=read_repo)

        query = GetPostByIdQuery(post_id=post.id)
        result = handler.handle(query)

        assert isinstance(result, PostDetailDTO)
        assert result.id == post.id
        assert result.title == post.title.value
        read_repo.get_by_id.assert_called_once_with(post.id)


# ─────────────────────────────────────────────────────────────
# LIST PUBLISHED POSTS
# ─────────────────────────────────────────────────────────────
class TestListPublishedPostsQueryHandler:
    """Tests del handler ListPublishedPosts."""

    def test_handle_returns_post_list_dto(self):
        """Listar publicados retorna PostListDTO con items y paginación."""
        post = _make_published_post()
        read_repo = Mock()
        read_repo.find_published.return_value = ([post], 1)
        handler = ListPublishedPostsQueryHandler(read_repo=read_repo)

        query = ListPublishedPostsQuery(page=1, page_size=10)
        result = handler.handle(query)

        assert isinstance(result, PostListDTO)
        assert result.total == 1
        assert result.page == 1
        assert result.page_size == 10
        assert len(result.items) == 1
        assert isinstance(result.items[0], PostSummaryDTO)
        assert result.items[0].id == post.id
        assert result.items[0].title == post.title.value
        read_repo.find_published.assert_called_once_with(
            page=1, page_size=10, tag=None
        )

    def test_handle_with_tag_filter(self):
        """Listar con filtro por tag llama al repo con tag."""
        read_repo = Mock()
        read_repo.find_published.return_value = ([], 0)
        handler = ListPublishedPostsQueryHandler(read_repo=read_repo)

        query = ListPublishedPostsQuery(page=2, page_size=5, tag="django")
        result = handler.handle(query)

        read_repo.find_published.assert_called_once_with(
            page=2, page_size=5, tag="django"
        )
        assert result.total == 0
        assert result.items == []


# ─────────────────────────────────────────────────────────────
# LIST POSTS BY AUTHOR
# ─────────────────────────────────────────────────────────────
class TestListPostsByAuthorQueryHandler:
    """Tests del handler ListPostsByAuthor."""

    def test_handle_returns_post_list_dto(self):
        """Listar por autor retorna PostListDTO."""
        author_id = uuid4()
        post = _make_published_post(author_id=author_id)
        read_repo = Mock()
        read_repo.find_by_author.return_value = ([post], 1)
        handler = ListPostsByAuthorQueryHandler(read_repo=read_repo)

        query = ListPostsByAuthorQuery(author_id=author_id, page=1, page_size=10)
        result = handler.handle(query)

        assert isinstance(result, PostListDTO)
        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].author_id == author_id
        read_repo.find_by_author.assert_called_once_with(
            author_id=author_id, page=1, page_size=10
        )


# ─────────────────────────────────────────────────────────────
# EVENT HANDLERS
# ─────────────────────────────────────────────────────────────
class TestOnPostPublished:
    """Tests del event handler OnPostPublished."""

    def test_handle_without_services_does_not_raise(self):
        """Sin servicios opcionales no falla."""
        handler = OnPostPublished()
        event = PostPublished(post_id=uuid4(), slug="mi-post")

        handler.handle(event)  # no raise

    def test_handle_invalidates_cache_when_service_present(self):
        """Con cache_service invalida las claves esperadas."""
        cache = Mock()
        handler = OnPostPublished(cache_service=cache)
        post_id = uuid4()
        event = PostPublished(post_id=post_id, slug="mi-post")

        handler.handle(event)

        assert cache.invalidate.call_count >= 1
        cache.invalidate.assert_any_call("posts:published:*")
        cache.invalidate.assert_any_call("posts:slug:mi-post")

    def test_handle_sends_email_when_service_present(self):
        """Con email_service envía notificación."""
        email_svc = Mock()
        handler = OnPostPublished(email_service=email_svc)
        post_id = uuid4()
        event = PostPublished(post_id=post_id, slug="mi-post")

        handler.handle(event)

        email_svc.send_post_published_notification.assert_called_once_with(
            post_id=post_id, slug="mi-post"
        )


class TestOnCommentAdded:
    """Tests del event handler OnCommentAdded."""

    def test_handle_without_services_does_not_raise(self):
        """Sin servicios opcionales no falla."""
        handler = OnCommentAdded()
        event = CommentAdded(
            post_id=uuid4(), comment_id=uuid4(), author_id=uuid4()
        )
        handler.handle(event)

    def test_handle_moderation_and_notify_when_services_present(self):
        """Con servicios llama a moderación y notificación."""
        moderation = Mock()
        notifications = Mock()
        handler = OnCommentAdded(
            notification_service=notifications,
            moderation_service=moderation,
        )
        post_id = uuid4()
        comment_id = uuid4()
        event = CommentAdded(
            post_id=post_id, comment_id=comment_id, author_id=uuid4()
        )

        handler.handle(event)

        moderation.check_comment.assert_called_once_with(comment_id)
        notifications.notify_new_comment.assert_called_once_with(
            post_id=post_id, comment_id=comment_id
        )


class TestOnPostArchived:
    """Tests del event handler OnPostArchived."""

    def test_handle_without_services_does_not_raise(self):
        """Sin servicios opcionales no falla."""
        handler = OnPostArchived()
        event = PostArchived(post_id=uuid4())
        handler.handle(event)

    def test_handle_invalidates_cache_and_audit_when_services_present(self):
        """Con cache y audit invalida y registra."""
        cache = Mock()
        audit = Mock()
        handler = OnPostArchived(cache_service=cache, audit_log=audit)
        post_id = uuid4()
        event = PostArchived(post_id=post_id)

        handler.handle(event)

        cache.invalidate.assert_any_call(f"posts:id:{post_id}")
        cache.invalidate.assert_any_call("posts:published:*")
        audit.record.assert_called_once()
        call_kw = audit.record.call_args[1]
        assert call_kw["action"] == "post_archived"
        assert call_kw["entity_id"] == str(post_id)
        assert "occurred_at" in call_kw


class TestOnPostCreated:
    """Tests del event handler OnPostCreated."""

    def test_handle_without_analytics_does_not_raise(self):
        """Sin analytics no falla."""
        handler = OnPostCreated()
        event = PostCreated(
            post_id=uuid4(), author_id=uuid4(), title="Nuevo"
        )
        handler.handle(event)

    def test_handle_tracks_analytics_when_service_present(self):
        """Con analytics registra post creado."""
        analytics = Mock()
        handler = OnPostCreated(analytics_service=analytics)
        post_id = uuid4()
        author_id = uuid4()
        event = PostCreated(
            post_id=post_id, author_id=author_id, title="Nuevo"
        )

        handler.handle(event)

        analytics.track_post_created.assert_called_once_with(
            post_id=post_id, author_id=author_id
        )
