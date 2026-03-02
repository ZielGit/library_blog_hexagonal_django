"""
Backend de autenticación JWT para Django REST Framework.

Este backend permite que DRF reconozca nuestros JWT tokens personalizados
sin necesidad de mixins o lógica manual en cada view.

Uso en views:
    from rest_framework.permissions import IsAuthenticated
    
    class MyProtectedView(APIView):
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]
        
        def get(self, request):
            # request.user es nuestra entidad User de dominio
            return Response({"username": request.user.username})
"""
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from uuid import UUID


class JWTAuthentication(BaseAuthentication):
    """
    Autenticación JWT personalizada para DRF.
    
    Lee el token desde el header Authorization: Bearer <token>
    y verifica su validez usando nuestro JWTTokenService.
    """

    def authenticate(self, request):
        """
        Retorna (user, None) si el token es válido.
        Retorna None si no hay token (permite vistas con AllowAny).
        Lanza AuthenticationFailed si el token es inválido.
        """
        auth_header = request.headers.get("Authorization", "")
        
        if not auth_header:
            return None  # No hay token — permitir si la view tiene AllowAny
        
        if not auth_header.startswith("Bearer "):
            raise AuthenticationFailed("Header Authorization debe ser 'Bearer <token>'")
        
        token = auth_header[7:]  # Quita "Bearer "
        
        # Verificar token con nuestro TokenService
        from config.container import get_token_service, get_user_repo
        
        token_service = get_token_service()
        payload = token_service.verify_token(token)
        
        if payload is None:
            raise AuthenticationFailed("Token inválido o expirado")
        
        # Obtener el usuario desde el repositorio
        user_repo = get_user_repo()
        user_id = UUID(payload.get("sub"))
        user = user_repo.get_by_id(user_id)
        
        if user is None:
            raise AuthenticationFailed("Usuario no encontrado")
        
        # DRF espera (user, auth_credentials)
        # auth_credentials puede ser None o el token — usamos None
        return (user, None)

    def authenticate_header(self, request):
        """
        Retorna el string que DRF usará en el header WWW-Authenticate
        cuando la autenticación falle (error 401).
        """
        return 'Bearer realm="api"'
