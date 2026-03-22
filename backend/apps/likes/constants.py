# 📁 Location: backend/apps/likes/constants.py

# Redis key TTL for like counters (24h — reconciled to DB before expiry)
LIKE_COUNTER_TTL = 60 * 60 * 24

# Celery reconciliation interval in seconds (every 5 minutes)
RECONCILE_INTERVAL = 60 * 5

# Likeable content type labels (used in Redis keys)
CT_POST    = "post"
CT_COMMENT = "comment"