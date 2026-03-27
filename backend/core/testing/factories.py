"""
Base factory classes.

All app-level factories should inherit from DjangoModelFactory
through these base classes so common behaviour (e.g. trait helpers)
lives in one place.

Requires: factory-boy
"""

from __future__ import annotations

from factory.django import DjangoModelFactory


class BaseFactory(DjangoModelFactory):
    """
    Root factory all app factories inherit from.

    Convention
    ----------
    - Use ``factory.Sequence`` for unique fields (username, email, …).
    - Use ``factory.SubFactory`` for FK relations.
    - Use ``factory.Trait`` for common states (e.g. ``is_staff``).
    - Always define ``class Meta: model = ...``
    """

    class Meta:
        abstract = True

    @classmethod
    def build_batch_as_list(cls, size: int, **kwargs: object) -> list:
        """build_batch returns a list; this is an explicit alias for clarity."""
        return cls.build_batch(size, **kwargs)

    @classmethod
    def create_batch_as_list(cls, size: int, **kwargs: object) -> list:
        return cls.create_batch(size, **kwargs)


# ── Example – extend this in apps/users/tests/factories.py ───────────────────
#
# from core.testing.factories import BaseFactory
# from apps.users.models import User
#
# class UserFactory(BaseFactory):
#     class Meta:
#         model = User
#
#     username  = factory.Sequence(lambda n: f"user_{n}")
#     email     = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
#     password  = factory.PostGenerationMethodCall("set_password", "testpass123")
#     is_active = True
#
#     class Params:
#         staff = factory.Trait(is_staff=True)
#         admin = factory.Trait(is_staff=True, is_superuser=True)
