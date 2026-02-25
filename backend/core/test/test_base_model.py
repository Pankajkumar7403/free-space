# 📁 Location: backend/core/tests/test_base_model.py
# ▶  Run:      pytest core/tests/test_base_model.py -v
"""
test_base_model.py
~~~~~~~~~~~~~~~~~~
Tests for core/database/base_model.py

Covers:
  - UUID primary key generation
  - created_at / updated_at auto-set
  - SoftDelete: soft_delete(), restore(), hard_delete()
  - SoftDeleteManager: live-only queryset by default
  - SoftDeleteQuerySet: bulk soft_delete() / restore()

These use a concrete proxy model (TestItem) so we don't need
a real app migration — Django creates it in the test DB via
@pytest.mark.django_db(databases=["default"]).
"""
from __future__ import annotations

import uuid
from datetime import timedelta

import pytest
from django.db import models
from django.utils import timezone

from core.database.base_model import BaseModel


# ── Concrete test model ───────────────────────────────────────────────────────
# We define a minimal model inline.
# In tests that use @pytest.mark.django_db, Django's test runner will
# create this table automatically when we use --create-db.
# We register it via the apps registry inside the test module.

class Article(BaseModel):
    """Minimal concrete model used only in this test module."""
    title = models.CharField(max_length=255, default="untitled")

    class Meta:
        app_label = "common"   # must match an INSTALLED_APPS entry


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def article(db) -> Article:
    return Article.objects.create(title="Hello World")


@pytest.fixture
def deleted_article(db) -> Article:
    a = Article.objects.create(title="Deleted")
    a.soft_delete()
    return a


# ── Tests ─────────────────────────────────────────────────────────────────────

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


class TestUUIDPrimaryKey:
    def test_pk_is_uuid(self, article):
        assert isinstance(article.id, uuid.UUID)

    def test_pk_is_unique(self, db):
        a1 = Article.objects.create(title="one")
        a2 = Article.objects.create(title="two")
        assert a1.id != a2.id

    def test_pk_is_auto_assigned(self, db):
        a = Article(title="no pk set")
        assert a.id is not None   # default=uuid.uuid4 fires before save


class TestTimestamps:
    def test_created_at_is_set_on_create(self, article):
        assert article.created_at is not None

    def test_updated_at_is_set_on_create(self, article):
        assert article.updated_at is not None

    def test_updated_at_changes_on_save(self, article):
        original = article.updated_at
        article.title = "changed"
        article.save(update_fields=["title"])
        article.refresh_from_db()
        assert article.updated_at > original

    def test_created_at_does_not_change_on_save(self, article):
        original = article.created_at
        article.title = "changed"
        article.save(update_fields=["title"])
        article.refresh_from_db()
        assert article.created_at == original


class TestSoftDelete:
    def test_soft_delete_sets_is_deleted(self, article):
        article.soft_delete()
        article.refresh_from_db()
        # Use all_objects to bypass SoftDeleteManager filter
        raw = Article.all_objects.get(pk=article.pk)
        assert raw.is_deleted is True

    def test_soft_delete_sets_deleted_at(self, article):
        before = timezone.now()
        article.soft_delete()
        article.refresh_from_db()
        raw = Article.all_objects.get(pk=article.pk)
        assert raw.deleted_at >= before

    def test_soft_deleted_row_hidden_from_default_manager(self, article):
        article.soft_delete()
        assert not Article.objects.filter(pk=article.pk).exists()

    def test_restore_clears_flags(self, deleted_article):
        deleted_article.restore()
        deleted_article.refresh_from_db()
        raw = Article.all_objects.get(pk=deleted_article.pk)
        assert raw.is_deleted is False
        assert raw.deleted_at is None

    def test_restore_makes_row_visible_again(self, deleted_article):
        deleted_article.restore()
        assert Article.objects.filter(pk=deleted_article.pk).exists()

    def test_hard_delete_removes_row_permanently(self, article):
        pk = article.pk
        article.hard_delete()
        assert not Article.all_objects.filter(pk=pk).exists()


class TestSoftDeleteManager:
    def test_objects_excludes_deleted(self, article, deleted_article):
        live_pks = list(Article.objects.values_list("pk", flat=True))
        assert article.pk in live_pks
        assert deleted_article.pk not in live_pks

    def test_all_objects_includes_deleted(self, article, deleted_article):
        all_pks = list(Article.all_objects.values_list("pk", flat=True))
        assert article.pk in all_pks
        assert deleted_article.pk in all_pks

    def test_alive_queryset(self, article, deleted_article):
        alive = list(Article.objects.alive().values_list("pk", flat=True))
        assert article.pk in alive
        assert deleted_article.pk not in alive

    def test_deleted_queryset(self, article, deleted_article):
        deleted = list(Article.objects.deleted().values_list("pk", flat=True))
        assert deleted_article.pk in deleted
        assert article.pk not in deleted


class TestBulkSoftDelete:
    def test_bulk_soft_delete(self, db):
        a1 = Article.objects.create(title="a1")
        a2 = Article.objects.create(title="a2")
        Article.objects.filter(pk__in=[a1.pk, a2.pk]).soft_delete()

        assert not Article.objects.filter(pk__in=[a1.pk, a2.pk]).exists()

    def test_bulk_restore(self, db):
        a1 = Article.objects.create(title="a1")
        a2 = Article.objects.create(title="a2")
        Article.objects.filter(pk__in=[a1.pk, a2.pk]).soft_delete()
        Article.all_objects.filter(pk__in=[a1.pk, a2.pk]).restore()

        assert Article.objects.filter(pk__in=[a1.pk, a2.pk]).count() == 2