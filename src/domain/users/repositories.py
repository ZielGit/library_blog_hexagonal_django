"""
PUERTOS del módulo Users.
"""
from abc import ABC, abstractmethod
from uuid import UUID
from src.domain.users.entities import User


class UserRepository(ABC):

    @abstractmethod
    def save(self, user: User) -> None: ...

    @abstractmethod
    def get_by_id(self, user_id: UUID) -> User | None: ...

    @abstractmethod
    def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    def get_by_username(self, username: str) -> User | None: ...

    @abstractmethod
    def email_exists(self, email: str) -> bool: ...

    @abstractmethod
    def username_exists(self, username: str) -> bool: ...


class PasswordHasher(ABC):
    """Puerto para hashear y verificar contraseñas."""

    @abstractmethod
    def hash(self, plain_password: str) -> str: ...

    @abstractmethod
    def verify(self, plain_password: str, hashed_password: str) -> bool: ...


class TokenService(ABC):
    """Puerto para generar y verificar JWT tokens."""

    @abstractmethod
    def generate_access_token(self, user_id: UUID, role: str) -> str: ...

    @abstractmethod
    def generate_refresh_token(self, user_id: UUID) -> str: ...

    @abstractmethod
    def verify_token(self, token: str) -> dict | None: ...
