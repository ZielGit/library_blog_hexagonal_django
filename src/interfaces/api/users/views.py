"""VISTAS de autenticación"""
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
from .swagger_schemas import (
    register_schema,
    login_schema,
    refresh_schema,
    me_schema,
)


def _get_auth_container():
    from config.container import (
        get_register_handler,
        get_login_handler,
        get_refresh_token_handler,
    )
    return get_register_handler, get_login_handler, get_refresh_token_handler


class RegisterView(APIView):
    """POST /api/auth/register/"""
    permission_classes = [AllowAny]

    @register_schema
    def post(self, request):
        try:
            command = RegisterUserCommand(
                email=request.data.get("email", ""),
                username=request.data.get("username", ""),
                password=request.data.get("password", ""),
            )
            get_register_handler, _, _ = _get_auth_container()
            result = get_register_handler().handle(command)

            return Response({
                "user_id": str(result.user_id),
                "email": result.email,
                "username": result.username,
                "role": result.role,
            }, status=status.HTTP_201_CREATED)
        except DomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """POST /api/auth/login/"""
    permission_classes = [AllowAny]

    @login_schema
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
                "user_id": str(result.user_id),
                "role": result.role,
            })
        except DomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)


class RefreshTokenView(APIView):
    """POST /api/auth/refresh/"""
    permission_classes = [AllowAny]

    @refresh_schema
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


class MeView(APIView):
    """GET /api/auth/me/"""
    authentication_classes = [JWTAuth]
    permission_classes = [IsAuthenticated]

    @me_schema
    def get(self, request):
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
