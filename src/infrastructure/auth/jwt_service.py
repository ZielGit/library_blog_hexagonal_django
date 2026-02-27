"""
ADAPTADOR JWT para autenticación.

Implementa el puerto TokenService usando PyJWT.
Genera y verifica Access Tokens (corta duración) y
Refresh Tokens (larga duración).
"""
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from src.domain.users.repositories import TokenService, PasswordHasher

logger = logging.getLogger(__name__)


class JWTTokenService(TokenService):
    """
    Genera y verifica JWT tokens con PyJWT.

    Estructura del token:
      Header:  { "alg": "HS256", "typ": "JWT" }
      Payload: { "sub": user_id, "role": role, "exp": ..., "iat": ... }
    """

    def __init__(
        self,
        secret_key: str,
        access_expire_minutes: int = 30,
        refresh_expire_days: int = 7,
    ):
        self._secret = secret_key
        self._access_expire = timedelta(minutes=access_expire_minutes)
        self._refresh_expire = timedelta(days=refresh_expire_days)

    def generate_access_token(self, user_id: UUID, role: str) -> str:
        payload = {
            "sub": str(user_id),
            "role": role,
            "type": "access",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + self._access_expire,
        }
        return self._encode(payload)

    def generate_refresh_token(self, user_id: UUID) -> str:
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + self._refresh_expire,
        }
        return self._encode(payload)

    def verify_token(self, token: str) -> dict | None:
        """
        Verifica y decodifica un token.
        Retorna el payload si es válido, None si no.
        """
        try:
            import jwt
            payload = jwt.decode(token, self._secret, algorithms=["HS256"])
            return payload
        except Exception as e:
            logger.debug(f"[JWTTokenService] Token inválido: {e}")
            return None

    def _encode(self, payload: dict) -> str:
        try:
            import jwt
            return jwt.encode(payload, self._secret, algorithm="HS256")
        except ImportError:
            raise RuntimeError("PyJWT no instalado. Ejecuta: pip install PyJWT")


class BcryptPasswordHasher(PasswordHasher):
    """
    Hashea contraseñas con bcrypt.
    """

    def hash(self, plain_password: str) -> str:
        try:
            import bcrypt
            salt = bcrypt.gensalt()
            return bcrypt.hashpw(plain_password.encode(), salt).decode()
        except ImportError:
            raise RuntimeError("bcrypt no instalado. Ejecuta: pip install bcrypt")

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        try:
            import bcrypt
            return bcrypt.checkpw(
                plain_password.encode(),
                hashed_password.encode()
            )
        except ImportError:
            raise RuntimeError("bcrypt no instalado. Ejecuta: pip install bcrypt")
        except Exception:
            return False


class DjangoPasswordHasher(PasswordHasher):
    """
    Usa el hasher nativo de Django (PBKDF2).
    Alternativa si ya usas Django Auth — no requiere dependencias extra.
    """

    def hash(self, plain_password: str) -> str:
        from django.contrib.auth.hashers import make_password
        return make_password(plain_password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        from django.contrib.auth.hashers import check_password
        return check_password(plain_password, hashed_password)
