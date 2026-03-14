"""
AppConfig para la app de persistencia.
Django necesita esto para registrar los modelos correctamente.
"""
from django.apps import AppConfig


class PersistenceConfig(AppConfig):
    name = "src.infrastructure.persistence"
    label = "persistence"          # debe coincidir con app_label en los modelos
    verbose_name = "Persistence"

    def ready(self):
        """Se ejecuta cuando Django termina de cargar la app."""
        # Importar admin para registrar los modelos en Django Admin
        import src.interfaces.admin.blog_admin  # noqa: F401
