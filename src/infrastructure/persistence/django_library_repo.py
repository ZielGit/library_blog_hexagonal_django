"""
ADAPTADOR Django ORM para el módulo Library.
Implementa BookRepository, AuthorRepository y LoanRepository.
"""
from uuid import UUID

from src.domain.library.entities import Book, Author, Loan, LoanStatus
from src.domain.library.repositories import (
    BookRepository, BookReadRepository,
    AuthorRepository, LoanRepository,
)
from src.domain.library.value_objects import ISBN, BookTitle
from src.infrastructure.persistence.models import BookModel, AuthorModel, LoanModel


class DjangoBookRepository(BookRepository, BookReadRepository):

    def save(self, book: Book) -> None:
        author_model = AuthorModel.objects.get(id=book.author_id)
        BookModel.objects.update_or_create(
            id=book.id,
            defaults={
                "isbn": book.isbn.value,
                "title": book.title.value,
                "author": author_model,
                "description": book.description,
                "total_copies": book.total_copies,
                "available_copies": book.available_copies,
                "published_year": book.published_year,
            }
        )

    def get_by_id(self, book_id: UUID) -> Book | None:
        try:
            return self._to_domain(BookModel.objects.select_related("author").get(id=book_id))
        except BookModel.DoesNotExist:
            return None

    def get_by_isbn(self, isbn: str) -> Book | None:
        try:
            return self._to_domain(BookModel.objects.select_related("author").get(isbn=isbn))
        except BookModel.DoesNotExist:
            return None

    def delete(self, book_id: UUID) -> None:
        BookModel.objects.filter(id=book_id).delete()

    def find_available(self, page: int = 1, page_size: int = 10) -> tuple[list[Book], int]:
        qs = BookModel.objects.filter(available_copies__gt=0).order_by("title")
        total = qs.count()
        start = (page - 1) * page_size
        return [self._to_domain(m) for m in qs[start:start + page_size]], total

    def find_by_author(self, author_id: UUID) -> list[Book]:
        return [
            self._to_domain(m)
            for m in BookModel.objects.filter(author_id=author_id)
        ]

    def search(self, query: str, page: int = 1, page_size: int = 10) -> tuple[list[Book], int]:
        qs = BookModel.objects.filter(title__icontains=query).order_by("title")
        total = qs.count()
        start = (page - 1) * page_size
        return [self._to_domain(m) for m in qs[start:start + page_size]], total

    @staticmethod
    def _to_domain(model: BookModel) -> Book:
        book = Book.__new__(Book)
        from src.domain.shared.base import Entity
        Entity.__init__(book, model.id)
        book._isbn = ISBN(value=model.isbn)
        book._title = BookTitle(value=model.title)
        book._author_id = model.author_id
        book._description = model.description
        book._total_copies = model.total_copies
        book._available_copies = model.available_copies
        book._published_year = model.published_year
        book._created_at = model.created_at
        return book


class DjangoAuthorRepository(AuthorRepository):

    def save(self, author: Author) -> None:
        AuthorModel.objects.update_or_create(
            id=author.id,
            defaults={"name": author.name, "bio": author.bio}
        )

    def get_by_id(self, author_id: UUID) -> Author | None:
        try:
            m = AuthorModel.objects.get(id=author_id)
            return self._to_domain(m)
        except AuthorModel.DoesNotExist:
            return None

    def find_all(self, page: int = 1, page_size: int = 10) -> tuple[list[Author], int]:
        qs = AuthorModel.objects.order_by("name")
        total = qs.count()
        start = (page - 1) * page_size
        return [self._to_domain(m) for m in qs[start:start + page_size]], total

    def delete(self, author_id: UUID) -> None:
        AuthorModel.objects.filter(id=author_id).delete()

    @staticmethod
    def _to_domain(model: AuthorModel) -> Author:
        author = Author.__new__(Author)
        from src.domain.shared.base import Entity
        Entity.__init__(author, model.id)
        author._name = model.name
        author._bio = model.bio
        author._created_at = model.created_at
        return author


class DjangoLoanRepository(LoanRepository):

    def save(self, loan: Loan) -> None:
        LoanModel.objects.update_or_create(
            id=loan.id,
            defaults={
                "book_id": loan.book_id,
                "user_id": loan.user_id,
                "loaned_at": loan.loaned_at,
                "due_date": loan.due_date,
                "returned_at": loan.returned_at,
                "status": loan.status.value,
            }
        )

    def get_by_id(self, loan_id: UUID) -> Loan | None:
        try:
            return self._to_domain(LoanModel.objects.get(id=loan_id))
        except LoanModel.DoesNotExist:
            return None

    def find_active_by_user(self, user_id: UUID) -> list[Loan]:
        return [
            self._to_domain(m)
            for m in LoanModel.objects.filter(user_id=user_id, status="active")
        ]

    def find_overdue(self) -> list[Loan]:
        from django.utils import timezone
        return [
            self._to_domain(m)
            for m in LoanModel.objects.filter(
                status="active",
                due_date__lt=timezone.now()
            )
        ]

    @staticmethod
    def _to_domain(model: "LoanModel") -> Loan:
        loan = Loan.__new__(Loan)
        from src.domain.shared.base import Entity
        Entity.__init__(loan, model.id)
        loan._book_id = model.book_id
        loan._user_id = model.user_id
        loan._loaned_at = model.loaned_at
        loan._due_date = model.due_date
        loan._returned_at = model.returned_at
        loan._status = LoanStatus(model.status)
        return loan
