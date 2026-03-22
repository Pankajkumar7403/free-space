# 📁 Location: backend/apps/feed/management/commands/run_feed_consumer.py
# ▶  Run:      uv run manage.py run_feed_consumer

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Start the Kafka consumer for feed fanout events"

    def handle(self, *args, **options):
        from apps.feed.events import FeedKafkaConsumer
        self.stdout.write("Starting FeedKafkaConsumer...")
        consumer = FeedKafkaConsumer(group_id="feed-service")
        consumer.start()