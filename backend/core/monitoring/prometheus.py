"""
core/monitoring/prometheus.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Single registry of all Prometheus custom metrics for Qommunity.

Metrics naming convention (Prometheus best practices):
  <namespace>_<subsystem>_<name>_<unit>
  e.g.  qommunity_http_request_duration_seconds

Import these objects wherever you need to record a metric - they are
module-level singletons, safe for multi-process use via prometheus_client.
"""
from prometheus_client import Counter, Gauge, Histogram, Summary

# -- HTTP ---------------------------------------------------------------------

HTTP_REQUEST_DURATION = Histogram(
    "qommunity_http_request_duration_seconds",
    "End-to-end HTTP request duration",
    labelnames=["method", "endpoint", "status_code"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

HTTP_REQUEST_TOTAL = Counter(
    "qommunity_http_requests_total",
    "Total HTTP requests",
    labelnames=["method", "endpoint", "status_code"],
)

HTTP_REQUEST_IN_PROGRESS = Gauge(
    "qommunity_http_requests_in_progress",
    "HTTP requests currently being handled",
    labelnames=["method", "endpoint"],
)

# -- Database -----------------------------------------------------------------

DB_QUERY_TOTAL = Counter(
    "qommunity_db_queries_total",
    "Total database queries executed",
    labelnames=["app_label"],
)

DB_SLOW_QUERY_TOTAL = Counter(
    "qommunity_db_slow_queries_total",
    "DB queries exceeding the slow-query threshold (>100ms)",
    labelnames=["app_label"],
)

# -- Redis --------------------------------------------------------------------

REDIS_OPERATIONS_TOTAL = Counter(
    "qommunity_redis_operations_total",
    "Redis operations by type",
    labelnames=["operation", "result"],   # result: hit | miss | error
)

REDIS_CONNECTION_ERRORS = Counter(
    "qommunity_redis_connection_errors_total",
    "Redis connection errors",
)

# -- Kafka --------------------------------------------------------------------

KAFKA_MESSAGES_PRODUCED = Counter(
    "qommunity_kafka_messages_produced_total",
    "Kafka messages produced",
    labelnames=["topic"],
)

KAFKA_MESSAGES_CONSUMED = Counter(
    "qommunity_kafka_messages_consumed_total",
    "Kafka messages consumed",
    labelnames=["topic", "consumer_group"],
)

KAFKA_CONSUMER_LAG = Gauge(
    "qommunity_kafka_consumer_lag",
    "Kafka consumer lag (messages behind)",
    labelnames=["topic", "consumer_group"],
)

KAFKA_PRODUCE_ERRORS = Counter(
    "qommunity_kafka_produce_errors_total",
    "Kafka produce errors",
    labelnames=["topic"],
)

# -- Celery -------------------------------------------------------------------

CELERY_TASKS_TOTAL = Counter(
    "qommunity_celery_tasks_total",
    "Celery tasks executed",
    labelnames=["task_name", "state"],    # state: success | failure | retry
)

CELERY_TASK_DURATION = Histogram(
    "qommunity_celery_task_duration_seconds",
    "Celery task execution duration",
    labelnames=["task_name"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

CELERY_QUEUE_DEPTH = Gauge(
    "qommunity_celery_queue_depth",
    "Tasks currently in Celery queue",
    labelnames=["queue_name"],
)

# -- WebSocket ----------------------------------------------------------------

ACTIVE_WS_CONNECTIONS = Gauge(
    "qommunity_active_websocket_connections",
    "Currently active WebSocket connections",
)

WS_MESSAGES_SENT = Counter(
    "qommunity_websocket_messages_sent_total",
    "WebSocket messages sent to clients",
    labelnames=["message_type"],
)

# -- Business -----------------------------------------------------------------

NOTIFICATIONS_DISPATCHED = Counter(
    "qommunity_notifications_dispatched_total",
    "Notifications dispatched by type and channel",
    labelnames=["notification_type", "channel"],   # channel: ws | fcm | email
)

POSTS_CREATED = Counter(
    "qommunity_posts_created_total",
    "Posts created",
    labelnames=["visibility"],
)

FEED_CACHE_HIT_RATE = Counter(
    "qommunity_feed_cache_operations_total",
    "Feed Redis cache operations",
    labelnames=["result"],    # hit | miss | cold
)

MODERATION_ACTIONS = Counter(
    "qommunity_moderation_actions_total",
    "Content moderation decisions",
    labelnames=["action", "severity"],    # action: block|warn|pass  severity: high|medium|low
)

GDPR_EXPORTS = Counter(
    "qommunity_gdpr_exports_total",
    "GDPR data export requests",
    labelnames=["status"],    # requested | completed | failed
)
