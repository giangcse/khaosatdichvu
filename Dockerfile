# syntax=docker/dockerfile:1

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Cài các gói hệ thống tối thiểu cần cho pandas/openpyxl
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libffi-dev \
       curl \
    && rm -rf /var/lib/apt/lists/*

# Cài dependencies trước để tận dụng layer cache
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn
COPY . .

EXPOSE 8000

ENV HOST=0.0.0.0 \
    PORT=8000 \
    THREADS=8 \
    CONN_LIMIT=100 \
    FLASK_CONFIG=ProductionConfig

# Healthcheck vào endpoint /health
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/health || exit 1

CMD ["python", "run_waitress.py"]
