"""
core/database/managers.py
~~~~~~~~~~~~~~~~~~~~~~~~~
Custom managers that work with our soft-delete pattern.
"""
from __future__ import annotations

from django.db import models


class SoftDeleteQuerySet(models.QuerySet):
    """
    QuerySet with bulk soft-delete / restore support.

    Usage
    -----
        Post.objects.filter(author=user).soft_delete()
        Post.objects.filter(author=user).restore()
    """

    def soft_delete(self) -> int:
        from django.utils import timezone
        return self.update(is_deleted=True, deleted_at=timezone.now())

    def restore(self) -> int:
        return self.update(is_deleted=False, deleted_at=None)

    def alive(self) -> "SoftDeleteQuerySet":
        return self.filter(is_deleted=False)

    def deleted(self) -> "SoftDeleteQuerySet":
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    """
    Default manager that automatically excludes soft-deleted rows.

    Any queryset from `Model.objects.*` will only return live rows.
    Use `Model.all_objects.*` when you need the full table.
    """

    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)

    def alive(self) -> SoftDeleteQuerySet:
        return self.get_queryset()

    def deleted(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=True)