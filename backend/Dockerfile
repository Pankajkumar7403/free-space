# -- Stage 1: Dependency builder ----------------------------------------------
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-cache


# -- Stage 2: Runtime ---------------------------------------------------------
FROM python:3.12-slim AS runtime

# Runtime system deps only
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy virtualenv from builder (avoids re-installing)
COPY --from=builder /app/.venv /app/.venv

WORKDIR /app

# Copy application source
COPY . .

# Create non-root user for security
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --no-create-home appuser && \
    mkdir -p /app/staticfiles /app/mediafiles && \
    chown -R appuser:appgroup /app

USER appuser

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings.production

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/ || exit 1

CMD ["gunicorn", "config.wsgi:application", \
     "--workers", "4", \
     "--worker-class", "gthread", \
     "--threads", "2", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "30", \
     "--keepalive", "5", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--log-level", "info", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
