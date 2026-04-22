from .base import *

DEBUG = True
ALLOWED_HOSTS = ["*"]

# ── Channels ──────────────────────────────────────────────────────────────────
# Uses base.py CHANNEL_LAYERS (Redis via REDIS_URL). No override needed here.

# Temporary local-dev stability: avoid external Redis auth/connect dependency
# while auth/session flow is being stabilized.
USE_FAKEREDIS = True
