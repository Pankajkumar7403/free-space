from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.db.models import CheckConstraint, Q, UniqueConstraint


class Report(models.Model):
    REASON_CHOICES = [
        ("harassment",       "Harassment"),
        ("hate_speech",      "Hate Speech"),
        ("abuse",            "Abuse"),
        ("explicit_content", "Explicit Content"),
        ("other",            "Other"),
    ]
    STATUS_CHOICES = [
        ("pending",   "Pending"),
        ("reviewed",  "Reviewed"),
        ("dismissed", "Dismissed"),
    ]

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at       = models.DateTimeField(auto_now_add=True)
    reporter         = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="common_reports_filed"
    )
    reported_user    = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="common_reports_received"
    )
    reported_post    = models.ForeignKey(
        "posts.Post", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="reports"
    )
    reported_comment = models.ForeignKey(
        "comments.Comment", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="reports"
    )
    reason  = models.CharField(max_length=32, choices=REASON_CHOICES)
    details = models.TextField(blank=True)
    status  = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")

    class Meta:
        constraints = [
            CheckConstraint(
                condition=(
                    Q(reported_user__isnull=False, reported_post__isnull=True,    reported_comment__isnull=True) |
                    Q(reported_user__isnull=True,  reported_post__isnull=False,   reported_comment__isnull=True) |
                    Q(reported_user__isnull=True,  reported_post__isnull=True,    reported_comment__isnull=False)
                ),
                name="report_exactly_one_target",
            ),
            UniqueConstraint(
                fields=["reporter", "reported_user"],
                condition=Q(reported_user__isnull=False),
                name="unique_report_per_user",
            ),
            UniqueConstraint(
                fields=["reporter", "reported_post"],
                condition=Q(reported_post__isnull=False),
                name="unique_report_per_post",
            ),
            UniqueConstraint(
                fields=["reporter", "reported_comment"],
                condition=Q(reported_comment__isnull=False),
                name="unique_report_per_comment",
            ),
        ]

    def __str__(self) -> str:
        return f"Report({self.reason}) by {self.reporter_id}"
