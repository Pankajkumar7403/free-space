from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Start the notification event consumer"

    def handle(self, *args, **options):
        self.stdout.write(
            "run_notification_consumer command scaffold created. "
            "Add consumer loop implementation next."
        )
