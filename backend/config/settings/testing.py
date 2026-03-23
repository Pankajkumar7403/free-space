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
        "NAME": os.getenv("POSTGRES_TEST_DB", "fs_test_db"),
        "USER": os.getenv("POSTGRES_TEST_USER", os.getenv("POSTGRES_USER", "qommunity_user")),
        "PASSWORD": os.getenv("POSTGRES_TEST_PASSWORD", os.getenv("POSTGRES_PASSWORD", "qommunity_password")),
        "HOST": os.getenv("POSTGRES_TEST_HOST", os.getenv("POSTGRES_HOST", "localhost")),
        "PORT": os.getenv("POSTGRES_TEST_PORT", os.getenv("POSTGRES_PORT", "5432")),
        # Wrap every test in a transaction and roll back → no teardown cost.
        "TEST": {
            "NAME": os.getenv("POSTGRES_TEST_NAME", "test_fs_test_db"),
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

# ── Channels ──────────────────────────────────────────────────────────────────
# Use in-memory channel layer so tests don't require Redis.
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}

# ── Celery ────────────────────────────────────────────────────────────────────
# Run tasks eagerly (synchronously) so tests don't need a broker.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# ── Email ─────────────────────────────────────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# ── External services (disabled for tests) ───────────────────────────────────
FCM_SERVER_KEY = ""
SENDGRID_API_KEY = ""

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