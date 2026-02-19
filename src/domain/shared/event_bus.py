"""
PUERTO de salida: contrato del Event Bus.
El dominio sólo conoce esta interface — no sabe si debajo hay
Celery, RabbitMQ o una lista en memoria para tests.
"""
from abc import ABC, abstractmethod
from .base import DomainEvent


class EventBus(ABC):
    """
    Puerto (interface) del bus de eventos.
    Analogía: es el sistema de megafonía de un aeropuerto.
    El altavoz (dominio) anuncia vuelos; no sabe si alguien escucha.
    """

    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        """Publica un evento de dominio."""
        ...

    @abstractmethod
    def publish_many(self, events: list[DomainEvent]) -> None:
        """Publica varios eventos de una sola vez."""
        ...
