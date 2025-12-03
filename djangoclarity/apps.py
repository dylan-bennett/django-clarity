from django.apps import AppConfig


class DjangoclarityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "djangoclarity"
    verbose_name = "Django Clarity"

    def ready(self):
        # Ensure django-bootstrap5 is installed
        try:
            import django_bootstrap5
        except ImportError:
            raise ImportError(
                "django-bootstrap5 is required. Install it with: pip install django-bootstrap5"
            )
