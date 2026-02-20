"""
DOMAIN EVENTS del módulo Blog.

Los eventos representan hechos del pasado que ya ocurrieron.
Otros módulos pueden reaccionar a ellos sin acoplarse al Blog.

Convención de nombres: Sustantivo + Participio pasado
  ✅ PostPublished, CommentAdded, PostDeleted
  ❌ PublishPost, AddComment  ← esos son Commands, no Events
"""
from dataclasses import dataclass, field
from uuid import UUID

from src.domain.shared.base import DomainEvent


@dataclass(frozen=True)
class PostCreated(DomainEvent):
    """Se emite cuando un Post es creado por primera vez (en borrador)."""
    post_id: UUID = field(default=None)
    author_id: UUID = field(default=None)
    title: str = field(default="")


@dataclass(frozen=True)
class PostPublished(DomainEvent):
    """Se emite cuando un Post pasa de DRAFT a PUBLISHED."""
    post_id: UUID = field(default=None)
    slug: str = field(default="")


@dataclass(frozen=True)
class PostArchived(DomainEvent):
    """Se emite cuando un Post es archivado."""
    post_id: UUID = field(default=None)


@dataclass(frozen=True)
class CommentAdded(DomainEvent):
    """Se emite cuando un comentario es añadido a un post."""
    post_id: UUID = field(default=None)
    comment_id: UUID = field(default=None)
    author_id: UUID = field(default=None)


@dataclass(frozen=True)
class PostUpdated(DomainEvent):
    """Se emite cuando el contenido de un Post es actualizado."""
    post_id: UUID = field(default=None)
    new_title: str = field(default="")
