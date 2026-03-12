"""Commands completos para Library module"""
from dataclasses import dataclass
from uuid import UUID
from datetime import datetime, timedelta, timezone

from src.domain.library.entities import Book, Author, Loan
from src.domain.library.value_objects import ISBN, BookTitle
from src.domain.library.repositories import (
    BookRepository, AuthorRepository, LoanRepository
)


# AUTHOR COMMANDS
@dataclass(frozen=True)
class CreateAuthorCommand:
    name: str
    bio: str = ""

class CreateAuthorCommandHandler:
    def __init__(self, repo: AuthorRepository):
        self._repo = repo
    def handle(self, cmd: CreateAuthorCommand) -> Author:
        author = Author(name=cmd.name, bio=cmd.bio)
        self._repo.save(author)
        return author


# BOOK COMMANDS
@dataclass(frozen=True)
class CreateBookCommand:
    isbn: str
    title: str
    author_id: UUID
    total_copies: int = 1

class CreateBookCommandHandler:
    def __init__(self, repo: BookRepository, author_repo: AuthorRepository):
        self._repo = repo
        self._author_repo = author_repo
    def handle(self, cmd: CreateBookCommand) -> Book:
        if not self._author_repo.get_by_id(cmd.author_id):
            raise ValueError("Author not found")
        book = Book(
            isbn=ISBN(cmd.isbn),
            title=BookTitle(cmd.title),
            author_id=cmd.author_id,
            total_copies=cmd.total_copies,
            available_copies=cmd.total_copies,
        )
        self._repo.save(book)
        return book


# LOAN COMMANDS
@dataclass(frozen=True)
class CheckoutBookCommand:
    book_id: UUID
    user_id: UUID

class CheckoutBookCommandHandler:
    def __init__(self, book_repo: BookRepository, loan_repo: LoanRepository):
        self._book_repo = book_repo
        self._loan_repo = loan_repo
    def handle(self, cmd: CheckoutBookCommand) -> Loan:
        book = self._book_repo.get_by_id(cmd.book_id)
        if not book or book.available_copies <= 0:
            raise ValueError("Book not available")
        book.checkout()
        self._book_repo.save(book)
        now = datetime.now(timezone.utc)
        loan = Loan(
            book_id=cmd.book_id,
            user_id=cmd.user_id,
            loaned_at=now,
            due_date=now + timedelta(days=14),
        )
        self._loan_repo.save(loan)
        return loan

@dataclass(frozen=True)
class ReturnBookCommand:
    loan_id: UUID

class ReturnBookCommandHandler:
    def __init__(self, book_repo: BookRepository, loan_repo: LoanRepository):
        self._book_repo = book_repo
        self._loan_repo = loan_repo
    def handle(self, cmd: ReturnBookCommand):
        loan = self._loan_repo.get_by_id(cmd.loan_id)
        if not loan or loan.status == "returned":
            raise ValueError("Invalid loan")
        book = self._book_repo.get_by_id(loan.book_id)
        if book:
            book.return_copy()
            self._book_repo.save(book)
        loan.return_book()
        self._loan_repo.save(loan)
