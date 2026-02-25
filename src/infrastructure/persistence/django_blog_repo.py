"""
ADAPTADOR Django ORM — implementa los Puertos del dominio.

Este es el único lugar donde coexisten:
  - Código de dominio (Entities, Value Objects)
  - Código de Django (ORM queries)

Responsabilidad: traducir entre el mundo del dominio y el mundo de Django.
  dominio → ORM : método _to_model()
  ORM → dominio : método _to_domain()

Si mañana cambiamos a SQLAlchemy o MongoDB, solo cambia este archivo.
"""
from uuid import UUID

from src.domain.blog.aggregates import PostAggregate
from src.domain.blog.entities import PostStatus, Comment
from src.domain.blog.repositories import PostRepository, PostReadRepository
from src.domain.blog.value_objects import Title, Content
from .models import PostModel, CommentModel


class DjangoPostRepository(PostRepository, PostReadRepository):
    """
    Adaptador de persistencia usando Django ORM.
    Implementa AMBAS interfaces (write + read) — en un proyecto grande
    podrías separarlas en dos clases distintas con modelos de lectura
    optimizados (ej: vistas desnormalizadas en Postgres).
    """

    # ── PostRepository (write) ───────────────────────────────
    def save(self, post: PostAggregate) -> None:
        """Upsert: crea o actualiza según exista el id."""
        # Guardar post principal
        post_model, _ = PostModel.objects.update_or_create(
            id=post.id,
            defaults=self._to_model_dict(post),
        )

        # Sincronizar comentarios (estrategia simple: recrear)
        # En producción considera un diff incremental
        existing_ids = set(
            CommentModel.objects.filter(post=post_model)
            .values_list("id", flat=True)
        )
        domain_ids = {c.id for c in post.comments}

        # Eliminar comentarios que ya no están en el agregado
        to_delete = existing_ids - domain_ids
        CommentModel.objects.filter(id__in=to_delete).delete()

        # Crear comentarios nuevos
        for comment in post.comments:
            if comment.id not in existing_ids:
                CommentModel.objects.create(
                    id=comment.id,
                    post=post_model,
                    body=comment.body,
                    author_id=comment.author_id,
                    created_at=comment.created_at,
                )

    def get_by_id(self, post_id: UUID) -> PostAggregate | None:
        try:
            model = PostModel.objects.prefetch_related("comments").get(id=post_id)
            return self._to_domain(model)
        except PostModel.DoesNotExist:
            return None

    def delete(self, post_id: UUID) -> None:
        PostModel.objects.filter(id=post_id).delete()

    # ── PostReadRepository (read) ────────────────────────────
    def find_by_slug(self, slug: str) -> PostAggregate | None:
        try:
            model = PostModel.objects.prefetch_related("comments").get(slug=slug)
            return self._to_domain(model)
        except PostModel.DoesNotExist:
            return None

    def find_published(
        self,
        page: int = 1,
        page_size: int = 10,
        tag: str | None = None,
    ) -> tuple[list[PostAggregate], int]:
        qs = PostModel.objects.filter(status="published").order_by("-published_at")

        if tag:
            # Filtra posts cuyo array JSON de tags contiene el tag
            qs = qs.filter(tags__contains=[tag.lower()])

        total = qs.count()
        start = (page - 1) * page_size
        models = qs.prefetch_related("comments")[start : start + page_size]
        return [self._to_domain(m) for m in models], total

    def find_by_author(
        self,
        author_id: UUID,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[PostAggregate], int]:
        qs = PostModel.objects.filter(author_id=author_id).order_by("-created_at")
        total = qs.count()
        start = (page - 1) * page_size
        models = qs.prefetch_related("comments")[start : start + page_size]
        return [self._to_domain(m) for m in models], total

    def slug_exists(self, slug: str) -> bool:
        return PostModel.objects.filter(slug=slug).exists()

    # ── Métodos de traducción ────────────────────────────────
    @staticmethod
    def _to_model_dict(post: PostAggregate) -> dict:
        """Convierte PostAggregate → dict para Django ORM."""
        return {
            "title": post.title.value,
            "slug": post.slug.value,
            "content": post.content.value,
            "status": post.status.value,
            "author_id": post.author_id,
            "tags": post.tags,
            "published_at": post.published_at,
        }

    @staticmethod
    def _to_domain(model: PostModel) -> PostAggregate:
        """Convierte PostModel (ORM) → PostAggregate (dominio)."""
        comments = [
            Comment(
                body=c.body,
                author_id=c.author_id,
                comment_id=c.id,
            )
            for c in model.comments.all()
        ]
        # Corregir el created_at de los comments desde el modelo
        for i, c_model in enumerate(model.comments.all()):
            comments[i]._created_at = c_model.created_at

        return PostAggregate.reconstitute(
            post_id=model.id,
            title=Title(value=model.title),
            content=Content(value=model.content),
            author_id=model.author_id,
            status=PostStatus(model.status),
            created_at=model.created_at,
            published_at=model.published_at,
            tags=model.tags or [],
            comments=comments,
        )
