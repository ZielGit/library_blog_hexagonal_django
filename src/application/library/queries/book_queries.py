"""Queries del módulo Library - Books"""
from dataclasses import dataclass
from uuid import UUID

from src.domain.library.repositories import BookReadRepository


@dataclass(frozen=True)
class BookDTO:
    id: UUID
    isbn: str
    title: str
    author_id: UUID
    available_copies: int
    total_copies: int


@dataclass(frozen=True)
class ListAvailableBooksQuery:
    pass


class ListAvailableBooksQueryHandler:
    def __init__(self, repo: BookReadRepository):
        self._repo = repo

    def handle(self, query: ListAvailableBooksQuery) -> list[BookDTO]:
        books = self._repo.find_available()
        return [
            BookDTO(
                id=b.id,
                isbn=b.isbn.value,
                title=b.title.value,
                author_id=b.author_id,
                available_copies=b.available_copies,
                total_copies=b.total_copies,
            )
            for b in books
        ]
