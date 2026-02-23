#!/usr/bin/env python
"""Punto de entrada de Django."""
import os
import sys

# Esto asegura que la app Celery se inicialice cuando Django arranca,
# lo que es necesario para que las tareas se registren correctamente.
# Ref: https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html
try:
    from config.celery_app import app as celery_app  # noqa: F401
except Exception:
    pass


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. Verifica que esté instalado "
            "y activo en tu virtualenv."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
