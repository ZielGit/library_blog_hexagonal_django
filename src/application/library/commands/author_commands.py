"""
COMMANDS del módulo Library - Authors.

Commands que modifican el estado de los autores.
"""
from dataclasses import dataclass
from uuid import UUID

from src.domain.library.entities import Author
from src.domain.library.repositories import AuthorRepository
from src.domain.shared.base import DomainError


@dataclass(frozen=True)
class CreateAuthorCommand:
    """Comando para crear un nuevo autor."""
    name: str
    biography: str = ""
    birth_year: int | None = None


@dataclass(frozen=True)
class AuthorCreatedDTO:
    """DTO con resultado de CreateAuthorCommand."""
    id: UUID
    name: str


class CreateAuthorCommandHandler:
    """Handler que ejecuta CreateAuthorCommand."""
    
    def __init__(self, author_repo: AuthorRepository):
        self._repo = author_repo
    
    def handle(self, command: CreateAuthorCommand) -> AuthorCreatedDTO:
        """
        Crea un nuevo autor en el sistema.
        
        Raises:
            DomainError: Si el nombre está vacío o es inválido.
        """
        if not command.name or len(command.name.strip()) < 2:
            raise DomainError("El nombre del autor debe tener al menos 2 caracteres")
        
        # Crear entidad de dominio
        author = Author.create(
            name=command.name.strip(),
            biography=command.biography.strip(),
            birth_year=command.birth_year,
        )
        
        # Persistir
        self._repo.save(author)
        
        return AuthorCreatedDTO(
            id=author.id,
            name=author.name,
        )


@dataclass(frozen=True)
class UpdateAuthorCommand:
    """Comando para actualizar un autor existente."""
    author_id: UUID
    name: str | None = None
    biography: str | None = None
    birth_year: int | None = None


class UpdateAuthorCommandHandler:
    """Handler que ejecuta UpdateAuthorCommand."""
    
    def __init__(self, author_repo: AuthorRepository):
        self._repo = author_repo
    
    def handle(self, command: UpdateAuthorCommand) -> None:
        """
        Actualiza un autor existente.
        
        Raises:
            NotFoundError: Si el autor no existe.
            DomainError: Si los datos son inválidos.
        """
        from src.domain.shared.base import NotFoundError
        
        author = self._repo.get_by_id(command.author_id)
        if author is None:
            raise NotFoundError(f"Autor con ID {command.author_id} no encontrado")
        
        # Actualizar campos si fueron provistos
        if command.name is not None:
            if len(command.name.strip()) < 2:
                raise DomainError("El nombre debe tener al menos 2 caracteres")
            author._name = command.name.strip()
        
        if command.biography is not None:
            author._biography = command.biography.strip()
        
        if command.birth_year is not None:
            author._birth_year = command.birth_year
        
        self._repo.save(author)
