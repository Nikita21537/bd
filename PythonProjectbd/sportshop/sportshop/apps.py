from django.apps import AppConfig


class SportshopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sportshop'

    def ready(self):
        import sportshop.signals