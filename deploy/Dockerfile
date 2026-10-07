# Auto Expert backend (FastAPI) for the server; built on the server from the release directory:
#   docker compose --env-file /srv/autoexpert/shared/.env -f deploy/compose.yaml build backend
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/backend

WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 autoexpert \
    && useradd --uid 10001 --gid autoexpert --home /app autoexpert

# dependencies pinned with hashes (exported from uv.lock: uv export --no-dev --no-emit-project --frozen)
COPY deploy/requirements.lock ./requirements.lock
RUN pip install --require-hashes -r requirements.lock

COPY backend/app ./backend/app
COPY backend/alembic ./backend/alembic
COPY backend/alembic.ini ./backend/alembic.ini
COPY data/manifests ./data/manifests
COPY scripts/garage_recall_job.py scripts/manage_users.py scripts/knowledge_admin.py ./scripts/

RUN mkdir -p /data/media && chown autoexpert:autoexpert /data/media
USER autoexpert
EXPOSE 8000
# no access log: URLs may contain vehicle identifiers
CMD ["uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--no-access-log", "--proxy-headers", "--forwarded-allow-ips", "*"]
