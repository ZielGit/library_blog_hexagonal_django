"""
ADAPTADORES del Event Bus.

1. InMemoryEventBus  — para tests (guarda eventos en lista)
2. LoggingEventBus   — para desarrollo (loguea eventos a consola)
3. CeleryEventBus    — para producción (stub — requiere Celery instalado)

El dominio y la application NO importan ninguno de estos.
Solo los conoce el Composition Root (container.py).
"""
import json
import logging
from uuid import UUID
from datetime import datetime

from src.domain.shared.base import DomainEvent
from src.domain.shared.event_bus import EventBus

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# IN-MEMORY EVENT BUS (para tests)
# ─────────────────────────────────────────────────────────────
class InMemoryEventBus(EventBus):
    """
    Adaptador de test: almacena eventos en memoria.
    Útil para verificar qué eventos se emitieron en un test.

    Uso en tests:
        bus = InMemoryEventBus()
        handler = CreatePostCommandHandler(repo, bus)
        handler.handle(command)
        assert len(bus.published) == 1
        assert isinstance(bus.published[0], PostCreated)
    """

    def __init__(self):
        self._published: list[DomainEvent] = []

    def publish(self, event: DomainEvent) -> None:
        self._published.append(event)
        logger.debug(f"[InMemoryEventBus] Event published: {event.__class__.__name__}")

    def publish_many(self, events: list[DomainEvent]) -> None:
        for event in events:
            self.publish(event)

    @property
    def published(self) -> list[DomainEvent]:
        return list(self._published)

    def clear(self) -> None:
        """Limpia el historial (útil entre tests)."""
        self._published = []

    def get_events_of_type(self, event_type: type) -> list[DomainEvent]:
        """Filtra eventos por tipo — facilita assertions en tests."""
        return [e for e in self._published if isinstance(e, event_type)]


# ─────────────────────────────────────────────────────────────
# LOGGING EVENT BUS (para desarrollo)
# ─────────────────────────────────────────────────────────────
class LoggingEventBus(EventBus):
    """
    Adaptador de desarrollo: loguea todos los eventos.
    No hace nada real — sirve para ver el flujo de eventos.
    """

    def publish(self, event: DomainEvent) -> None:
        logger.info(
            f"[EVENT] {event.__class__.__name__} | "
            f"id={event.event_id} | "
            f"at={event.occurred_at.isoformat()}"
        )

    def publish_many(self, events: list[DomainEvent]) -> None:
        for event in events:
            self.publish(event)


# ─────────────────────────────────────────────────────────────
# CELERY EVENT BUS (stub para producción)
# ─────────────────────────────────────────────────────────────
class CeleryEventBus(EventBus):
    """
    Adaptador de producción: serializa eventos y los envía a Celery.

    NOTA: Este es un stub. En producción necesitas:
      pip install celery redis
      Y configurar CELERY_BROKER_URL en settings.py

    El Handler no sabe si hay Celery — solo llama a publish().
    """

    def publish(self, event: DomainEvent) -> None:
        try:
            # Import tardío — solo cuando Celery está disponible
            from config.celery import dispatch_domain_event
            payload = self._serialize(event)
            dispatch_domain_event.delay(payload)
        except ImportError:
            logger.warning(
                f"[CeleryEventBus] Celery no disponible. "
                f"Evento {event.__class__.__name__} no publicado."
            )

    def publish_many(self, events: list[DomainEvent]) -> None:
        for event in events:
            self.publish(event)

    @staticmethod
    def _serialize(event: DomainEvent) -> dict:
        """Convierte el evento a dict serializable para Celery."""
        data = {}
        for key, value in event.__dict__.items():
            if isinstance(value, UUID):
                data[key] = str(value)
            elif isinstance(value, datetime):
                data[key] = value.isoformat()
            else:
                data[key] = value
        return {
            "event_type": event.__class__.__name__,
            "event_id": str(event.event_id),
            "occurred_at": event.occurred_at.isoformat(),
            "data": data,
        }
