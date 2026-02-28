"""
COMMANDS del módulo Users: Register y Login.
"""
from dataclasses import dataclass
from uuid import UUID

from src.domain.users.entities import User, UserRole
from src.domain.users.repositories import UserRepository, PasswordHasher, TokenService
from src.domain.shared.base import DomainError


# ── DTOs de respuesta ────────────────────────────────────────
@dataclass(frozen=True)
class RegisteredUserDTO:
    id: UUID
    email: str
    username: str
    role: str


@dataclass(frozen=True)
class AuthTokensDTO:
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    user_id: UUID = None
    role: str = ""


# ══════════════════════════════════════════════════════════════
# REGISTER USER
# ══════════════════════════════════════════════════════════════
@dataclass(frozen=True)
class RegisterUserCommand:
    email: str
    username: str
    password: str
    role: str = "reader"


class RegisterUserCommandHandler:
    """
    Registra un nuevo usuario.
    Verifica unicidad de email y username antes de crear.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher: PasswordHasher,
    ):
        self._repo = user_repo
        self._hasher = password_hasher

    def handle(self, command: RegisterUserCommand) -> RegisteredUserDTO:
        # 1. Verificar unicidad
        if self._repo.email_exists(command.email):
            raise DomainError(f"El email '{command.email}' ya está registrado.")
        if self._repo.username_exists(command.username):
            raise DomainError(f"El username '{command.username}' ya está en uso.")

        # 2. Validar contraseña
        if len(command.password) < 8:
            raise DomainError("La contraseña debe tener al menos 8 caracteres.")

        # 3. Crear usuario con contraseña hasheada
        try:
            role = UserRole(command.role)
        except ValueError:
            role = UserRole.READER

        hashed = self._hasher.hash(command.password)
        user = User(
            email=command.email,
            username=command.username,
            hashed_password=hashed,
            role=role,
        )

        # 4. Persistir
        self._repo.save(user)

        return RegisteredUserDTO(
            id=user.id,
            email=user.email,
            username=user.username,
            role=user.role.value,
        )


# ══════════════════════════════════════════════════════════════
# LOGIN
# ══════════════════════════════════════════════════════════════
@dataclass(frozen=True)
class LoginCommand:
    email: str
    password: str


class LoginCommandHandler:
    """
    Autentica un usuario y genera JWT tokens.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ):
        self._repo = user_repo
        self._hasher = password_hasher
        self._tokens = token_service

    def handle(self, command: LoginCommand) -> AuthTokensDTO:
        # 1. Buscar usuario
        user = self._repo.get_by_email(command.email)
        if user is None:
            raise DomainError("Credenciales inválidas.")  # No decir "email no existe"

        # 2. Verificar contraseña
        if not self._hasher.verify(command.password, user.hashed_password):
            raise DomainError("Credenciales inválidas.")

        # 3. Verificar que el usuario está activo
        if not user.is_active:
            raise DomainError("Tu cuenta está desactivada. Contacta al administrador.")

        # 4. Registrar login y generar tokens
        user.record_login()
        self._repo.save(user)

        access = self._tokens.generate_access_token(user.id, user.role.value)
        refresh = self._tokens.generate_refresh_token(user.id)

        return AuthTokensDTO(
            access_token=access,
            refresh_token=refresh,
            user_id=user.id,
            role=user.role.value,
        )


# ══════════════════════════════════════════════════════════════
# REFRESH TOKEN
# ══════════════════════════════════════════════════════════════
@dataclass(frozen=True)
class RefreshTokenCommand:
    refresh_token: str


class RefreshTokenCommandHandler:

    def __init__(
        self,
        user_repo: UserRepository,
        token_service: TokenService,
    ):
        self._repo = user_repo
        self._tokens = token_service

    def handle(self, command: RefreshTokenCommand) -> AuthTokensDTO:
        payload = self._tokens.verify_token(command.refresh_token)
        if payload is None or payload.get("type") != "refresh":
            raise DomainError("Token de refresco inválido o expirado.")

        from uuid import UUID
        user = self._repo.get_by_id(UUID(payload["sub"]))
        if user is None or not user.is_active:
            raise DomainError("Usuario no encontrado o inactivo.")

        access = self._tokens.generate_access_token(user.id, user.role.value)
        refresh = self._tokens.generate_refresh_token(user.id)

        return AuthTokensDTO(
            access_token=access,
            refresh_token=refresh,
            user_id=user.id,
            role=user.role.value,
        )
