"""
Clases base compartidas por todo el dominio.
Ningún import de Django aquí — el dominio es puro Python.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


# ─────────────────────────────────────────────────────────────
# BASE ENTITY
# ─────────────────────────────────────────────────────────────
class Entity:
    """
    Toda entidad tiene identidad única (id).
    """
    def __init__(self, entity_id: UUID | None = None):
        self._id: UUID = entity_id or uuid4()

    @property
    def id(self) -> UUID:
        return self._id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)


# ─────────────────────────────────────────────────────────────
# BASE AGGREGATE ROOT
# ─────────────────────────────────────────────────────────────
class AggregateRoot(Entity):
    """
    Raíz de agregado: controla la consistencia del cluster de entidades
    y acumula domain events para publicarlos después de persistir.
    """
    def __init__(self, entity_id: UUID | None = None):
        super().__init__(entity_id)
        self._domain_events: list = []

    def _record_event(self, event) -> None:
        self._domain_events.append(event)

    def pull_events(self) -> list:
        """Extrae y limpia los eventos pendientes (consume-once)."""
        events, self._domain_events = self._domain_events, []
        return events


# ─────────────────────────────────────────────────────────────
# BASE DOMAIN EVENT
# ─────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class DomainEvent:
    """
    Algo importante que OCURRIÓ en el dominio (pasado).
    Inmutable: los hechos del pasado no cambian.
    """
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ─────────────────────────────────────────────────────────────
# BASE DOMAIN EXCEPTION
# ─────────────────────────────────────────────────────────────
class DomainError(Exception):
    """Error de regla de negocio en el dominio."""
    pass


class NotFoundError(DomainError):
    """Entidad no encontrada."""
    pass
