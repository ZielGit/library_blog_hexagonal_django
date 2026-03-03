"""
ADAPTADOR Django ORM → UserRepository.

Traduce entre el modelo UserModel (Django ORM) y la entidad User (dominio).
"""
from uuid import UUID
from typing import Optional

from src.domain.users.entities import User
from src.domain.users.repositories import UserRepository
from .models import UserModel


class DjangoUserRepository(UserRepository):
    """Repositorio de usuarios usando Django ORM."""

    def save(self, user: User) -> None:
        """Persiste o actualiza un usuario."""
        user_model, created = UserModel.objects.update_or_create(
            id=user.id,
            defaults={
                "email": user.email,
                "username": user.username,
                "hashed_password": user.hashed_password,
                "role": user.role.value,
                "status": user.status.value,
                "last_login": user.last_login,
            },
        )

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Busca usuario por ID."""
        try:
            user_model = UserModel.objects.get(id=user_id)
            return self._to_domain(user_model)
        except UserModel.DoesNotExist:
            return None

    def get_by_email(self, email: str) -> Optional[User]:
        """Busca usuario por email."""
        try:
            user_model = UserModel.objects.get(email=email)
            return self._to_domain(user_model)
        except UserModel.DoesNotExist:
            return None

    def get_by_username(self, username: str) -> Optional[User]:
        """Busca usuario por username."""
        try:
            user_model = UserModel.objects.get(username=username)
            return self._to_domain(user_model)
        except UserModel.DoesNotExist:
            return None

    def email_exists(self, email: str) -> bool:
        """Verifica si existe un usuario con ese email."""
        return UserModel.objects.filter(email=email).exists()

    def username_exists(self, username: str) -> bool:
        """Verifica si existe un usuario con ese username."""
        return UserModel.objects.filter(username=username).exists()

    # ── Métodos privados ───────────────────────────────────────────
    def _to_domain(self, model: UserModel) -> User:
        """
        Convierte UserModel (ORM) → User (entidad de dominio).
        User.reconstitute() es un factory method que reconstruye la entidad
        sin ejecutar validaciones de negocio (porque vienen de la BD).
        """
        return User.reconstitute(
            id=model.id,
            email=model.email,
            username=model.username,
            hashed_password=model.hashed_password,
            role=model.role,
            status=model.status,
            created_at=model.created_at,
            last_login=model.last_login,
        )
