"""
core.middleware
~~~~~~~~~~~~~~~
Django middleware stack for Qommunity.

Order matters — add to settings.MIDDLEWARE in this sequence:

    "core.middleware.exception_handler.ExceptionHandlerMiddleware",
    "core.middleware.request_logging.RequestLoggingMiddleware",
    "core.middleware.metrics.MetricsMiddleware",
"""