from django.apps import AppConfig

class AgrovetConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.agrovet'

    def ready(self):
        # We can pre-load the ML models on startup if desired.
        # Alternatively, lazy loading is handled by the MLEngine.
        # For this setup, we'll let MLEngine lazy-load them on first request 
        # to speed up development server reload times.
        pass
