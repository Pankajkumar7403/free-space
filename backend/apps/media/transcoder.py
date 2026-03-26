# 📁 Location: backend/apps/media/transcoder.py

from __future__ import annotations

import logging
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings

from apps.media.storage import build_s3_key
from apps.posts.constants import MediaType

logger = logging.getLogger(__name__)

# ── Transcoding targets ───────────────────────────────────────────────────────
IMAGE_MAX_WIDTH = 1080
IMAGE_MAX_HEIGHT = 1080
IMAGE_QUALITY = 85  # JPEG quality (0-100)
VIDEO_CRF = 23  # H.264 CRF (lower = higher quality, 23 is default)
VIDEO_PRESET = "fast"
THUMBNAIL_WIDTH = 400
THUMBNAIL_HEIGHT = 400


@dataclass
class TranscodeResult:
    processed_key: str
    thumbnail_key: str
    width: int | None = None
    height: int | None = None
    duration: float | None = None


def transcode_media(media) -> TranscodeResult:
    """
    Entry point called by process_media_task.
    Downloads from S3, runs FFmpeg, uploads results, returns keys.

    In test environments (USE_FAKE_S3=True), returns mock result
    without actually calling FFmpeg or S3.
    """
    if getattr(settings, "USE_FAKE_S3", False):
        return _mock_transcode_result(media)

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = _download_from_s3(media.original_key, tmpdir)

        if media.media_type == MediaType.IMAGE:
            return _transcode_image(media, input_path, tmpdir)
        else:
            return _transcode_video(media, input_path, tmpdir)


def _transcode_image(media, input_path: Path, tmpdir: str) -> TranscodeResult:
    """Resize image to max 1080×1080, generate 400×400 thumbnail."""
    processed_path = Path(tmpdir) / "processed.jpg"
    thumbnail_path = Path(tmpdir) / "thumbnail.jpg"

    # Resize main image
    _run_ffmpeg(
        [
            "ffmpeg",
            "-i",
            str(input_path),
            "-vf",
            f"scale='min({IMAGE_MAX_WIDTH},iw)':'min({IMAGE_MAX_HEIGHT},ih)':force_original_aspect_ratio=decrease",
            "-qscale:v",
            str(IMAGE_QUALITY),
            str(processed_path),
            "-y",
        ]
    )

    # Generate thumbnail
    _run_ffmpeg(
        [
            "ffmpeg",
            "-i",
            str(input_path),
            "-vf",
            f"scale={THUMBNAIL_WIDTH}:{THUMBNAIL_HEIGHT}:force_original_aspect_ratio=increase,crop={THUMBNAIL_WIDTH}:{THUMBNAIL_HEIGHT}",
            str(thumbnail_path),
            "-y",
        ]
    )

    # Get dimensions from processed image
    width, height = _get_image_dimensions(processed_path)

    processed_key = build_s3_key("processed", "image/jpeg")
    thumbnail_key = build_s3_key("thumbnails", "image/jpeg")

    _upload_to_s3(processed_path, processed_key, "image/jpeg")
    _upload_to_s3(thumbnail_path, thumbnail_key, "image/jpeg")

    return TranscodeResult(
        processed_key=processed_key,
        thumbnail_key=thumbnail_key,
        width=width,
        height=height,
    )


def _transcode_video(media, input_path: Path, tmpdir: str) -> TranscodeResult:
    """Compress video to H.264/AAC, extract first-frame thumbnail."""
    processed_path = Path(tmpdir) / "processed.mp4"
    thumbnail_path = Path(tmpdir) / "thumbnail.jpg"

    # Compress video
    _run_ffmpeg(
        [
            "ffmpeg",
            "-i",
            str(input_path),
            "-c:v",
            "libx264",
            "-crf",
            str(VIDEO_CRF),
            "-preset",
            VIDEO_PRESET,
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            str(processed_path),
            "-y",
        ]
    )

    # Extract first frame as thumbnail
    _run_ffmpeg(
        [
            "ffmpeg",
            "-i",
            str(input_path),
            "-vframes",
            "1",
            "-an",
            "-vf",
            f"scale={THUMBNAIL_WIDTH}:{THUMBNAIL_HEIGHT}:force_original_aspect_ratio=increase,crop={THUMBNAIL_WIDTH}:{THUMBNAIL_HEIGHT}",
            str(thumbnail_path),
            "-y",
        ]
    )

    duration = _get_video_duration(input_path)
    width, height = _get_image_dimensions(thumbnail_path)

    processed_key = build_s3_key("processed", "video/mp4")
    thumbnail_key = build_s3_key("thumbnails", "image/jpeg")

    _upload_to_s3(processed_path, processed_key, "video/mp4")
    _upload_to_s3(thumbnail_path, thumbnail_key, "image/jpeg")

    return TranscodeResult(
        processed_key=processed_key,
        thumbnail_key=thumbnail_key,
        width=width,
        height=height,
        duration=duration,
    )


# ── FFmpeg helpers ─────────────────────────────────────────────────────────────


def _run_ffmpeg(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {result.stderr.decode()}")


def _get_image_dimensions(path: Path) -> tuple[int | None, int | None]:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_streams",
                str(path),
            ],
            capture_output=True,
            text=True,
        )
        import json

        data = json.loads(result.stdout)
        stream = data.get("streams", [{}])[0]
        return stream.get("width"), stream.get("height")
    except Exception:
        return None, None


def _get_video_duration(path: Path) -> float | None:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                str(path),
            ],
            capture_output=True,
            text=True,
        )
        import json

        data = json.loads(result.stdout)
        return float(data.get("format", {}).get("duration", 0)) or None
    except Exception:
        return None


def _download_from_s3(s3_key: str, tmpdir: str) -> Path:
    import boto3
    from django.conf import settings

    bucket = settings.AWS_STORAGE_BUCKET_NAME
    local_path = Path(tmpdir) / "input"
    boto3.client("s3").download_file(bucket, s3_key, str(local_path))
    return local_path


def _upload_to_s3(local_path: Path, s3_key: str, content_type: str) -> None:
    import boto3
    from django.conf import settings

    bucket = settings.AWS_STORAGE_BUCKET_NAME
    boto3.client("s3").upload_file(
        str(local_path),
        bucket,
        s3_key,
        ExtraArgs={"ContentType": content_type, "ACL": "public-read"},
    )


def _mock_transcode_result(media) -> TranscodeResult:
    """Returns a fake result for test/dev environments."""
    return TranscodeResult(
        processed_key=f"processed/mock/{media.id}.jpg",
        thumbnail_key=f"thumbnails/mock/{media.id}.jpg",
        width=1080,
        height=1080,
        duration=None,
    )
