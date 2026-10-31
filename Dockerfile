FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY frontend ./frontend
COPY vendor ./vendor

# Run as an unprivileged user
RUN useradd --create-home appuser && mkdir -p /srv/data && chown appuser:appuser /srv/data
USER appuser

# Cloud Run injects PORT
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --no-proxy-headers"]
