"""
ADAPTADOR de Caché con Redis.

Puerto de salida: el dominio y la application no saben
si la caché es Redis, Memcached o un dict en memoria.

Patrón Cache-Aside:
  1. Leer de caché → si existe, retornar
  2. Si no existe → ir a la DB, guardar en caché, retornar
  3. Al escribir → invalidar caché relacionada
"""
import json
import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# PUERTO (interface)
# ─────────────────────────────────────────────────────────────
class CacheService(ABC):
    """Puerto de caché — el dominio/application depende de esto."""

    @abstractmethod
    def get(self, key: str) -> Any | None: ...

    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

    @abstractmethod
    def invalidate(self, pattern: str) -> None:
        """Elimina todas las claves que coincidan con el patrón (usa * como wildcard)."""
        ...


# ─────────────────────────────────────────────────────────────
# ADAPTADOR REDIS
# ─────────────────────────────────────────────────────────────
class RedisCacheService(CacheService):
    """Adaptador Redis."""
    DEFAULT_TTL = 300  # 5 minutos

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        try:
            import redis
            self._client = redis.from_url(redis_url, decode_responses=True)
            self._client.ping()
            logger.info(f"[RedisCacheService] Conectado a {redis_url}")
        except ImportError:
            raise RuntimeError(
                "Redis no instalado. Ejecuta: pip install redis"
            )
        except Exception as e:
            logger.warning(f"[RedisCacheService] No se pudo conectar: {e}")
            self._client = None

    def get(self, key: str) -> Any | None:
        if self._client is None:
            return None
        try:
            value = self._client.get(key)
            if value:
                logger.debug(f"[Cache HIT] {key}")
                return json.loads(value)
            logger.debug(f"[Cache MISS] {key}")
            return None
        except Exception as e:
            logger.warning(f"[Cache GET error] {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl_seconds: int = DEFAULT_TTL) -> None:
        if self._client is None:
            return
        try:
            self._client.setex(key, ttl_seconds, json.dumps(value, default=str))
            logger.debug(f"[Cache SET] {key} (ttl={ttl_seconds}s)")
        except Exception as e:
            logger.warning(f"[Cache SET error] {key}: {e}")

    def delete(self, key: str) -> None:
        if self._client is None:
            return
        try:
            self._client.delete(key)
            logger.debug(f"[Cache DEL] {key}")
        except Exception as e:
            logger.warning(f"[Cache DEL error] {key}: {e}")

    def invalidate(self, pattern: str) -> None:
        """Borra todas las claves que coincidan con el patrón (usa SCAN, no KEYS)."""
        if self._client is None:
            return
        try:
            cursor = 0
            deleted = 0
            while True:
                cursor, keys = self._client.scan(cursor, match=pattern, count=100)
                if keys:
                    self._client.delete(*keys)
                    deleted += len(keys)
                if cursor == 0:
                    break
            if deleted:
                logger.debug(f"[Cache INVALIDATE] {pattern} → {deleted} claves borradas")
        except Exception as e:
            logger.warning(f"[Cache INVALIDATE error] {pattern}: {e}")


# ─────────────────────────────────────────────────────────────
# ADAPTADOR EN MEMORIA (para tests y desarrollo)
# ─────────────────────────────────────────────────────────────
class InMemoryCacheService(CacheService):
    """
    Caché en memoria para tests y desarrollo local.
    No persiste entre reinicios — perfecto para tests unitarios.
    """

    def __init__(self):
        self._store: dict[str, Any] = {}

    def get(self, key: str) -> Any | None:
        return self._store.get(key)

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        # En memoria no manejamos TTL — suficiente para tests
        self._store[key] = value

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def invalidate(self, pattern: str) -> None:
        """Borra claves usando matching simple con *."""
        import fnmatch
        keys_to_delete = [k for k in self._store if fnmatch.fnmatch(k, pattern)]
        for key in keys_to_delete:
            del self._store[key]

    def clear(self) -> None:
        """Limpia toda la caché (útil entre tests)."""
        self._store.clear()

    def size(self) -> int:
        return len(self._store)
