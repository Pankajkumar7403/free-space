# 📁 Location: backend/apps/likes/tasks.py

from __future__ import annotations

import logging

from celery import shared_task

from apps.likes.constants import CT_COMMENT, CT_POST

logger = logging.getLogger(__name__)


@shared_task(name="likes.reconcile_counts")
def reconcile_like_counts() -> None:
    """
    Celery periodic task: sync Redis like counts back to the DB.

    Runs every 5 minutes (configured in CELERY_BEAT_SCHEDULE).
    Reads current DB counts, writes them to Redis so counts
    survive Redis restarts.

    Why periodic reconciliation?
    - Redis counters can drift if a worker crashes mid-pipeline
    - Redis data expires (LIKE_COUNTER_TTL = 24h)
    - This task is the safety net that keeps counts accurate
    """
    from apps.likes.cache import set_like_count
    from apps.likes.models import Like
    from django.contrib.contenttypes.models import ContentType
    from django.db.models import Count

    # Aggregate DB counts per (content_type, object_id)
    counts = (
        Like.objects
        .values("content_type_id", "object_id")
        .annotate(total=Count("id"))
    )

    ct_map = {ct.pk: ct.model for ct in ContentType.objects.all()}

    for row in counts:
        ct_label  = ct_map.get(row["content_type_id"], "unknown")
        object_id = str(row["object_id"])
        total     = row["total"]
        set_like_count(ct_label, object_id, total)

    logger.info("reconcile_like_counts: synced %d counters to Redis", len(counts))