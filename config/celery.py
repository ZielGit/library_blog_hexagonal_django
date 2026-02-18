"""
Alias de entrada para Celery.

Django y Celery buscan este módulo con el comando:
    celery -A config worker ...
    celery -A config.celery worker ...

Este archivo simplemente re-exporta todo desde celery_app.py

Referencia: https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html
"""
from config.celery_app import app, dispatch_domain_event, health_check

# Hace que Celery encuentre la app al usar -A config
# (busca config.celery.app o config.celery_app.app)
__all__ = ("app", "dispatch_domain_event", "health_check")
