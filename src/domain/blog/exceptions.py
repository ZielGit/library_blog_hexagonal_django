"""
EXCEPCIONES del dominio Blog.

Cada excepción representa una violación de una regla de negocio.
Son más expresivas que un ValueError genérico — el nombre
ya describe QUÉ salió mal sin leer el mensaje.

Jerarquía:
    DomainException (base)
        ├── BlogException (base de blog)
        │   ├── PostNotFoundError
        │   ├── PostAlreadyPublishedError
        │   ├── PostArchivedError
        │   ├── InvalidPostContentError
        │   ├── UnauthorizedPostActionError
        │   └── CommentNotAllowedError
        └── ValidationError (reglas de formato)

Uso en los Handlers:
    try:
        post.publish()
    except PostAlreadyPublishedError:
        return Response({"error": "..."}, 409)
    except BlogException as e:
        return Response({"error": str(e)}, 422)
"""


# ─────────────────────────────────────────────────────────────
# BASE
# ─────────────────────────────────────────────────────────────
class DomainException(Exception):
    """Raíz de todas las excepciones de dominio."""
    pass


class ValidationError(DomainException):
    """Dato de entrada no cumple reglas de formato (Value Objects)."""
    pass


# ─────────────────────────────────────────────────────────────
# BLOG EXCEPTIONS
# ─────────────────────────────────────────────────────────────
class BlogException(DomainException):
    """Base de todas las excepciones del módulo Blog."""
    pass


class PostNotFoundError(BlogException):
    """El post solicitado no existe en el sistema."""
    def __init__(self, identifier: str):
        super().__init__(f"Post '{identifier}' no encontrado.")
        self.identifier = identifier


class PostAlreadyPublishedError(BlogException):
    """Intento de publicar un post que ya está publicado."""
    def __init__(self):
        super().__init__("El post ya está publicado.")


class PostArchivedError(BlogException):
    """Operación no permitida sobre un post archivado."""
    def __init__(self, operation: str = "esta operación"):
        super().__init__(f"No se puede realizar '{operation}' en un post archivado.")
        self.operation = operation


class InvalidPostContentError(BlogException):
    """El contenido no cumple los requisitos mínimos para publicar."""
    def __init__(self, current_length: int, min_length: int):
        super().__init__(
            f"El contenido es demasiado corto para publicar "
            f"({current_length} chars). Mínimo requerido: {min_length}."
        )
        self.current_length = current_length
        self.min_length = min_length


class UnauthorizedPostActionError(BlogException):
    """El usuario no tiene permisos para realizar esta acción sobre el post."""
    def __init__(self, action: str = "esta acción"):
        super().__init__(f"No tienes permisos para realizar '{action}' en este post.")
        self.action = action


class CommentNotAllowedError(BlogException):
    """No se puede comentar en este post (archivado, cerrado, etc.)."""
    def __init__(self, reason: str = "comentarios no permitidos"):
        super().__init__(f"No se puede añadir un comentario: {reason}.")
        self.reason = reason


class DuplicateSlugError(BlogException):
    """Ya existe un post con ese slug."""
    def __init__(self, slug: str):
        super().__init__(f"Ya existe un post con el slug '{slug}'.")
        self.slug = slug


# ─────────────────────────────────────────────────────────────
# CATEGORY EXCEPTIONS
# ─────────────────────────────────────────────────────────────
class CategoryNotFoundError(BlogException):
    def __init__(self, identifier: str):
        super().__init__(f"Categoría '{identifier}' no encontrada.")
        self.identifier = identifier
