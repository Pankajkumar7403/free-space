from .base import *

DEBUG = True
ALLOWED_HOSTS = ["*"]

# ── Channels ──────────────────────────────────────────────────────────────────
# Uses base.py CHANNEL_LAYERS (Redis via REDIS_URL). No override needed here.