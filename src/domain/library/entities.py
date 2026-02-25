"""
ENTIDADES del módulo Library: Book, Author, Loan.

Dominio de Biblioteca:
  - Author  → escribe libros (entidad con identidad propia)
  - Book    → tiene ISBN único, pertenece a un Author
  - Loan    → registro del préstamo de un Book a un User

Reglas de negocio:
  - Un libro no puede prestarse si no hay copias disponibles
  - Un préstamo no puede devolverse si ya fue devuelto
  - No se puede eliminar un Author con libros activos
"""
from datetime import datetime, date, timezone, timedelta
from enum import Enum
from uuid import UUID, uuid4

from src.domain.shared.base import Entity, DomainError
from src.domain.library.value_objects import ISBN, BookTitle


# ─────────────────────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────────────────────
class LoanStatus(Enum):
    ACTIVE = "active"
    RETURNED = "returned"
    OVERDUE = "overdue"


# ─────────────────────────────────────────────────────────────
# AUTHOR ENTITY
# ─────────────────────────────────────────────────────────────
class Author(Entity):
    """
    Autor de libros. Entidad independiente con su propio ciclo de vida.
    Puede tener múltiples libros asociados.
    """
    DEFAULT_LOAN_DAYS = 14

    def __init__(
        self,
        name: str,
        bio: str = "",
        author_id: UUID | None = None,
    ):
        super().__init__(author_id)
        if not name or not name.strip():
            raise DomainError("El nombre del autor no puede estar vacío.")
        if len(name) > 200:
            raise DomainError("El nombre del autor no puede exceder 200 caracteres.")

        self._name = name.strip()
        self._bio = bio
        self._created_at = datetime.now(timezone.utc)

    @property
    def name(self) -> str:
        return self._name

    @property
    def bio(self) -> str:
        return self._bio

    @property
    def created_at(self) -> datetime:
        return self._created_at

    def update_bio(self, bio: str) -> None:
        self._bio = bio

    def rename(self, new_name: str) -> None:
        if not new_name or not new_name.strip():
            raise DomainError("El nombre del autor no puede estar vacío.")
        self._name = new_name.strip()

    def __repr__(self) -> str:
        return f"Author(id={self._id}, name={self._name!r})"


# ─────────────────────────────────────────────────────────────
# BOOK ENTITY
# ─────────────────────────────────────────────────────────────
class Book(Entity):
    """
    Libro de la biblioteca.
    El ISBN es su identificador de negocio (Value Object).
    Gestiona el inventario de copias disponibles.
    """

    def __init__(
        self,
        isbn: ISBN,
        title: BookTitle,
        author_id: UUID,
        description: str = "",
        total_copies: int = 1,
        published_year: int | None = None,
        book_id: UUID | None = None,
    ):
        super().__init__(book_id)
        if total_copies < 1:
            raise DomainError("El libro debe tener al menos 1 copia.")

        self._isbn = isbn
        self._title = title
        self._author_id = author_id
        self._description = description
        self._total_copies = total_copies
        self._available_copies = total_copies
        self._published_year = published_year
        self._created_at = datetime.now(timezone.utc)

    @property
    def isbn(self) -> ISBN:
        return self._isbn

    @property
    def title(self) -> BookTitle:
        return self._title

    @property
    def author_id(self) -> UUID:
        return self._author_id

    @property
    def description(self) -> str:
        return self._description

    @property
    def total_copies(self) -> int:
        return self._total_copies

    @property
    def available_copies(self) -> int:
        return self._available_copies

    @property
    def published_year(self) -> int | None:
        return self._published_year

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def is_available(self) -> bool:
        return self._available_copies > 0

    def checkout(self) -> None:
        """Reduce las copias disponibles al prestarse."""
        if self._available_copies <= 0:
            raise DomainError(
                f"No hay copias disponibles de '{self._title.value}'."
            )
        self._available_copies -= 1

    def return_copy(self) -> None:
        """Aumenta las copias disponibles al devolverse."""
        if self._available_copies >= self._total_copies:
            raise DomainError("No se pueden devolver más copias de las prestadas.")
        self._available_copies += 1

    def add_copies(self, quantity: int) -> None:
        """Agrega copias físicas al inventario."""
        if quantity < 1:
            raise DomainError("La cantidad de copias a agregar debe ser ≥ 1.")
        self._total_copies += quantity
        self._available_copies += quantity

    def __repr__(self) -> str:
        return (
            f"Book(isbn={self._isbn.value!r}, "
            f"title={self._title.value!r}, "
            f"available={self._available_copies}/{self._total_copies})"
        )


# ─────────────────────────────────────────────────────────────
# LOAN ENTITY
# ─────────────────────────────────────────────────────────────
class Loan(Entity):
    """
    Registro de préstamo de un libro a un usuario.
    Tiene su propio ciclo de vida: ACTIVE → RETURNED (o OVERDUE).
    """
    DEFAULT_LOAN_DAYS = 14

    def __init__(
        self,
        book_id: UUID,
        user_id: UUID,
        loan_days: int = DEFAULT_LOAN_DAYS,
        loan_id: UUID | None = None,
    ):
        super().__init__(loan_id)
        self._book_id = book_id
        self._user_id = user_id
        self._loaned_at = datetime.now(timezone.utc)
        self._due_date = self._loaned_at + timedelta(days=loan_days)
        self._returned_at: datetime | None = None
        self._status = LoanStatus.ACTIVE

    @property
    def book_id(self) -> UUID:
        return self._book_id

    @property
    def user_id(self) -> UUID:
        return self._user_id

    @property
    def loaned_at(self) -> datetime:
        return self._loaned_at

    @property
    def due_date(self) -> datetime:
        return self._due_date

    @property
    def returned_at(self) -> datetime | None:
        return self._returned_at

    @property
    def status(self) -> LoanStatus:
        return self._status

    @property
    def is_active(self) -> bool:
        return self._status == LoanStatus.ACTIVE

    @property
    def is_overdue(self) -> bool:
        if self._status == LoanStatus.RETURNED:
            return False
        return datetime.now(timezone.utc) > self._due_date

    def return_book(self) -> None:
        """Registra la devolución del libro."""
        if self._status == LoanStatus.RETURNED:
            raise DomainError("Este préstamo ya fue devuelto.")
        self._returned_at = datetime.now(timezone.utc)
        self._status = LoanStatus.RETURNED

    def mark_overdue(self) -> None:
        """Marca el préstamo como vencido (llamado por tarea programada)."""
        if self._status == LoanStatus.ACTIVE and self.is_overdue:
            self._status = LoanStatus.OVERDUE

    def __repr__(self) -> str:
        return (
            f"Loan(id={self._id}, "
            f"book={self._book_id}, "
            f"user={self._user_id}, "
            f"status={self._status.value})"
        )
