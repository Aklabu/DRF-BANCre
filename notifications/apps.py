from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name               = 'notifications'

    def ready(self):
        # Register all signal handlers — imported here to avoid duplicate firing
        import notifications.signals