"""
COMMAND: AddComment
Añade un comentario a un post existente.
"""
from dataclasses import dataclass
from uuid import UUID

from src.domain.blog.repositories import PostRepository
from src.domain.blog.exceptions import PostNotFoundError
from src.domain.shared.event_bus import EventBus
from src.application.dtos import CommentDTO


@dataclass(frozen=True)
class AddCommentCommand:
    post_id: UUID
    body: str
    commenter_id: UUID


class AddCommentCommandHandler:

    def __init__(self, repo: PostRepository, event_bus: EventBus):
        self._repo = repo
        self._event_bus = event_bus

    def handle(self, command: AddCommentCommand) -> CommentDTO:
        post = self._repo.get_by_id(command.post_id)
        if post is None:
            raise PostNotFoundError(str(command.post_id))

        comment = post.add_comment(
            body=command.body,
            commenter_id=command.commenter_id,
        )
        self._repo.save(post)
        self._event_bus.publish_many(post.pull_events())

        return CommentDTO(
            id=comment.id,
            body=comment.body,
            author_id=comment.author_id,
            created_at=comment.created_at,
        )
