"""
COMMANDS del módulo Library - Loans.

Commands que gestionan préstamos de libros.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from src.domain.library.entities import Loan, LoanStatus
from src.domain.library.repositories import LoanRepository, BookRepository
from src.domain.shared.base import DomainError, NotFoundError


@dataclass(frozen=True)
class CheckoutBookCommand:
    """Comando para solicitar préstamo de un libro."""
    book_id: UUID
    user_id: UUID
    due_days: int = 14  # días de préstamo por defecto


@dataclass(frozen=True)
class LoanCreatedDTO:
    """DTO con resultado de CheckoutBookCommand."""
    id: UUID
    book_id: UUID
    user_id: UUID
    checkout_date: datetime
    due_date: datetime
    status: str


class CheckoutBookCommandHandler:
    """Handler que ejecuta CheckoutBookCommand."""
    
    def __init__(self, loan_repo: LoanRepository, book_repo: BookRepository):
        self._loan_repo = loan_repo
        self._book_repo = book_repo
    
    def handle(self, command: CheckoutBookCommand) -> LoanCreatedDTO:
        """
        Crea un préstamo de libro.
        
        Raises:
            NotFoundError: Si el libro no existe.
            DomainError: Si no hay copias disponibles o datos inválidos.
        """
        # Verificar que el libro existe
        book = self._book_repo.get_by_id(command.book_id)
        if book is None:
            raise NotFoundError(f"Libro con ID {command.book_id} no encontrado")
        
        # Verificar disponibilidad
        if not book.is_available():
            raise DomainError(
                f"No hay copias disponibles del libro '{book.title.value}'. "
                f"Total: {book.total_copies}, Disponibles: {book.available_copies}"
            )
        
        # Validar días de préstamo
        if command.due_days < 1 or command.due_days > 90:
            raise DomainError("Los días de préstamo deben estar entre 1 y 90")
        
        # Verificar que el usuario no tenga préstamos vencidos
        active_loans = self._loan_repo.find_by_user_id(command.user_id)
        overdue_loans = [
            loan for loan in active_loans 
            if loan.is_overdue() and loan.status == LoanStatus.ACTIVE
        ]
        if overdue_loans:
            raise DomainError(
                f"El usuario tiene {len(overdue_loans)} préstamo(s) vencido(s). "
                "Debe devolverlos antes de solicitar nuevos préstamos."
            )
        
        # Crear préstamo
        checkout_date = datetime.now()
        due_date = checkout_date + timedelta(days=command.due_days)
        
        loan = Loan.create(
            book_id=command.book_id,
            user_id=command.user_id,
            checkout_date=checkout_date,
            due_date=due_date,
        )
        
        # Decrementar copias disponibles
        book.checkout()
        
        # Persistir ambos
        self._loan_repo.save(loan)
        self._book_repo.save(book)
        
        return LoanCreatedDTO(
            id=loan.id,
            book_id=loan.book_id,
            user_id=loan.user_id,
            checkout_date=loan.checkout_date,
            due_date=loan.due_date,
            status=loan.status.value,
        )


@dataclass(frozen=True)
class ReturnBookCommand:
    """Comando para devolver un libro prestado."""
    loan_id: UUID


class ReturnBookCommandHandler:
    """Handler que ejecuta ReturnBookCommand."""
    
    def __init__(self, loan_repo: LoanRepository, book_repo: BookRepository):
        self._loan_repo = loan_repo
        self._book_repo = book_repo
    
    def handle(self, command: ReturnBookCommand) -> None:
        """
        Marca un préstamo como devuelto.
        
        Raises:
            NotFoundError: Si el préstamo no existe.
            DomainError: Si el préstamo ya fue devuelto.
        """
        loan = self._loan_repo.get_by_id(command.loan_id)
        if loan is None:
            raise NotFoundError(f"Préstamo con ID {command.loan_id} no encontrado")
        
        if loan.status == LoanStatus.RETURNED:
            raise DomainError("Este préstamo ya fue devuelto")
        
        # Marcar como devuelto
        loan.return_book()
        
        # Incrementar copias disponibles
        book = self._book_repo.get_by_id(loan.book_id)
        if book is not None:
            book.return_copy()
            self._book_repo.save(book)
        
        self._loan_repo.save(loan)


@dataclass(frozen=True)
class RenewLoanCommand:
    """Comando para renovar un préstamo activo."""
    loan_id: UUID
    additional_days: int = 7


class RenewLoanCommandHandler:
    """Handler que ejecuta RenewLoanCommand."""
    
    def __init__(self, loan_repo: LoanRepository):
        self._repo = loan_repo
    
    def handle(self, command: RenewLoanCommand) -> None:
        """
        Renueva un préstamo extendiendo su fecha de vencimiento.
        
        Raises:
            NotFoundError: Si el préstamo no existe.
            DomainError: Si el préstamo no puede renovarse.
        """
        loan = self._repo.get_by_id(command.loan_id)
        if loan is None:
            raise NotFoundError(f"Préstamo con ID {command.loan_id} no encontrado")
        
        if loan.status != LoanStatus.ACTIVE:
            raise DomainError("Solo se pueden renovar préstamos activos")
        
        if command.additional_days < 1 or command.additional_days > 30:
            raise DomainError("Los días adicionales deben estar entre 1 y 30")
        
        # Extender fecha de vencimiento
        loan._due_date = loan.due_date + timedelta(days=command.additional_days)
        
        self._repo.save(loan)
