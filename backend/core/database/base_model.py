"""
core/database/base_model.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Foundation model every app model inherits from.

Features
--------
- UUID primary key        → no sequential ID guessing, safe in URLs
- created_at / updated_at → auto-managed timestamps (always UTC)
- SoftDeleteMixin         → deleted=True hides rows without data loss
- TransactionMixin        → convenience helpers for atomic blocks

Usage
-----
    from core.database.base_model import BaseModel

    class Post(BaseModel):
        content = models.TextField()
        # inherits: id (UUID), created_at, updated_at, is_deleted
"""

from __future__ import annotations

import uuid

from django.db import models

from core.database.managers import SoftDeleteManager, SoftDeleteQuerySet


class TimestampMixin(models.Model):
    """Adds auto-managed created_at / updated_at to any model."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):  # type: ignore[override]
        update_fields = kwargs.get("update_fields")
        if update_fields is not None and "updated_at" not in update_fields:
            kwargs["update_fields"] = list(update_fields) + ["updated_at"]
        return super().save(*args, **kwargs)


class SoftDeleteMixin(models.Model):
    """
    Soft-delete support.

    Instead of DELETE FROM table, we set is_deleted=True.
    The default manager (SoftDeleteManager) automatically filters
    out deleted rows so all normal queries are unaffected.

    Methods
    -------
    soft_delete()   Mark the row as deleted and save.
    restore()       Undo a soft delete.
    hard_delete()   Permanently remove the row (audit/admin use only).
    """

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Replace the default manager with our soft-delete-aware one.
    objects = SoftDeleteManager()
    # Keep a backdoor for admin/migrations that need ALL rows.
    all_objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        abstract = True

    def soft_delete(self) -> None:
        from django.utils import timezone

        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def restore(self) -> None:
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at"])

    def hard_delete(self) -> None:
        super().delete()  # type: ignore[misc]


class BaseModel(TimestampMixin, SoftDeleteMixin):
    """
    Root abstract model for all Qommunity domain models.

    Provides:
      id          UUID primary key (non-sequential, URL-safe)
      created_at  auto-set on INSERT
      updated_at  auto-set on every UPDATE
      is_deleted  soft-delete flag (default False)
      deleted_at  timestamp of soft deletion (null if not deleted)
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    class Meta:
        abstract = True
        # Subclasses should define their own ordering.
        ordering = ["-created_at"]

    def __repr__(self) -> str:  # pragma: no cover
        return f"<{self.__class__.__name__} id={self.id}>"
