import pytest

from apps.notifications.tests.factories import (
    DeviceTokenFactory,
    NotificationFactory,
    NotificationPreferenceFactory,
)


@pytest.fixture
def notification_factory(db):
    def _create(**kwargs):
        return NotificationFactory(**kwargs)

    return _create


@pytest.fixture
def notification_preference_factory(db):
    def _create(**kwargs):
        return NotificationPreferenceFactory(**kwargs)

    return _create


@pytest.fixture
def device_token_factory(db):
    def _create(**kwargs):
        return DeviceTokenFactory(**kwargs)

    return _create
