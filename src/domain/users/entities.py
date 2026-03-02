"""
ENTIDADES del módulo Users.

El módulo de usuarios gestiona:
  - User: la identidad del usuario en el sistema
  - Role: colección de permisos (ADMIN, EDITOR, READER)
  - Permission: una acción específica permitida

Decisión de diseño: usamos roles basados en strings en lugar
de un modelo de permisos complejo. Para sistemas más grandes
considera RBAC (Role-Based Access Control) con una librería dedicada.
"""
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from src.domain.shared.base import Entity, DomainError


# ─────────────────────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────────────────────
class UserRole(Enum):
    """
    Roles del sistema. Cada rol agrupa un conjunto de permisos.
    Sigue el principio de menor privilegio.
    """
    ADMIN = "admin"      # Acceso total: CRUD en todo
    EDITOR = "editor"    # Puede crear/publicar/archivar posts y libros
    READER = "reader"    # Solo lectura + puede comentar


class UserStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BANNED = "banned"


# ─────────────────────────────────────────────────────────────
# PERMISSION VALUE OBJECT
# ─────────────────────────────────────────────────────────────
ROLE_PERMISSIONS: dict[UserRole, set[str]] = {
    UserRole.ADMIN: {
        "post:create", "post:publish", "post:archive", "post:delete",
        "comment:create", "comment:delete",
        "user:manage", "user:ban",
        "book:create", "book:edit", "book:delete",
        "loan:create", "loan:manage",
    },
    UserRole.EDITOR: {
        "post:create", "post:publish", "post:archive",
        "comment:create",
        "book:create", "book:edit",
        "loan:create",
    },
    UserRole.READER: {
        "comment:create",
        "loan:create",
    },
}


# ─────────────────────────────────────────────────────────────
# USER ENTITY
# ─────────────────────────────────────────────────────────────
class User(Entity):
    """
    Usuario del sistema. Tiene un rol que determina sus permisos.

    Reglas de negocio:
      - Un admin no puede banearse a sí mismo
      - Un usuario baneado no puede autenticarse
      - El email debe ser único en el sistema
    """

    def __init__(
        self,
        email: str,
        username: str,
        hashed_password: str,
        role: UserRole = UserRole.READER,
        user_id: UUID | None = None,
    ):
        super().__init__(user_id)
        self._validate_email(email)
        self._validate_username(username)

        self._email = email.lower().strip()
        self._username = username.strip()
        self._hashed_password = hashed_password
        self._role = role
        self._status = UserStatus.ACTIVE
        self._created_at = datetime.now(timezone.utc)
        self._last_login: datetime | None = None

    # ── Validaciones ────────────────────────────────────────
    @staticmethod
    def _validate_email(email: str) -> None:
        import re
        if not email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            raise DomainError(f"Email inválido: '{email}'.")

    @staticmethod
    def _validate_username(username: str) -> None:
        import re
        if not username or len(username.strip()) < 3:
            raise DomainError("El username debe tener al menos 3 caracteres.")
        if len(username) > 50:
            raise DomainError("El username no puede exceder 50 caracteres.")
        if not re.match(r"^[a-zA-Z0-9_.-]+$", username):
            raise DomainError(
                "El username solo puede contener letras, números, _, -, y ."
            )

    # ── Propiedades ──────────────────────────────────────────
    @property
    def email(self) -> str:
        return self._email

    @property
    def username(self) -> str:
        return self._username

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    @property
    def role(self) -> UserRole:
        return self._role

    @property
    def status(self) -> UserStatus:
        return self._status

    @property
    def is_active(self) -> bool:
        return self._status == UserStatus.ACTIVE

    @property
    def is_authenticated(self) -> bool:
        """
        Propiedad requerida por Django REST Framework.
        Siempre retorna True porque si llegamos aquí es porque
        el token ya fue verificado exitosamente.
        """
        return True

    @property
    def is_anonymous(self) -> bool:
        """
        Propiedad requerida por Django REST Framework.
        Siempre retorna False (inverso de is_authenticated).
        """
        return False

    @property
    def is_admin(self) -> bool:
        return self._role == UserRole.ADMIN

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def last_login(self) -> datetime | None:
        return self._last_login

    # ── Permisos ────────────────────────────────────────────
    def has_permission(self, permission: str) -> bool:
        """Verifica si el usuario tiene un permiso específico."""
        if self._status != UserStatus.ACTIVE:
            return False
        return permission in ROLE_PERMISSIONS.get(self._role, set())

    def can(self, permission: str) -> bool:
        """Alias legible de has_permission."""
        return self.has_permission(permission)

    def permissions(self) -> set[str]:
        """Retorna todos los permisos del rol del usuario."""
        return ROLE_PERMISSIONS.get(self._role, set()).copy()

    # ── Comandos de dominio ───────────────────────────────────
    def change_role(self, new_role: UserRole, changed_by: "User") -> None:
        """Solo un ADMIN puede cambiar roles."""
        if not changed_by.is_admin:
            raise DomainError("Solo un administrador puede cambiar roles.")
        self._role = new_role

    def ban(self, banned_by: "User") -> None:
        """Banea al usuario. Un admin no puede banearse a sí mismo."""
        if not banned_by.is_admin:
            raise DomainError("Solo un administrador puede banear usuarios.")
        if banned_by.id == self._id:
            raise DomainError("Un administrador no puede banearse a sí mismo.")
        if self._status == UserStatus.BANNED:
            raise DomainError("El usuario ya está baneado.")
        self._status = UserStatus.BANNED

    def activate(self) -> None:
        self._status = UserStatus.ACTIVE

    def record_login(self) -> None:
        """Registra el momento del último login."""
        self._last_login = datetime.now(timezone.utc)

    def change_password(self, new_hashed_password: str) -> None:
        if not new_hashed_password:
            raise DomainError("La contraseña no puede estar vacía.")
        self._hashed_password = new_hashed_password

    def __repr__(self) -> str:
        return f"User(id={self._id}, email={self._email!r}, role={self._role.value})"

    # ── Factory para reconstrucción desde persistencia ─────────
    @classmethod
    def reconstitute(
        cls,
        id: UUID,
        email: str,
        username: str,
        hashed_password: str,
        role: str,
        status: str,
        created_at: datetime,
        last_login: datetime | None,
    ) -> "User":
        """
        Reconstruye una entidad User desde la persistencia sin validaciones.
        Usado por el repositorio al hidratar desde la base de datos.
        """
        user = cls.__new__(cls)  # crea instancia sin llamar __init__
        user._id = id
        user._email = email
        user._username = username
        user._hashed_password = hashed_password
        user._role = UserRole(role)
        user._status = UserStatus(status)
        user._created_at = created_at
        user._last_login = last_login
        return user
