"""
QUERIES del módulo Users.

Queries son operaciones de solo lectura que retornan DTOs.
No modifican estado — ideal para separación CQRS.
"""
from dataclasses import dataclass
from uuid import UUID

from src.domain.users.repositories import UserRepository


# ═══════════════════════════════════════════════════════════════
# DTOs
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class UserProfileDTO:
    """DTO con información completa del perfil de usuario."""
    id: UUID
    email: str
    username: str
    role: str
    status: str
    permissions: list[str]
    created_at: str  # ISO format
    last_login: str | None  # ISO format


# ═══════════════════════════════════════════════════════════════
# QUERY: GetUserProfile
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class GetUserProfileQuery:
    """Query para obtener el perfil de un usuario por ID."""
    user_id: UUID


class GetUserProfileQueryHandler:
    """
    Handler para GetUserProfileQuery.
    
    Uso típico: endpoint /api/auth/me/ que retorna el perfil del usuario logueado.
    """

    def __init__(self, user_repo: UserRepository):
        self._repo = user_repo

    def handle(self, query: GetUserProfileQuery) -> UserProfileDTO | None:
        user = self._repo.get_by_id(query.user_id)
        if user is None:
            return None

        return UserProfileDTO(
            id=user.id,
            email=user.email,
            username=user.username,
            role=user.role.value,
            status=user.status.value,
            permissions=sorted(user.permissions()),
            created_at=user.created_at.isoformat(),
            last_login=user.last_login.isoformat() if user.last_login else None,
        )
