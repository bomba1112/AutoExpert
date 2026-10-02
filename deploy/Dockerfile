FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/backend
WORKDIR /app
RUN groupadd --gid 10001 autoexpert && useradd --uid 10001 --gid autoexpert --create-home autoexpert
COPY pyproject.toml README.md ./
COPY deploy/requirements.lock ./requirements.lock
COPY backend ./backend
COPY apps/web_preview ./apps/web_preview
COPY scripts/knowledge_admin.py ./scripts/knowledge_admin.py
COPY data/manifests ./data/manifests
RUN pip install --no-cache-dir --require-hashes -r requirements.lock && pip install --no-cache-dir --no-deps . && mkdir /data && chown autoexpert:autoexpert /data
USER autoexpert
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
