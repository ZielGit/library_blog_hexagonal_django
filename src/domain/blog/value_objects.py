"""
VALUE OBJECTS del módulo Blog.

Regla de oro: son INMUTABLES (frozen=True) y se definen por su VALOR,
no por su identidad.
"""
import re
from dataclasses import dataclass

from src.domain.shared.base import DomainError


# ─────────────────────────────────────────────────────────────
# TITLE
# ─────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Title:
    """
    Título de un post o libro.
    Garantiza que siempre es válido: no vacío, max 200 chars, capitalizado.
    """
    value: str

    def __post_init__(self):
        # frozen=True no permite self.value = ..., usamos object.__setattr__
        cleaned = self.value.strip().title() if self.value else ""

        if not cleaned:
            raise DomainError("El título no puede estar vacío.")
        if len(cleaned) > 200:
            raise DomainError(f"El título excede 200 caracteres (actual: {len(cleaned)}).")

        object.__setattr__(self, "value", cleaned)

    def to_slug(self) -> "Slug":
        """Genera un Slug a partir del título."""
        import re
        raw = self.value.lower()
        raw = re.sub(r"[áàäâ]", "a", raw)
        raw = re.sub(r"[éèëê]", "e", raw)
        raw = re.sub(r"[íìïî]", "i", raw)
        raw = re.sub(r"[óòöô]", "o", raw)
        raw = re.sub(r"[úùüû]", "u", raw)
        raw = re.sub(r"ñ", "n", raw)
        raw = re.sub(r"[^a-z0-9\s-]", "", raw)
        raw = re.sub(r"[\s]+", "-", raw.strip())
        return Slug(value=raw)

    def __str__(self) -> str:
        return self.value


# ─────────────────────────────────────────────────────────────
# SLUG
# ─────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Slug:
    """
    Slug URL-safe para posts: solo letras minúsculas, números y guiones.
    """
    value: str

    def __post_init__(self):
        cleaned = self.value.strip().lower()
        if not cleaned:
            raise DomainError("El slug no puede estar vacío.")
        if not re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$", cleaned) and len(cleaned) > 1:
            raise DomainError(
                f"Slug inválido '{cleaned}'. Solo letras minúsculas, números y guiones."
            )
        object.__setattr__(self, "value", cleaned)

    def __str__(self) -> str:
        return self.value


# ─────────────────────────────────────────────────────────────
# CONTENT
# ─────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Content:
    """
    Contenido de un post. Mínimo 100 chars para poder publicar.
    Soporta Markdown.
    """
    value: str
    MIN_LENGTH_TO_PUBLISH = 100

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise DomainError("El contenido no puede estar vacío.")
        object.__setattr__(self, "value", self.value)

    @property
    def is_publishable(self) -> bool:
        return len(self.value.strip()) >= self.MIN_LENGTH_TO_PUBLISH

    @property
    def word_count(self) -> int:
        return len(self.value.split())

    def excerpt(self, max_chars: int = 160) -> str:
        """Retorna un resumen truncado."""
        if len(self.value) <= max_chars:
            return self.value
        return self.value[:max_chars].rsplit(" ", 1)[0] + "..."

    def __str__(self) -> str:
        return self.value


# ─────────────────────────────────────────────────────────────
# ISBN (para el módulo Library)
# ─────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class ISBN:
    """
    ISBN-13 de un libro. Valida el formato y el dígito de control.
    """
    value: str

    def __post_init__(self):
        cleaned = re.sub(r"[-\s]", "", self.value)
        if not re.match(r"^\d{13}$", cleaned):
            raise DomainError(f"ISBN inválido: '{self.value}'. Debe tener 13 dígitos.")
        if not self._valid_check_digit(cleaned):
            raise DomainError(f"ISBN '{self.value}' tiene dígito de control incorrecto.")
        object.__setattr__(self, "value", cleaned)

    @staticmethod
    def _valid_check_digit(isbn: str) -> bool:
        total = sum(
            int(d) * (1 if i % 2 == 0 else 3)
            for i, d in enumerate(isbn)
        )
        return total % 10 == 0

    def formatted(self) -> str:
        """ISBN con guiones: 978-X-XXX-XXXXX-X"""
        v = self.value
        return f"{v[:3]}-{v[3]}-{v[4:7]}-{v[7:12]}-{v[12]}"

    def __str__(self) -> str:
        return self.value
