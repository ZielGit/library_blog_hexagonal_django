"""
FEATURE TESTS - Blog Business Workflows

Tests de features que verifican comportamientos de negocio complejos
y flujos completos usando múltiples commands/queries.
"""
import pytest
from datetime import datetime

from src.application.blog.commands.create_post import CreatePostCommand, CreatePostCommandHandler
from src.application.blog.commands.publish_post import PublishPostCommandHandler, PublishPostCommand
from src.application.blog.commands.add_comment import AddCommentCommandHandler, AddCommentCommand
from src.application.blog.commands.archive_post import ArchivePostCommandHandler, ArchivePostCommand
from src.application.blog.queries.list_posts import ListPublishedPostsQueryHandler, ListPublishedPostsQuery
from src.domain.shared.base import DomainError


@pytest.mark.django_db
@pytest.mark.feature
class TestPostLifecycle:
    """Feature: Ciclo de vida completo de un post."""
    
    def test_complete_post_lifecycle_draft_to_archived(self, blog_repo, test_user):
        """
        Escenario: Usuario crea post, lo publica, recibe comentarios, y lo archiva
        
        Given un usuario registrado
        When crea un post en draft
        And lo publica
        And recibe comentarios
        And lo archiva
        Then el post pasa por todos los estados correctamente
        """
        # Given - usuario registrado (test_user fixture)
        
        # When - crea post en draft
        create_handler = CreatePostCommandHandler(repo=blog_repo)
        create_cmd = CreatePostCommand(
            title="Mi experiencia con Django",
            content="En este artículo compartiré mi experiencia usando Django. " * 10,
            author_id=test_user.id,
            tags=["django", "python", "web"],
        )
        post_dto = create_handler.handle(create_cmd)
        
        # Verificar draft
        post = blog_repo.get_by_id(post_dto.id)
        assert post.status.value == "draft"
        assert post.published_at is None
        
        # When - publica post
        publish_handler = PublishPostCommandHandler(repo=blog_repo)
        publish_cmd = PublishPostCommand(
            post_id=post.id,
            requesting_author_id=test_user.id,
        )
        publish_handler.handle(publish_cmd)
        
        # Verificar publicado
        post = blog_repo.get_by_id(post.id)
        assert post.status.value == "published"
        assert post.published_at is not None
        
        # When - recibe comentarios
        comment_handler = AddCommentCommandHandler(repo=blog_repo)
        for i in range(3):
            comment_cmd = AddCommentCommand(
                post_id=post.id,
                body=f"Gran artículo! Comentario {i+1}",
                commenter_id=test_user.id,
            )
            comment_handler.handle(comment_cmd)
        
        # Verificar comentarios
        post = blog_repo.get_by_id(post.id)
        assert len(post.comments) == 3
        
        # When - archiva post
        archive_handler = ArchivePostCommandHandler(repo=blog_repo)
        archive_cmd = ArchivePostCommand(
            post_id=post.id,
            requesting_author_id=test_user.id,
        )
        archive_handler.handle(archive_cmd)
        
        # Then - verificar archived
        post = blog_repo.get_by_id(post.id)
        assert post.status.value == "archived"


@pytest.mark.django_db
@pytest.mark.feature
class TestPublishedPostsVisibility:
    """Feature: Visibilidad de posts según estado."""
    
    def test_only_published_posts_visible_in_public_list(self, blog_repo, test_user, editor_user):
        """
        Escenario: Solo posts publicados son visibles en lista pública
        
        Given múltiples posts en diferentes estados
        When se lista posts publicados
        Then solo aparecen los publicados
        """
        create_handler = CreatePostCommandHandler(repo=blog_repo)
        publish_handler = PublishPostCommandHandler(repo=blog_repo)
        archive_handler = ArchivePostCommandHandler(repo=blog_repo)
        
        # Given - crear posts en diferentes estados
        # Post 1: Publicado
        cmd1 = CreatePostCommand(
            title="Post publicado 1",
            content="Contenido largo " * 20,
            author_id=test_user.id,
        )
        post1_dto = create_handler.handle(cmd1)
        publish_handler.handle(PublishPostCommand(post1_dto.id, test_user.id))
        
        # Post 2: Draft
        cmd2 = CreatePostCommand(
            title="Post en draft",
            content="Contenido largo " * 20,
            author_id=test_user.id,
        )
        create_handler.handle(cmd2)
        
        # Post 3: Publicado
        cmd3 = CreatePostCommand(
            title="Post publicado 2",
            content="Contenido largo " * 20,
            author_id=editor_user.id,
        )
        post3_dto = create_handler.handle(cmd3)
        publish_handler.handle(PublishPostCommand(post3_dto.id, editor_user.id))
        
        # Post 4: Publicado y archivado
        cmd4 = CreatePostCommand(
            title="Post archivado",
            content="Contenido largo " * 20,
            author_id=test_user.id,
        )
        post4_dto = create_handler.handle(cmd4)
        publish_handler.handle(PublishPostCommand(post4_dto.id, test_user.id))
        archive_handler.handle(ArchivePostCommand(post4_dto.id, test_user.id))
        
        # When - listar posts publicados
        list_handler = ListPublishedPostsQueryHandler(read_repo=blog_repo)
        query = ListPublishedPostsQuery(page=1, page_size=10)
        result = list_handler.handle(query)
        
        # Then - solo 2 posts publicados (no draft, no archived)
        assert result.total == 2
        assert len(result.items) == 2
        
        titles = [p.title for p in result.items]
        assert "Post publicado 1" in titles
        assert "Post publicado 2" in titles
        assert "Post en draft" not in titles
        assert "Post archivado" not in titles


@pytest.mark.django_db
@pytest.mark.feature
class TestContentValidationRules:
    """Feature: Reglas de validación de contenido."""
    
    def test_cannot_publish_post_with_insufficient_content(self, blog_repo, test_user):
        """
        Escenario: Post con contenido insuficiente no puede publicarse
        
        Given un post con contenido corto (< 100 chars)
        When intenta publicarlo
        Then recibe error de validación
        """
        create_handler = CreatePostCommandHandler(repo=blog_repo)
        publish_handler = PublishPostCommandHandler(repo=blog_repo)
        
        # Given - post con contenido corto
        cmd = CreatePostCommand(
            title="Post con poco contenido",
            content="Muy corto",  # < 100 chars
            author_id=test_user.id,
        )
        post_dto = create_handler.handle(cmd)
        
        # When/Then - publicar falla
        with pytest.raises(DomainError, match="al menos 100 caracteres"):
            publish_handler.handle(
                PublishPostCommand(post_dto.id, test_user.id)
            )
    
    def test_can_save_draft_with_any_content_length(self, blog_repo, test_user):
        """
        Escenario: Draft puede tener cualquier longitud de contenido
        
        Given un usuario
        When crea un draft con contenido corto
        Then se guarda exitosamente
        """
        create_handler = CreatePostCommandHandler(repo=blog_repo)
        
        # When - crear draft con contenido muy corto
        cmd = CreatePostCommand(
            title="Draft corto",
            content="Solo 10 caracteres",
            author_id=test_user.id,
        )
        post_dto = create_handler.handle(cmd)
        
        # Then - se creó exitosamente
        assert post_dto.id is not None
        
        post = blog_repo.get_by_id(post_dto.id)
        assert post.status.value == "draft"


@pytest.mark.django_db
@pytest.mark.feature
class TestCommentingRules:
    """Feature: Reglas de comentarios."""
    
    def test_can_comment_on_published_post(self, blog_repo, test_user, editor_user):
        """
        Escenario: Se puede comentar en posts publicados
        
        Given un post publicado
        When cualquier usuario agrega comentario
        Then el comentario se guarda
        """
        # Given - post publicado
        create_handler = CreatePostCommandHandler(repo=blog_repo)
        publish_handler = PublishPostCommandHandler(repo=blog_repo)
        comment_handler = AddCommentCommandHandler(repo=blog_repo)
        
        cmd = CreatePostCommand(
            title="Post comentable",
            content="Contenido largo " * 20,
            author_id=test_user.id,
        )
        post_dto = create_handler.handle(cmd)
        publish_handler.handle(PublishPostCommand(post_dto.id, test_user.id))
        
        # When - otro usuario comenta
        comment_cmd = AddCommentCommand(
            post_id=post_dto.id,
            body="Muy interesante!",
            commenter_id=editor_user.id,
        )
        comment_dto = comment_handler.handle(comment_cmd)
        
        # Then - comentario guardado
        assert comment_dto.id is not None
        
        post = blog_repo.get_by_id(post_dto.id)
        assert len(post.comments) == 1
        assert post.comments[0].author_id == editor_user.id
    
    def test_cannot_comment_on_archived_post(self, blog_repo, test_user):
        """
        Escenario: No se puede comentar en posts archivados
        
        Given un post archivado
        When intenta agregar comentario
        Then recibe error
        """
        # Given - post archivado
        create_handler = CreatePostCommandHandler(repo=blog_repo)
        publish_handler = PublishPostCommandHandler(repo=blog_repo)
        archive_handler = ArchivePostCommandHandler(repo=blog_repo)
        comment_handler = AddCommentCommandHandler(repo=blog_repo)
        
        cmd = CreatePostCommand(
            title="Post archivado",
            content="Contenido largo " * 20,
            author_id=test_user.id,
        )
        post_dto = create_handler.handle(cmd)
        publish_handler.handle(PublishPostCommand(post_dto.id, test_user.id))
        archive_handler.handle(ArchivePostCommand(post_dto.id, test_user.id))
        
        # When/Then - comentar falla
        with pytest.raises(DomainError, match="comentar"):
            comment_handler.handle(
                AddCommentCommand(
                    post_id=post_dto.id,
                    body="Intento comentar",
                    commenter_id=test_user.id,
                )
            )


@pytest.mark.django_db
@pytest.mark.feature
class TestAuthorizationRules:
    """Feature: Reglas de autorización."""
    
    def test_only_author_can_archive_own_post(self, blog_repo, test_user, editor_user):
        """
        Escenario: Solo el autor puede archivar su post
        
        Given un post de usuario A
        When usuario B intenta archivarlo
        Then recibe error de autorización
        """
        # Given - post de test_user
        create_handler = CreatePostCommandHandler(repo=blog_repo)
        publish_handler = PublishPostCommandHandler(repo=blog_repo)
        archive_handler = ArchivePostCommandHandler(repo=blog_repo)
        
        cmd = CreatePostCommand(
            title="Post de test_user",
            content="Contenido largo " * 20,
            author_id=test_user.id,
        )
        post_dto = create_handler.handle(cmd)
        publish_handler.handle(PublishPostCommand(post_dto.id, test_user.id))
        
        # When/Then - editor_user no puede archivar
        with pytest.raises(DomainError, match="autorizado"):
            archive_handler.handle(
                ArchivePostCommand(
                    post_id=post_dto.id,
                    requesting_author_id=editor_user.id,  # ← diferente autor
                )
            )
        
        # But - test_user sí puede
        archive_handler.handle(
            ArchivePostCommand(
                post_id=post_dto.id,
                requesting_author_id=test_user.id,  # ← mismo autor
            )
        )
        
        post = blog_repo.get_by_id(post_dto.id)
        assert post.status.value == "archived"
