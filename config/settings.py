"""
Django Settings — Library Blog Platform.
Configuración separada por entorno usando variables de entorno.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ─────────────────────────────────────────────────────────────
# SEGURIDAD
# ─────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-key-change-in-production")
DEBUG = os.getenv("DJANGO_DEBUG", "True") == "True"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# ─────────────────────────────────────────────────────────────
# GENERAL  ← movido aquí para que TIME_ZONE esté disponible
# ─────────────────────────────────────────────────────────────
LANGUAGE_CODE = "es-pe"
TIME_ZONE = "America/Lima"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─────────────────────────────────────────────────────────────
# APPS
# ─────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "rest_framework.authtoken",
    # Apps internas (solo los modelos ORM viven aquí)
    "src.infrastructure.persistence",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ─────────────────────────────────────────────────────────────
# BASE DE DATOS
# ─────────────────────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.getenv("DB_NAME", str(BASE_DIR / "db.sqlite3")),
        "USER": os.getenv("DB_USER", ""),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", ""),
        "PORT": os.getenv("DB_PORT", ""),
    }
}

# ─────────────────────────────────────────────────────────────
# DJANGO REST FRAMEWORK
# ─────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}

# ─────────────────────────────────────────────────────────────
# CACHE (Redis en prod, local mem en dev)
# ─────────────────────────────────────────────────────────────
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

CACHES = {
    "default": {
        "BACKEND": (
            "django.core.cache.backends.locmem.LocMemCache"
            if DEBUG
            else "django.core.cache.backends.redis.RedisCache"
        ),
        "LOCATION": REDIS_URL if not DEBUG else "",
    }
}

# ─────────────────────────────────────────────────────────────
# CELERY
# Docs: https://docs.celeryq.dev/en/stable/userguide/configuration.html
# Arrancar worker:  celery -A config.celery worker --loglevel=info
# Monitoreo:        celery -A config.celery flower --port=5555
# ─────────────────────────────────────────────────────────────
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

# Serialización
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]

# Zona horaria — TIME_ZONE ya está definido arriba ✅
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

# Comportamiento de tareas
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60        # 30 min máximo por tarea
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60   # warning a los 25 min
CELERY_TASK_ACKS_LATE = True            # confirma DESPUÉS de ejecutar (más seguro)
CELERY_WORKER_PREFETCH_MULTIPLIER = 1   # sin pre-fetch agresivo
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# Colas separadas por tipo de tarea
CELERY_TASK_ROUTES = {
    "dispatch_domain_event": {"queue": "domain_events"},
    "health_check":          {"queue": "celery"},
}

# ─────────────────────────────────────────────────────────────
# ENTORNO
# ─────────────────────────────────────────────────────────────
DJANGO_ENV = os.getenv("DJANGO_ENV", "development")  # development | production | test
