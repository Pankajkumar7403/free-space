"""
apps/common/moderation/image_classifier.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
NSFW image detection using AWS Rekognition (production) or
a stub (development/testing).

The backend is selected by the NSFW_CLASSIFIER_BACKEND setting:
  "rekognition"   ->  AWS Rekognition (production)
  "stub"          ->  Always returns PASS (dev/test)
  "local"         ->  Run a local ONNX model (future M8)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

from django.conf import settings

from apps.common.moderation.constants import (
    NSFW_BLOCK_CONFIDENCE,
    NSFW_WARN_CONFIDENCE,
    ModerationAction,
    ModerationSeverity,
)

logger = logging.getLogger(__name__)


@dataclass
class ImageModerationResult:
    action:      ModerationAction
    severity:    ModerationSeverity
    confidence:  float          # 0.0 - 1.0
    label:       str = ""
    explanation: str = ""


def classify_image(s3_key: str) -> ImageModerationResult:
    """
    Classify an image stored in S3 for NSFW content.
    Dispatches to the configured backend.
    """
    backend = getattr(settings, "NSFW_CLASSIFIER_BACKEND", "stub")

    if backend == "rekognition":
        return _rekognition_classify(s3_key)
    else:
        return _stub_classify(s3_key)


def _rekognition_classify(s3_key: str) -> ImageModerationResult:
    """Use AWS Rekognition DetectModerationLabels."""
    try:
        import boto3
        client = boto3.client(
            "rekognition",
            region_name=getattr(settings, "AWS_S3_REGION_NAME", "us-east-1"),
        )
        response = client.detect_moderation_labels(
            Image={
                "S3Object": {
                    "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
                    "Name": s3_key,
                }
            },
            MinConfidence=50.0,
        )
        labels = response.get("ModerationLabels", [])

        if not labels:
            return _pass_result()

        # Find highest-confidence explicit label
        top = max(labels, key=lambda x: x["Confidence"])
        confidence = top["Confidence"] / 100.0
        label      = top["Name"]

        if confidence >= NSFW_BLOCK_CONFIDENCE:
            return ImageModerationResult(
                action=ModerationAction.BLOCK,
                severity=ModerationSeverity.HIGH,
                confidence=confidence,
                label=label,
                explanation=f"Image classified as '{label}' with {confidence:.0%} confidence.",
            )
        if confidence >= NSFW_WARN_CONFIDENCE:
            return ImageModerationResult(
                action=ModerationAction.WARN,
                severity=ModerationSeverity.MEDIUM,
                confidence=confidence,
                label=label,
                explanation=f"Image may contain '{label}' content.",
            )
        return _pass_result()

    except Exception as exc:
        logger.error(
            "image_classifier.rekognition_failed",
            extra={"s3_key": s3_key, "error": str(exc)},
        )
        return _pass_result()   # Fail open on errors


def _stub_classify(s3_key: str) -> ImageModerationResult:
    """Development stub - always passes."""
    return _pass_result()


def _pass_result() -> ImageModerationResult:
    return ImageModerationResult(
        action=ModerationAction.PASS,
        severity=ModerationSeverity.LOW,
        confidence=0.0,
    )
