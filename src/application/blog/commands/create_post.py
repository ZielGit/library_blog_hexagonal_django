"""
COMMAND: CreatePost
Crea un nuevo post en estado DRAFT.
"""
from dataclasses import dataclass, field
from uuid import UUID

from src.domain.blog.aggregates import PostAggregate
from src.domain.blog.repositories import PostRepository
from src.domain.blog.value_objects import Title, Content
from src.domain.shared.event_bus import EventBus
from src.application.dtos import PostCreatedDTO


@dataclass(frozen=True)
class CreatePostCommand:
    title: str
    content: str
    author_id: UUID
    category_id: UUID | None = None
    tags: list[str] = field(default_factory=list)


class CreatePostCommandHandler:
    """
    Orquesta la creación de un Post:
      1. Construye Value Objects (validan formato)
      2. Crea el PostAggregate (valida reglas de negocio)
      3. Persiste vía puerto
      4. Publica Domain Events
      5. Retorna DTO
    """

    def __init__(self, repo: PostRepository, event_bus: EventBus):
        self._repo = repo
        self._event_bus = event_bus

    def handle(self, command: CreatePostCommand) -> PostCreatedDTO:
        title = Title(value=command.title)
        content = Content(value=command.content)

        post = PostAggregate(
            title=title,
            content=content,
            author_id=command.author_id,
            category_id=command.category_id,
        )
        post.add_tags(command.tags)

        self._repo.save(post)
        self._event_bus.publish_many(post.pull_events())

        return PostCreatedDTO(
            id=post.id,
            slug=post.slug.value,
            title=post.title.value,
        )
