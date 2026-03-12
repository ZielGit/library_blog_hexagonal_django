"""
COMMANDS del módulo Library - Books.

Commands que modifican el estado de los libros.
"""
from dataclasses import dataclass
from uuid import UUID

from src.domain.library.entities import Book
from src.domain.library.value_objects import ISBN, BookTitle
from src.domain.library.repositories import BookRepository, AuthorRepository
from src.domain.shared.base import DomainError, NotFoundError


@dataclass(frozen=True)
class CreateBookCommand:
    """Comando para crear un nuevo libro."""
    isbn: str
    title: str
    author_id: UUID
    description: str = ""
    total_copies: int = 1
    published_year: int | None = None


@dataclass(frozen=True)
class BookCreatedDTO:
    """DTO con resultado de CreateBookCommand."""
    id: UUID
    isbn: str
    title: str
    author_name: str


class CreateBookCommandHandler:
    """Handler que ejecuta CreateBookCommand."""
    
    def __init__(self, book_repo: BookRepository, author_repo: AuthorRepository):
        self._book_repo = book_repo
        self._author_repo = author_repo
    
    def handle(self, command: CreateBookCommand) -> BookCreatedDTO:
        """
        Crea un nuevo libro en el sistema.
        
        Raises:
            NotFoundError: Si el autor no existe.
            DomainError: Si el ISBN ya existe o datos inválidos.
        """
        # Verificar que el autor existe
        author = self._author_repo.get_by_id(command.author_id)
        if author is None:
            raise NotFoundError(f"Autor con ID {command.author_id} no encontrado")
        
        # Verificar que el ISBN no existe
        existing = self._book_repo.get_by_isbn(command.isbn)
        if existing is not None:
            raise DomainError(f"Ya existe un libro con ISBN {command.isbn}")
        
        if command.total_copies < 1:
            raise DomainError("El total de copias debe ser al menos 1")
        
        # Crear entidad de dominio
        book = Book.create(
            isbn=ISBN(command.isbn),
            title=BookTitle(command.title),
            author_id=command.author_id,
            total_copies=command.total_copies,
            description=command.description,
            published_year=command.published_year,
        )
        
        # Persistir
        self._book_repo.save(book)
        
        return BookCreatedDTO(
            id=book.id,
            isbn=book.isbn.value,
            title=book.title.value,
            author_name=author.name,
        )


@dataclass(frozen=True)
class AddBookCopiesCommand:
    """Comando para agregar copias de un libro existente."""
    book_id: UUID
    copies_to_add: int


class AddBookCopiesCommandHandler:
    """Handler que ejecuta AddBookCopiesCommand."""
    
    def __init__(self, book_repo: BookRepository):
        self._repo = book_repo
    
    def handle(self, command: AddBookCopiesCommand) -> None:
        """
        Agrega copias a un libro existente.
        
        Raises:
            NotFoundError: Si el libro no existe.
            DomainError: Si la cantidad es inválida.
        """
        book = self._repo.get_by_id(command.book_id)
        if book is None:
            raise NotFoundError(f"Libro con ID {command.book_id} no encontrado")
        
        if command.copies_to_add < 1:
            raise DomainError("Debe agregar al menos 1 copia")
        
        book.add_copies(command.copies_to_add)
        self._repo.save(book)
