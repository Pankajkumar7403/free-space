# 📁 Location: backend/apps/users/tests/factories.py
import factory
from django.contrib.auth import get_user_model

from core.testing.factories import BaseFactory

User = get_user_model()


class UserFactory(BaseFactory):
    class Meta:
        model = User

    username   = factory.Sequence(lambda n: f"user_{n}")
    email      = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name  = factory.Faker("last_name")
    password   = factory.PostGenerationMethodCall("set_password", "testpass123")
    is_active  = True

    class Params:
        staff = factory.Trait(is_staff=True)
        admin = factory.Trait(is_staff=True, is_superuser=True)
        inactive = factory.Trait(is_active=False)