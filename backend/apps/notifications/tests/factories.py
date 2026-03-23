import factory
from factory.django import DjangoModelFactory

from apps.notifications.constants import DevicePlatform, NotificationType
from apps.notifications.models import DeviceToken, Notification, NotificationPreference


class NotificationFactory(DjangoModelFactory):
    class Meta:
        model = Notification

    recipient = factory.SubFactory("apps.users.tests.factories.UserFactory")
    actor = factory.SubFactory("apps.users.tests.factories.UserFactory")
    notification_type = NotificationType.FOLLOW
    message = factory.LazyAttribute(
        lambda o: f"{o.actor.username} started following you"
    )
    is_read = False


class NotificationPreferenceFactory(DjangoModelFactory):
    class Meta:
        model = NotificationPreference
        django_get_or_create = ("user",)

    user = factory.SubFactory("apps.users.tests.factories.UserFactory")


class DeviceTokenFactory(DjangoModelFactory):
    class Meta:
        model = DeviceToken
        django_get_or_create = ("user", "token")

    user = factory.SubFactory("apps.users.tests.factories.UserFactory")
    token = factory.Sequence(lambda n: f"fcm-token-{n:04d}")
    platform = DevicePlatform.IOS
    is_active = True
