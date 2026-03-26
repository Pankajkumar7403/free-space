"""
Reusable test mixins.

Mix these into any TestCase subclass to get focused, opt-in behaviours
without polluting the base classes.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class CacheMixin:
    """
    Disable cache reads/writes for the duration of a test.

    Use when testing service logic that calls cache.get() / cache.set()
    and you want deterministic behaviour without cache side-effects.
    """

    def setUp(self) -> None:
        super().setUp()  # type: ignore[misc]
        self._cache_patcher = patch("django.core.cache.cache")
        self.mock_cache: MagicMock = self._cache_patcher.start()
        self.mock_cache.get.return_value = None  # cache always misses by default

    def tearDown(self) -> None:
        self._cache_patcher.stop()
        super().tearDown()  # type: ignore[misc]


class CeleryEagerMixin:
    """
    Ensure Celery tasks run synchronously inside tests.
    Useful as belt-and-suspenders alongside CELERY_TASK_ALWAYS_EAGER.
    """

    def setUp(self) -> None:
        super().setUp()  # type: ignore[misc]
        from django.test.utils import override_settings

        self._celery_override = override_settings(
            CELERY_TASK_ALWAYS_EAGER=True,
            CELERY_TASK_EAGER_PROPAGATES=True,
        )
        self._celery_override.enable()

    def tearDown(self) -> None:
        self._celery_override.disable()
        super().tearDown()  # type: ignore[misc]


class S3MockMixin:
    """
    Mock S3 / object storage calls so media tests don't hit real buckets.
    """

    def setUp(self) -> None:
        super().setUp()  # type: ignore[misc]
        self._s3_patcher = patch("storages.backends.s3boto3.S3Boto3Storage.save")
        self.mock_s3_save: MagicMock = self._s3_patcher.start()
        self.mock_s3_save.return_value = "mocked/path/to/file.jpg"

    def tearDown(self) -> None:
        self._s3_patcher.stop()
        super().tearDown()  # type: ignore[misc]


class KafkaMockMixin:
    """
    Mock Kafka producer so event-emitting services don't need a broker.
    """

    def setUp(self) -> None:
        super().setUp()  # type: ignore[misc]
        self._kafka_patcher = patch("core.kafka.producer.KafkaProducer.send")
        self.mock_kafka_send: MagicMock = self._kafka_patcher.start()

    def tearDown(self) -> None:
        self._kafka_patcher.stop()
        super().tearDown()  # type: ignore[misc]

    def assert_event_emitted(self, topic: str) -> None:
        calls = [str(call) for call in self.mock_kafka_send.call_args_list]
        self.assertTrue(  # type: ignore[attr-defined]
            any(topic in c for c in calls),
            msg=f"Expected a Kafka event on topic {topic!r}, got calls: {calls}",
        )
