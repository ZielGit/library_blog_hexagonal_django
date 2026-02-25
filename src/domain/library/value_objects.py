"""
VALUE OBJECTS del módulo Library.

BookTitle e ISBN son inmutables y se identifican por su valor,
no por su identidad.
"""
import re
from dataclasses import dataclass

from src.domain.shared.base import DomainError


@dataclass(frozen=True)
class BookTitle:
    """
    Título de un libro de biblioteca.
    Más permisivo que el Title del Blog: permite caracteres
    especiales comunes en títulos académicos.
    """
    value: str

    def __post_init__(self):
        cleaned = self.value.strip() if self.value else ""
        if not cleaned:
            raise DomainError("El título del libro no puede estar vacío.")
        if len(cleaned) > 300:
            raise DomainError(
                f"El título excede 300 caracteres (actual: {len(cleaned)})."
            )
        object.__setattr__(self, "value", cleaned)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ISBN:
    """
    ISBN-13 de un libro. Valida el dígito de control módulo 10.
    Acepta formato con o sin guiones: "978-0-306-40615-7" o "9780306406157".

    Regla de validación:
      Suma alternada de dígitos × (1 o 3) debe ser divisible por 10.
    """
    value: str

    def __post_init__(self):
        # Normalizar: quitar guiones y espacios
        cleaned = re.sub(r"[-\s]", "", self.value)

        if not re.match(r"^\d{13}$", cleaned):
            raise DomainError(
                f"ISBN inválido: '{self.value}'. Debe tener 13 dígitos numéricos."
            )
        if not self._valid_check_digit(cleaned):
            raise DomainError(
                f"ISBN '{self.value}' tiene dígito de control incorrecto."
            )
        object.__setattr__(self, "value", cleaned)

    @staticmethod
    def _valid_check_digit(isbn: str) -> bool:
        """
        Algoritmo ISBN-13:
          Suma = Σ dígito[i] × (1 si i par, 3 si i impar)
          Válido si Suma % 10 == 0
        """
        total = sum(
            int(d) * (1 if i % 2 == 0 else 3)
            for i, d in enumerate(isbn)
        )
        return total % 10 == 0

    def formatted(self) -> str:
        """Retorna ISBN con guiones estándar: 978-X-XXX-XXXXX-X"""
        v = self.value
        return f"{v[:3]}-{v[3]}-{v[4:7]}-{v[7:12]}-{v[12]}"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class PublishedYear:
    """
    Año de publicación de un libro.
    Debe ser un año válido (entre 1450 y el año actual).
    """
    value: int

    def __post_init__(self):
        from datetime import datetime
        current_year = datetime.now().year
        if not (1450 <= self.value <= current_year + 1):
            raise DomainError(
                f"Año de publicación inválido: {self.value}. "
                f"Debe estar entre 1450 y {current_year + 1}."
            )

    def __str__(self) -> str:
        return str(self.value)
