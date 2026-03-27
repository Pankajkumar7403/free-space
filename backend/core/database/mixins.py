"""
core/database/mixins.py
~~~~~~~~~~~~~~~~~~~~~~~
Lightweight model mixins for cross-cutting concerns.
These are separate from BaseModel so they can be composed individually
when a model doesn't need the full BaseModel (e.g. through-tables).
"""

from __future__ import annotations

from django.db import models, transaction


class TransactionMixin:
    """
    Mixin for service classes (not models) that need atomic helpers.

    Usage in a service
    ------------------
        class PostService(TransactionMixin):
            def create(self, ...):
                with self.atomic():
                    ...
    """

    @staticmethod
    def atomic():
        return transaction.atomic()


class SlugMixin(models.Model):
    """
    Adds a unique slug field.  Auto-populated via signals or services.
    """

    slug = models.SlugField(max_length=255, unique=True, blank=True)

    class Meta:
        abstract = True


class OrderableMixin(models.Model):
    """
    Adds an integer `position` field for explicit ordering (e.g. media items).
    """

    position = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        abstract = True
        ordering = ["position"]


class UserStampMixin(models.Model):
    """
    Records who created / last updated a row.
    Use alongside TimestampMixin for a full audit trail.
    """

    created_by = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        abstract = True
