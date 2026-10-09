
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    BACKEND_URL=http://127.0.0.1:8000 \
    REDIS_URL=redis://127.0.0.1:6379/0

RUN apt-get update \
    && apt-get install -y --no-install-recommends redis-server \
    && rm -rf /var/lib/apt/lists/*


RUN useradd --create-home --uid 1000 appuser
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY --chown=appuser:appuser backend ./backend
COPY --chown=appuser:appuser frontend ./frontend

USER appuser

EXPOSE 10000

CMD ["bash", "-c", "redis-server --bind 127.0.0.1 --port 6379 --save '' --appendonly no --maxmemory 64mb --maxmemory-policy allkeys-lru & uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 & streamlit run frontend/app.py --server.address=0.0.0.0 --server.port=${PORT:-10000} --server.headless=true --browser.gatherUsageStats=false & wait -n; exit $?"]
