"""
INTEGRATION TESTS - Blog Commands + Repositories

Tests de integración que verifican que commands/queries funcionan
correctamente con repositorios reales (Django ORM + PostgreSQL).
"""
import pytest
from uuid import uuid4

from src.application.blog.commands.create_post import CreatePostCommand, CreatePostCommandHandler
from src.application.blog.commands.publish_post import PublishPostCommand, PublishPostCommandHandler
from src.application.blog.commands.add_comment import AddCommentCommand, AddCommentCommandHandler
from src.application.blog.commands.archive_post import ArchivePostCommand, ArchivePostCommandHandler
from src.application.blog.queries.get_post import GetPostBySlugQuery, GetPostBySlugQueryHandler
from src.application.blog.queries.list_posts import ListPublishedPostsQuery, ListPublishedPostsQueryHandler
from src.domain.shared.base import DomainError, NotFoundError
from src.infrastructure.persistence.models import PostModel, CommentModel


@pytest.mark.django_db
class TestCreatePostCommand:
    """Tests de integración para CreatePostCommand."""
    
    def test_create_post_persists_to_database(self, blog_repo, test_user):
        """Crear post lo persiste en la base de datos."""
        command = CreatePostCommand(
            title="Post de integración",
            content="Contenido con suficiente longitud para cumplir reglas de negocio y poder publicar después.",
            author_id=test_user.id,
            tags=["integration", "test"],
        )
        
        handler = CreatePostCommandHandler(repo=blog_repo)
        result = handler.handle(command)
        
        # Verificar en BD
        assert PostModel.objects.filter(id=result.id).exists()
        
        post_model = PostModel.objects.get(id=result.id)
        assert post_model.title == "Post de integración"
        assert post_model.slug == "post-de-integracion"
        assert post_model.status == "draft"
        assert post_model.author_id == test_user.id
        assert "integration" in post_model.tags
    
    def test_create_multiple_posts_same_title_generates_unique_ids(self, blog_repo, test_user):
        """Crear múltiples posts con mismo título genera IDs únicos."""
        handler = CreatePostCommandHandler(repo=blog_repo)
        
        command1 = CreatePostCommand(
            title="Post duplicado",
            content="Primer contenido largo " * 20,
            author_id=test_user.id,
        )
        command2 = CreatePostCommand(
            title="Post duplicado",
            content="Segundo contenido largo " * 20,
            author_id=test_user.id,
        )
        
        result1 = handler.handle(command1)
        result2 = handler.handle(command2)
        
        assert result1.id != result2.id
        assert PostModel.objects.count() == 2


@pytest.mark.django_db
class TestPublishPostCommand:
    """Tests de integración para PublishPostCommand."""
    
    def test_publish_post_updates_status_in_database(self, blog_repo, test_user):
        """Publicar post actualiza status en BD."""
        # Crear post en draft
        post = blog_repo.create_post(
            title="Post para publicar",
            content="Contenido largo " * 20,
            author_id=test_user.id,
        )
        blog_repo.save(post)
        
        # Publicar
        command = PublishPostCommand(
            post_id=post.id,
            requesting_author_id=test_user.id,
        )
        handler = PublishPostCommandHandler(repo=blog_repo)
        handler.handle(command)
        
        # Verificar en BD
        post_model = PostModel.objects.get(id=post.id)
        assert post_model.status == "published"
        assert post_model.published_at is not None
    
    def test_publish_nonexistent_post_raises_error(self, blog_repo, test_user):
        """Publicar post inexistente lanza NotFoundError."""
        command = PublishPostCommand(
            post_id=uuid4(),
            requesting_author_id=test_user.id,
        )
        handler = PublishPostCommandHandler(repo=blog_repo)
        
        with pytest.raises(NotFoundError):
            handler.handle(command)
    
    def test_publish_short_content_post_raises_domain_error(self, blog_repo, test_user):
        """Publicar post con contenido corto lanza DomainError."""
        post = blog_repo.create_post(
            title="Post con contenido corto",
            content="Muy corto",
            author_id=test_user.id,
        )
        blog_repo.save(post)
        
        command = PublishPostCommand(
            post_id=post.id,
            requesting_author_id=test_user.id,
        )
        handler = PublishPostCommandHandler(repo=blog_repo)
        
        with pytest.raises(DomainError, match="al menos 100 caracteres"):
            handler.handle(command)


@pytest.mark.django_db
class TestAddCommentCommand:
    """Tests de integración para AddCommentCommand."""
    
    def test_add_comment_persists_to_database(self, blog_repo, test_user):
        """Agregar comentario lo persiste en BD."""
        # Crear y publicar post
        post = blog_repo.create_post(
            title="Post con comentarios",
            content="Contenido largo " * 20,
            author_id=test_user.id,
        )
        post.publish(author_id=test_user.id)
        blog_repo.save(post)
        
        # Agregar comentario
        command = AddCommentCommand(
            post_id=post.id,
            body="Excelente artículo!",
            commenter_id=test_user.id,
        )
        handler = AddCommentCommandHandler(repo=blog_repo)
        result = handler.handle(command)
        
        # Verificar en BD
        assert CommentModel.objects.filter(id=result.id).exists()
        comment_model = CommentModel.objects.get(id=result.id)
        assert comment_model.body == "Excelente artículo!"
        assert comment_model.post_id == post.id
    
    def test_add_multiple_comments_to_same_post(self, blog_repo, test_user):
        """Se pueden agregar múltiples comentarios al mismo post."""
        post = blog_repo.create_post(
            title="Post popular",
            content="Contenido largo " * 20,
            author_id=test_user.id,
        )
        post.publish(author_id=test_user.id)
        blog_repo.save(post)
        
        handler = AddCommentCommandHandler(repo=blog_repo)
        
        for i in range(3):
            command = AddCommentCommand(
                post_id=post.id,
                body=f"Comentario número {i+1}",
                commenter_id=test_user.id,
            )
            handler.handle(command)
        
        # Verificar en BD
        assert CommentModel.objects.filter(post_id=post.id).count() == 3


@pytest.mark.django_db
class TestArchivePostCommand:
    """Tests de integración para ArchivePostCommand."""
    
    def test_archive_post_updates_status_in_database(self, blog_repo, test_user):
        """Archivar post actualiza status en BD."""
        post = blog_repo.create_post(
            title="Post para archivar",
            content="Contenido largo " * 20,
            author_id=test_user.id,
        )
        post.publish(author_id=test_user.id)
        blog_repo.save(post)
        
        command = ArchivePostCommand(
            post_id=post.id,
            requesting_author_id=test_user.id,
        )
        handler = ArchivePostCommandHandler(repo=blog_repo)
        handler.handle(command)
        
        post_model = PostModel.objects.get(id=post.id)
        assert post_model.status == "archived"
    
    def test_archive_other_user_post_raises_error(self, blog_repo, test_user, editor_user):
        """No se puede archivar post de otro usuario."""
        post = blog_repo.create_post(
            title="Post de otro usuario",
            content="Contenido largo " * 20,
            author_id=test_user.id,
        )
        post.publish(author_id=test_user.id)
        blog_repo.save(post)
        
        command = ArchivePostCommand(
            post_id=post.id,
            requesting_author_id=editor_user.id,  # usuario diferente
        )
        handler = ArchivePostCommandHandler(repo=blog_repo)
        
        with pytest.raises(DomainError, match="autorizado"):
            handler.handle(command)


@pytest.mark.django_db
class TestGetPostBySlugQuery:
    """Tests de integración para GetPostBySlugQuery."""
    
    def test_get_existing_post_returns_dto(self, blog_repo, test_user):
        """Obtener post existente retorna DTO."""
        post = blog_repo.create_post(
            title="Post consultable",
            content="Contenido largo " * 20,
            author_id=test_user.id,
        )
        blog_repo.save(post)
        
        query = GetPostBySlugQuery(slug="post-consultable")
        handler = GetPostBySlugQueryHandler(repo=blog_repo)
        result = handler.handle(query)
        
        assert result is not None
        assert result.title == "Post consultable"
        assert result.slug == "post-consultable"
        assert result.author_id == test_user.id
    
    def test_get_nonexistent_post_returns_none(self, blog_repo):
        """Obtener post inexistente retorna None."""
        query = GetPostBySlugQuery(slug="no-existe")
        handler = GetPostBySlugQueryHandler(repo=blog_repo)
        result = handler.handle(query)
        
        assert result is None


@pytest.mark.django_db
class TestListPublishedPostsQuery:
    """Tests de integración para ListPublishedPostsQuery."""
    
    def test_list_only_shows_published_posts(self, blog_repo, test_user):
        """Listar solo muestra posts publicados, no drafts."""
        # Crear 2 posts: 1 publicado, 1 draft
        post1 = blog_repo.create_post(
            title="Post publicado",
            content="Contenido largo " * 20,
            author_id=test_user.id,
        )
        post1.publish(author_id=test_user.id)
        blog_repo.save(post1)
        
        post2 = blog_repo.create_post(
            title="Post en draft",
            content="Contenido largo " * 20,
            author_id=test_user.id,
        )
        blog_repo.save(post2)
        
        # Listar
        query = ListPublishedPostsQuery(page=1, page_size=10)
        handler = ListPublishedPostsQueryHandler(read_repo=blog_repo)
        result = handler.handle(query)
        
        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].title == "Post publicado"
    
    def test_pagination_works_correctly(self, blog_repo, test_user):
        """Paginación funciona correctamente."""
        # Crear 5 posts publicados
        for i in range(5):
            post = blog_repo.create_post(
                title=f"Post {i}",
                content="Contenido largo " * 20,
                author_id=test_user.id,
            )
            post.publish(author_id=test_user.id)
            blog_repo.save(post)
        
        # Página 1 (2 items)
        query = ListPublishedPostsQuery(page=1, page_size=2)
        handler = ListPublishedPostsQueryHandler(read_repo=blog_repo)
        result = handler.handle(query)
        
        assert result.total == 5
        assert len(result.items) == 2
        assert result.page == 1
        assert result.has_next is True
        
        # Página 2
        query = ListPublishedPostsQuery(page=2, page_size=2)
        result = handler.handle(query)
        
        assert len(result.items) == 2
        assert result.page == 2
