from django.apps import AppConfig


class MessagingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.messaging"
    label = "messaging"  # avoid collision with django.contrib.messages

    def ready(self) -> None:
        return
