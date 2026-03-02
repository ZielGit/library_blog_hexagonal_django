"""
VISTAS de autenticación — Adaptadores Primarios del módulo Users.

Endpoints:
  POST /api/auth/register/   → Registrar nuevo usuario
  POST /api/auth/login/      → Login, retorna JWT tokens
  POST /api/auth/refresh/    → Renovar access token
  GET  /api/auth/me/         → Perfil del usuario autenticado

Autenticación JWT en DRF:
  El cliente envía: Authorization: Bearer <access_token>
  La view verifica el token y carga el usuario antes de procesar.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from src.domain.shared.base import DomainError
from src.application.users.commands.auth_commands import (
    RegisterUserCommand,
    LoginCommand,
    RefreshTokenCommand,
)
from src.infrastructure.auth.drf_jwt_authentication import JWTAuthentication as JWTAuth


def _get_auth_container():
    from config.container import (
        get_register_handler,
        get_login_handler,
        get_refresh_token_handler,
    )
    return get_register_handler, get_login_handler, get_refresh_token_handler


# ─────────────────────────────────────────────────────────────
# REGISTER
# ─────────────────────────────────────────────────────────────
class RegisterView(APIView):
    """POST /api/auth/register/"""
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            command = RegisterUserCommand(
                email=request.data.get("email", ""),
                username=request.data.get("username", ""),
                password=request.data.get("password", ""),
            )
            get_register_handler, _, _ = _get_auth_container()
            result = get_register_handler().handle(command)

            return Response(
                {
                    "id": str(result.id),
                    "email": result.email,
                    "username": result.username,
                    "role": result.role,
                },
                status=status.HTTP_201_CREATED,
            )
        except DomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except Exception as e:
            return Response({"error": "Error interno."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────────────────────
class LoginView(APIView):
    """POST /api/auth/login/"""
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            command = LoginCommand(
                email=request.data.get("email", ""),
                password=request.data.get("password", ""),
            )
            _, get_login_handler, _ = _get_auth_container()
            result = get_login_handler().handle(command)

            return Response({
                "access_token": result.access_token,
                "refresh_token": result.refresh_token,
                "token_type": result.token_type,
                "user_id": str(result.user_id),
                "role": result.role,
            })
        except DomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)


# ─────────────────────────────────────────────────────────────
# REFRESH TOKEN
# ─────────────────────────────────────────────────────────────
class RefreshTokenView(APIView):
    """POST /api/auth/refresh/"""
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            command = RefreshTokenCommand(
                refresh_token=request.data.get("refresh_token", "")
            )
            _, _, get_refresh_handler = _get_auth_container()
            result = get_refresh_handler().handle(command)

            return Response({
                "access_token": result.access_token,
                "refresh_token": result.refresh_token,
            })
        except DomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)


# ─────────────────────────────────────────────────────────────
# ME VIEW
# ─────────────────────────────────────────────────────────────
class MeView(APIView):
    """GET /api/auth/me/"""
    authentication_classes = [JWTAuth]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # request.user es nuestra entidad User de dominio
        user = request.user
        
        # Usar query handler para ser consistentes con CQRS
        from config.container import get_user_profile_handler
        from src.application.users.queries.user_queries import GetUserProfileQuery

        query = GetUserProfileQuery(user_id=user.id)
        profile = get_user_profile_handler().handle(query)

        if profile is None:
            return Response(
                {"error": "Usuario no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            "id": str(profile.id),
            "email": profile.email,
            "username": profile.username,
            "role": profile.role,
            "status": profile.status,
            "permissions": profile.permissions,
            "created_at": profile.created_at,
            "last_login": profile.last_login,
        })
