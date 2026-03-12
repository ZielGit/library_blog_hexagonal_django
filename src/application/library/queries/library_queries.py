"""QUERIES del módulo Library - solo lectura"""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.domain.library.repositories import BookRepository, AuthorRepository, LoanRepository


@dataclass(frozen=True)
class AuthorDTO:
    id: UUID
    name: str
    biography: str
    birth_year: int | None
    books_count: int


@dataclass(frozen=True)
class BookSummaryDTO:
    id: UUID
    isbn: str
    title: str
    author_id: UUID
    author_name: str
    total_copies: int
    available_copies: int
    published_year: int | None


@dataclass(frozen=True)
class BookDetailDTO:
    id: UUID
    isbn: str
    title: str
    author_id: UUID
    author_name: str
    description: str
    total_copies: int
    available_copies: int
    published_year: int | None


@dataclass(frozen=True)
class LoanDTO:
    id: UUID
    book_id: UUID
    book_title: str
    user_id: UUID
    checkout_date: datetime
    due_date: datetime
    return_date: datetime | None
    status: str
    is_overdue: bool


@dataclass(frozen=True)
class ListAuthorsQuery:
    page: int = 1
    page_size: int = 20


class ListAuthorsQueryHandler:
    def __init__(self, author_repo: AuthorRepository, book_repo: BookRepository):
        self._author_repo = author_repo
        self._book_repo = book_repo
    
    def handle(self, query: ListAuthorsQuery) -> list[AuthorDTO]:
        authors = self._author_repo.list_all()
        result = []
        for author in authors:
            books = self._book_repo.find_by_author_id(author.id)
            result.append(AuthorDTO(
                id=author.id,
                name=author.name,
                biography=author.biography,
                birth_year=author.birth_year,
                books_count=len(books),
            ))
        start = (query.page - 1) * query.page_size
        end = start + query.page_size
        return result[start:end]


@dataclass(frozen=True)
class ListAvailableBooksQuery:
    page: int = 1
    page_size: int = 20


class ListAvailableBooksQueryHandler:
    def __init__(self, book_repo: BookRepository, author_repo: AuthorRepository):
        self._book_repo = book_repo
        self._author_repo = author_repo
    
    def handle(self, query: ListAvailableBooksQuery) -> list[BookSummaryDTO]:
        books = self._book_repo.find_available()
        result = []
        for book in books:
            author = self._author_repo.get_by_id(book.author_id)
            result.append(BookSummaryDTO(
                id=book.id,
                isbn=book.isbn.value,
                title=book.title.value,
                author_id=book.author_id,
                author_name=author.name if author else "Desconocido",
                total_copies=book.total_copies,
                available_copies=book.available_copies,
                published_year=book.published_year,
            ))
        start = (query.page - 1) * query.page_size
        end = start + query.page_size
        return result[start:end]


@dataclass(frozen=True)
class ListUserLoansQuery:
    user_id: UUID


class ListUserLoansQueryHandler:
    def __init__(self, loan_repo: LoanRepository, book_repo: BookRepository):
        self._loan_repo = loan_repo
        self._book_repo = book_repo
    
    def handle(self, query: ListUserLoansQuery) -> list[LoanDTO]:
        loans = self._loan_repo.find_by_user_id(query.user_id)
        result = []
        for loan in loans:
            book = self._book_repo.get_by_id(loan.book_id)
            result.append(LoanDTO(
                id=loan.id,
                book_id=loan.book_id,
                book_title=book.title.value if book else "Libro eliminado",
                user_id=loan.user_id,
                checkout_date=loan.checkout_date,
                due_date=loan.due_date,
                return_date=loan.return_date,
                status=loan.status.value,
                is_overdue=loan.is_overdue(),
            ))
        return result
