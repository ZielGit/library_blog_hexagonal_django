"""
COMMAND: PublishPost
Cambia el estado de un post de DRAFT a PUBLISHED.
"""
from dataclasses import dataclass
from uuid import UUID

from src.domain.blog.repositories import PostRepository
from src.domain.blog.exceptions import PostNotFoundError
from src.domain.shared.event_bus import EventBus


@dataclass(frozen=True)
class PublishPostCommand:
    post_id: UUID
    requesting_author_id: UUID


class PublishPostCommandHandler:

    def __init__(self, repo: PostRepository, event_bus: EventBus):
        self._repo = repo
        self._event_bus = event_bus

    def handle(self, command: PublishPostCommand) -> None:
        post = self._repo.get_by_id(command.post_id)
        if post is None:
            raise PostNotFoundError(str(command.post_id))

        post.publish()  # lanza excepción si no se puede publicar

        self._repo.save(post)
        self._event_bus.publish_many(post.pull_events())
