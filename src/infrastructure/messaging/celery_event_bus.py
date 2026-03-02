"""
ADAPTADOR Celery para el Event Bus.

Traduce Domain Events a tareas Celery asíncronas.
El dominio no sabe que existe Celery — solo llama a EventBus.publish().

Flujo:
  PostAggregate.publish()
    → PostPublished event
      → CeleryEventBus.publish(PostPublished)
        → celery_task.delay(payload_json)
          → Worker Celery ejecuta OnPostPublished.handle()
            → Envía email, invalida caché, etc.

Ventajas de Celery para Event Bus:
  - Asíncrono: la API responde rápido, los efectos ocurren en background
  - Reintentos automáticos si falla el email o la caché
  - Monitoreo con Flower dashboard
"""
import json
import logging
from datetime import datetime
from uuid import UUID

from src.domain.shared.base import DomainEvent
from src.domain.shared.event_bus import EventBus

logger = logging.getLogger(__name__)

# Mapa de nombre de evento → clase del evento
# Se usa para deserializar en el worker
EVENT_REGISTRY: dict[str, type] = {}


def register_event(cls):
    """Decorador para registrar eventos en el registry."""
    EVENT_REGISTRY[cls.__name__] = cls
    return cls


# ─────────────────────────────────────────────────────────────
# CELERY EVENT BUS
# ─────────────────────────────────────────────────────────────
class CeleryEventBus(EventBus):
    """
    Publica eventos como tareas Celery.
    Requiere: CELERY_BROKER_URL configurado en settings.py
    """

    def publish(self, event: DomainEvent) -> None:
        try:
            from config.celery_app import dispatch_domain_event
            payload = self._serialize(event)
            dispatch_domain_event.delay(payload)
            logger.info(
                f"[CeleryEventBus] Publicado: {event.__class__.__name__} "
                f"id={event.event_id}"
            )
        except ImportError:
            logger.warning(
                f"[CeleryEventBus] Celery no disponible. "
                f"Evento {event.__class__.__name__} descartado."
            )
        except Exception as e:
            logger.error(
                f"[CeleryEventBus] Error publicando {event.__class__.__name__}: {e}"
            )

    def publish_many(self, events: list[DomainEvent]) -> None:
        for event in events:
            self.publish(event)

    @staticmethod
    def _serialize(event: DomainEvent) -> dict:
        """Convierte el evento a dict JSON-serializable."""
        data = {}
        for key, value in vars(event).items():
            if key.startswith("_"):
                continue
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
