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

# ── Cache ───────────────────────────────j──────────────────────────────────────
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
DEFAULT_FILE_STORAGE = "django.core.files.storage.InMemoryStorage"

# ── Security ──────────────────────────────────────────────────────────────────
SECRET_KEY = "test-secret-key-not-for-production"
DEBUG = True
ALLOWED_HOSTS = ["*"]