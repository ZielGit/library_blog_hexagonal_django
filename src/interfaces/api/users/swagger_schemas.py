"""Schemas de drf-spectacular para la API de Users/Auth"""
from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework import serializers


# ═══════════════════════════════════════════════════════════════
# SERIALIZERS
# ═══════════════════════════════════════════════════════════════

class RegisterRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(min_length=3, max_length=50)
    password = serializers.CharField(min_length=8, write_only=True)


class RegisterResponseSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    email = serializers.EmailField()
    username = serializers.CharField()
    role = serializers.CharField()


class LoginRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class LoginResponseSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    user_id = serializers.UUIDField()
    role = serializers.CharField()


class RefreshRequestSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class RefreshResponseSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()


class UserProfileResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.EmailField()
    username = serializers.CharField()
    role = serializers.CharField()
    status = serializers.CharField()
    permissions = serializers.ListField(child=serializers.CharField())
    created_at = serializers.DateTimeField()
    last_login = serializers.DateTimeField(allow_null=True)


# ═══════════════════════════════════════════════════════════════
# SCHEMA DECORATORS
# ═══════════════════════════════════════════════════════════════

register_schema = extend_schema(
    summary="Registrar usuario",
    description="Crea un nuevo usuario en el sistema con role 'reader' por defecto",
    request=RegisterRequestSerializer,
    responses={
        201: RegisterResponseSerializer,
        400: {"description": "Email o username ya existe / Validación fallida"},
    },
    examples=[
        OpenApiExample(
            "Usuario nuevo",
            value={
                "email": "juan@example.com",
                "username": "juan123",
                "password": "MiPassword123"
            },
            request_only=True,
        )
    ],
    tags=["Auth"],
)

login_schema = extend_schema(
    summary="Login",
    description="Autentica usuario y retorna JWT tokens (access + refresh)",
    request=LoginRequestSerializer,
    responses={
        200: LoginResponseSerializer,
        401: {"description": "Credenciales inválidas / Usuario inactivo"},
    },
    examples=[
        OpenApiExample(
            "Login ejemplo",
            value={"email": "juan@example.com", "password": "MiPassword123"},
            request_only=True,
        )
    ],
    tags=["Auth"],
)

refresh_schema = extend_schema(
    summary="Renovar access token",
    description="Usa el refresh token para obtener un nuevo access token",
    request=RefreshRequestSerializer,
    responses={
        200: RefreshResponseSerializer,
        401: {"description": "Refresh token inválido o expirado"},
    },
    tags=["Auth"],
)

me_schema = extend_schema(
    summary="Obtener perfil",
    description="Retorna el perfil del usuario autenticado",
    request=None,
    responses={
        200: UserProfileResponseSerializer,
        401: {"description": "Token inválido o no provisto"},
    },
    tags=["Auth"],
)
