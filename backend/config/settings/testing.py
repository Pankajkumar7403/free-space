# 📁 Location: backend/config/settings/testing.py
# 🔧 Usage:    export DJANGO_SETTINGS_MODULE=config.settings.testing
#              pytest uses this automatically via pyproject.toml

from .base import *  # noqa: F401, F403

# ── Speed ────────────────────────────────────────────────────────────────────
# Use a fast in-memory hasher so unit tests aren't bottlenecked by bcrypt.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# ── Database ─────────────────────────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "fs_test_db",
        "USER": "fs_user",
        "PASSWORD": "fs_password",
        "HOST": "localhost",
        "PORT": "5432",
        # Wrap every test in a transaction and roll back → no teardown cost.
        "TEST": {
            "NAME": "fs_test_db",
        },
    }
}

# ── Cache ─────────────────────────────────────────────────────────────────────
# Use a local-memory cache so tests never touch Redis.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# ── Celery ────────────────────────────────────────────────────────────────────
# Run tasks eagerly (synchronously) so tests don't need a broker.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# ── Email ─────────────────────────────────────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# ── Media / Storage ───────────────────────────────────────────────────────────
USE_S3 = False
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.InMemoryStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# ── Security ──────────────────────────────────────────────────────────────────
SECRET_KEY = "test-secret-key-not-for-production-must-be-at-least-32-bytes-long-xxxx"
DEBUG = True
ALLOWED_HOSTS = ["*"]

# ── S3 / Media ────────────────────────────────────────────────────────────────
# Tests never hit real S3 — storage.py checks this flag
USE_FAKE_S3 = True
AWS_STORAGE_BUCKET_NAME = "test-bucket"
CDN_DOMAIN = "cdn.example.com"