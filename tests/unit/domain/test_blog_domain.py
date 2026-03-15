"""
UNIT TESTS - Blog Domain

Tests unitarios que verifican la lógica de negocio del dominio Blog.
No tocan la base de datos, usan entidades en memoria.
"""
import pytest
from datetime import datetime
from uuid import uuid4

from src.domain.blog.aggregates import PostAggregate
from src.domain.blog.entities import Post, Comment, PostStatus, Category
from src.domain.blog.value_objects import Title, Content
from src.domain.blog.exceptions import (
    PostAlreadyPublishedError,
    PostArchivedError,
    InvalidPostContentError,
    UnauthorizedPostActionError,
    CommentNotAllowedError,
)


class TestPostAggregate:
    """Tests del agregado PostAggregate."""
    
    def test_create_post_generates_valid_aggregate(self):
        """Crear post genera un aggregate válido en draft."""
        author_id = uuid4()
        
        post = PostAggregate.create(
            title=Title("Mi primer post"),
            content=Content("Contenido del post con más de 100 caracteres para cumplir la regla de negocio que requiere contenido sustancial."),
            author_id=author_id,
            tags=["django", "python"],
        )
        
        assert post.id is not None
        assert post.title.value == "Mi primer post"
        assert post.slug.value == "mi-primer-post"
        assert post.status == PostStatus.DRAFT
        assert post.author_id == author_id
        assert post.tags == ["django", "python"]
        assert len(post.comments) == 0
    
    def test_publish_post_changes_status_and_sets_published_at(self):
        """Publicar post cambia status y establece published_at."""
        author_id = uuid4()
        post = PostAggregate.create(
            title=Title("Post para publicar"),
            content=Content("Contenido suficientemente largo con más de cien caracteres para poder publicar este post sin problemas."),
            author_id=author_id,
        )
        
        # Publicar
        post.publish(author_id=author_id)
        
        assert post.status == PostStatus.PUBLISHED
        assert post.published_at is not None
        assert isinstance(post.published_at, datetime)
    
    def test_publish_short_content_raises_error(self):
        """Publicar post con contenido corto lanza error."""
        author_id = uuid4()
        post = PostAggregate.create(
            title=Title("Post con contenido corto"),
            content=Content("Muy corto"),  # < 100 chars
            author_id=author_id,
        )
        
        with pytest.raises(InvalidPostContentError, match="al menos 100 caracteres"):
            post.publish(author_id=author_id)
    
    def test_publish_already_published_post_raises_error(self):
        """No se puede publicar un post ya publicado."""
        author_id = uuid4()
        post = PostAggregate.create(
            title=Title("Post ya publicado"),
            content=Content("Contenido largo " * 20),
            author_id=author_id,
        )
        
        post.publish(author_id=author_id)
        
        with pytest.raises(PostAlreadyPublishedError):
            post.publish(author_id=author_id)
    
    def test_archive_post_changes_status(self):
        """Archivar post cambia el status a ARCHIVED."""
        author_id = uuid4()
        post = PostAggregate.create(
            title=Title("Post para archivar"),
            content=Content("Contenido largo " * 20),
            author_id=author_id,
        )
        
        post.publish(author_id=author_id)
        post.archive(requesting_author_id=author_id)
        
        assert post.status == PostStatus.ARCHIVED
    
    def test_archive_requires_author_authorization(self):
        """Solo el autor puede archivar su post."""
        author_id = uuid4()
        other_user_id = uuid4()
        
        post = PostAggregate.create(
            title=Title("Post de otro autor"),
            content=Content("Contenido largo " * 20),
            author_id=author_id,
        )
        post.publish(author_id=author_id)
        
        with pytest.raises(UnauthorizedPostActionError):
            post.archive(requesting_author_id=other_user_id)
    
    def test_add_comment_to_published_post(self):
        """Se puede agregar comentario a post publicado."""
        author_id = uuid4()
        commenter_id = uuid4()
        
        post = PostAggregate.create(
            title=Title("Post con comentarios"),
            content=Content("Contenido largo " * 20),
            author_id=author_id,
        )
        post.publish(author_id=author_id)
        
        post.add_comment(
            body="Excelente artículo!",
            commenter_id=commenter_id,
        )
        
        assert len(post.comments) == 1
        assert post.comments[0].body == "Excelente artículo!"
        assert post.comments[0].author_id == commenter_id
    
    def test_cannot_comment_on_archived_post(self):
        """No se puede comentar en post archivado."""
        author_id = uuid4()
        commenter_id = uuid4()
        
        post = PostAggregate.create(
            title=Title("Post archivado"),
            content=Content("Contenido largo " * 20),
            author_id=author_id,
        )
        post.publish(author_id=author_id)
        post.archive(requesting_author_id=author_id)
        
        with pytest.raises(CommentNotAllowedError):
            post.add_comment("Comentario", commenter_id=commenter_id)
    
    def test_update_post_content(self):
        """Se puede actualizar el contenido de un post en draft."""
        author_id = uuid4()
        post = PostAggregate.create(
            title=Title("Post editable"),
            content=Content("Contenido original largo " * 15),
            author_id=author_id,
        )
        
        new_content = Content("Contenido actualizado que también es largo " * 15)
        post.update_content(new_content, requesting_author_id=author_id)
        
        assert post.content.value == new_content.value
    
    def test_cannot_update_archived_post(self):
        """No se puede editar un post archivado."""
        author_id = uuid4()
        post = PostAggregate.create(
            title=Title("Post archivado"),
            content=Content("Contenido largo " * 20),
            author_id=author_id,
        )
        post.publish(author_id=author_id)
        post.archive(requesting_author_id=author_id)
        
        with pytest.raises(PostArchivedError):
            post.update_content(
                Content("Nuevo contenido largo " * 20),
                requesting_author_id=author_id
            )


class TestTitle:
    """Tests del value object Title."""
    
    def test_title_generates_slug(self):
        """Title genera slug automáticamente."""
        title = Title("Mi Título Con Espacios")
        assert title.to_slug() == "mi-titulo-con-espacios"
    
    def test_title_slug_removes_special_chars(self):
        """Slug elimina caracteres especiales."""
        title = Title("¡Título con acentos y símbolos!")
        slug = title.to_slug()
        assert slug == "titulo-con-acentos-y-simbolos"
    
    def test_empty_title_raises_error(self):
        """Título vacío lanza error."""
        with pytest.raises(ValueError):
            Title("")
    
    def test_title_too_long_raises_error(self):
        """Título muy largo lanza error."""
        with pytest.raises(ValueError):
            Title("a" * 201)


class TestContent:
    """Tests del value object Content."""
    
    def test_content_calculates_word_count(self):
        """Content calcula word_count correctamente."""
        content = Content("Este contenido tiene exactamente cinco palabras")
        assert content.word_count == 5
    
    def test_content_generates_excerpt(self):
        """Content genera excerpt de 150 caracteres."""
        long_text = "Palabra " * 50
        content = Content(long_text)
        excerpt = content.to_excerpt()
        
        assert len(excerpt) <= 153  # 150 + "..."
        assert excerpt.endswith("...")
    
    def test_short_content_excerpt_no_ellipsis(self):
        """Excerpt corto no agrega puntos suspensivos."""
        content = Content("Texto corto")
        excerpt = content.to_excerpt()
        
        assert excerpt == "Texto corto"
        assert not excerpt.endswith("...")


class TestComment:
    """Tests de la entidad Comment."""
    
    def test_create_comment(self):
        """Crear comentario genera ID y timestamp."""
        comment = Comment.create(
            body="Mi comentario",
            author_id=uuid4(),
        )
        
        assert comment.id is not None
        assert comment.body == "Mi comentario"
        assert comment.created_at is not None
    
    def test_comment_body_too_long_raises_error(self):
        """Comentario muy largo lanza error."""
        with pytest.raises(ValueError, match="1000 caracteres"):
            Comment.create(
                body="x" * 1001,
                author_id=uuid4(),
            )
    
    def test_empty_comment_raises_error(self):
        """Comentario vacío lanza error."""
        with pytest.raises(ValueError):
            Comment.create(body="", author_id=uuid4())
