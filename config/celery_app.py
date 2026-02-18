"""
CONFIGURACIÓN DE CELERY.

Este archivo hace dos cosas:
  1. Crea la instancia de la app Celery (config.celery_app:app)
  2. Define la tarea `dispatch_domain_event` que recibe
     Domain Events serializados y los enruta al handler correcto.

Cómo arrancarlo:
  celery -A config.celery_app worker --loglevel=info
  celery -A config.celery_app beat   --loglevel=info   # tareas periódicas

Monitoreo con Flower:
  celery -A config.celery_app flower --port=5555
"""
import os
import importlib
import logging

from celery import Celery

logger = logging.getLogger(__name__)

# ── Configuración base ────────────────────────────────────────
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("library_blog")

# Lee toda la configuración de Django settings con prefijo CELERY_
# Ejemplo: CELERY_BROKER_URL, CELERY_RESULT_BACKEND, etc.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-descubre tareas en archivos tasks.py de cada app Django
app.autodiscover_tasks()


# ─────────────────────────────────────────────────────────────
# MAPA DE EVENTOS → HANDLERS
# Cuando llega un evento serializado, este mapa determina
# qué handler de la capa Application debe procesarlo.
# ─────────────────────────────────────────────────────────────
EVENT_HANDLER_MAP: dict[str, str] = {
    "PostCreated": (
        "src.application.blog.event_handlers.post_event_handlers",
        "OnPostCreated",
    ),
    "PostPublished": (
        "src.application.blog.event_handlers.post_event_handlers",
        "OnPostPublished",
    ),
    "PostArchived": (
        "src.application.blog.event_handlers.post_event_handlers",
        "OnPostArchived",
    ),
    "CommentAdded": (
        "src.application.blog.event_handlers.post_event_handlers",
        "OnCommentAdded",
    ),
    "PostUpdated": (
        "src.application.blog.event_handlers.post_event_handlers",
        "OnPostCreated",  # reutilizamos o crea uno dedicado
    ),
}


# ─────────────────────────────────────────────────────────────
# TAREA PRINCIPAL: dispatch_domain_event
# ─────────────────────────────────────────────────────────────
@app.task(
    name="dispatch_domain_event",
    bind=True,
    max_retries=3,
    default_retry_delay=30,   # segundos entre reintentos
    acks_late=True,            # confirma el mensaje DESPUÉS de ejecutar
)
def dispatch_domain_event(self, payload: dict):
    """
    Tarea Celery que recibe un Domain Event serializado como dict
    y lo enruta al EventHandler correspondiente.

    Payload esperado:
        {
            "event_type": "PostPublished",
            "event_id": "uuid...",
            "occurred_at": "2025-01-01T00:00:00Z",
            "data": { "post_id": "uuid...", "slug": "mi-post" }
        }

    Flujo:
      CeleryEventBus.publish(PostPublished)
        → serializa a dict
          → dispatch_domain_event.delay(dict)   [async]
            → este worker lo recibe
              → instancia el handler correcto
                → handler.handle(event reconstruido)
    """
    event_type = payload.get("event_type", "")
    event_id = payload.get("event_id", "N/A")

    logger.info(f"[Celery] Procesando evento: {event_type} (id={event_id})")

    # 1. Buscar el handler en el mapa
    handler_info = EVENT_HANDLER_MAP.get(event_type)
    if not handler_info:
        logger.warning(f"[Celery] Sin handler para evento: {event_type}. Ignorando.")
        return {"status": "skipped", "event_type": event_type}

    module_path, class_name = handler_info

    try:
        # 2. Importar dinámicamente el handler
        module = importlib.import_module(module_path)
        handler_cls = getattr(module, class_name)

        # 3. Construir dependencias del handler desde el container
        handler = _build_handler(class_name)

        # 4. Reconstruir el evento de dominio desde el payload
        event = _reconstruct_event(event_type, payload)

        # 5. Ejecutar el handler
        if event and hasattr(handler, "handle"):
            handler.handle(event)
        else:
            # Si no podemos reconstruir el evento, llamamos con datos raw
            logger.warning(
                f"[Celery] Ejecutando {class_name} con payload raw "
                f"(evento no reconstruido)."
            )

        logger.info(f"[Celery] ✅ {event_type} procesado por {class_name}")
        return {"status": "ok", "event_type": event_type, "handler": class_name}

    except Exception as exc:
        logger.error(
            f"[Celery] ❌ Error procesando {event_type}: {exc}",
            exc_info=True,
        )
        # Reintenta automáticamente hasta max_retries
        raise self.retry(exc=exc)


def _build_handler(class_name: str):
    """
    Construye el handler con sus dependencias inyectadas.
    Los servicios opcionales (email, caché) se inyectan si están disponibles.
    """
    from config.container import get_cache_service

    cache = get_cache_service()

    handlers_config = {
        "OnPostPublished": lambda: _import_cls(
            "src.application.blog.event_handlers.post_event_handlers",
            "OnPostPublished"
        )(cache_service=cache),

        "OnCommentAdded": lambda: _import_cls(
            "src.application.blog.event_handlers.post_event_handlers",
            "OnCommentAdded"
        )(),

        "OnPostArchived": lambda: _import_cls(
            "src.application.blog.event_handlers.post_event_handlers",
            "OnPostArchived"
        )(cache_service=cache),

        "OnPostCreated": lambda: _import_cls(
            "src.application.blog.event_handlers.post_event_handlers",
            "OnPostCreated"
        )(),
    }

    factory = handlers_config.get(class_name)
    if factory:
        return factory()

    # Fallback: instanciar sin dependencias
    return _import_cls(
        "src.application.blog.event_handlers.post_event_handlers",
        class_name
    )()


def _import_cls(module_path: str, class_name: str):
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def _reconstruct_event(event_type: str, payload: dict):
    """
    Reconstruye el objeto DomainEvent desde el payload serializado.
    Retorna None si no puede reconstruir.
    """
    from uuid import UUID
    from datetime import datetime, timezone

    data = payload.get("data", {})

    try:
        event_classes = {
            "PostCreated": _import_cls(
                "src.domain.blog.events", "PostCreated"
            ),
            "PostPublished": _import_cls(
                "src.domain.blog.events", "PostPublished"
            ),
            "PostArchived": _import_cls(
                "src.domain.blog.events", "PostArchived"
            ),
            "CommentAdded": _import_cls(
                "src.domain.blog.events", "CommentAdded"
            ),
        }

        event_cls = event_classes.get(event_type)
        if not event_cls:
            return None

        # Convertir UUIDs de string a UUID
        clean_data = {}
        for k, v in data.items():
            if k in ("post_id", "comment_id", "author_id", "event_id"):
                try:
                    clean_data[k] = UUID(v) if v else None
                except (ValueError, AttributeError):
                    clean_data[k] = v
            else:
                clean_data[k] = v

        # Quitar campos que no son parámetros del evento
        clean_data.pop("event_id", None)
        clean_data.pop("occurred_at", None)

        return event_cls(**clean_data)

    except Exception as e:
        logger.warning(f"[Celery] No se pudo reconstruir {event_type}: {e}")
        return None


# ─────────────────────────────────────────────────────────────
# TAREA DE DIAGNÓSTICO (útil para verificar que Celery funciona)
# ─────────────────────────────────────────────────────────────
@app.task(name="health_check")
def health_check():
    """
    Tarea de diagnóstico. Verifica que Celery está funcionando.
    Ejecución manual:
      from config.celery_app import health_check
      result = health_check.delay()
      print(result.get(timeout=10))  # → "Celery OK"
    """
    return "Celery OK"
