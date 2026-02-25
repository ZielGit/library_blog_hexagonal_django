"""
PUERTOS del módulo Library.

Interfaces que definen qué operaciones de persistencia necesita
el dominio, sin saber cómo se implementan.
"""
from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.library.entities import Book, Author, Loan


class BookRepository(ABC):
    """Puerto de escritura para libros."""

    @abstractmethod
    def save(self, book: Book) -> None: ...

    @abstractmethod
    def get_by_id(self, book_id: UUID) -> Book | None: ...

    @abstractmethod
    def get_by_isbn(self, isbn: str) -> Book | None: ...

    @abstractmethod
    def delete(self, book_id: UUID) -> None: ...


class BookReadRepository(ABC):
    """Puerto de lectura para libros (CQRS)."""

    @abstractmethod
    def find_available(self, page: int = 1, page_size: int = 10) -> tuple[list[Book], int]: ...

    @abstractmethod
    def find_by_author(self, author_id: UUID) -> list[Book]: ...

    @abstractmethod
    def search(self, query: str, page: int = 1, page_size: int = 10) -> tuple[list[Book], int]: ...


class AuthorRepository(ABC):
    """Puerto para autores."""

    @abstractmethod
    def save(self, author: Author) -> None: ...

    @abstractmethod
    def get_by_id(self, author_id: UUID) -> Author | None: ...

    @abstractmethod
    def find_all(self, page: int = 1, page_size: int = 10) -> tuple[list[Author], int]: ...

    @abstractmethod
    def delete(self, author_id: UUID) -> None: ...


class LoanRepository(ABC):
    """Puerto para préstamos."""

    @abstractmethod
    def save(self, loan: Loan) -> None: ...

    @abstractmethod
    def get_by_id(self, loan_id: UUID) -> Loan | None: ...

    @abstractmethod
    def find_active_by_user(self, user_id: UUID) -> list[Loan]: ...

    @abstractmethod
    def find_overdue(self) -> list[Loan]: ...
