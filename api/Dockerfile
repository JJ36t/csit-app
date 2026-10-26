# -*- coding: utf-8 -*-
# صورة خدمة FastAPI — سياق البناء هو مجلد api/.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# curl لفحص الصحة فقط؛ psycopg[binary] وbcrypt يأتيان كـwheels جاهزة فلا مترجم
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# مستخدم غير جذر + مجلد رفع قابل للكتابة (يُثبَّت كـvolume في compose)
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/uploads \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# /health عميق: يفشل (503) عند تعطّل قاعدة البيانات، فيظهر الحاوٍ unhealthy
HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=3 \
    CMD curl --fail --silent --show-error --max-time 5 http://127.0.0.1:8000/health || exit 1

# عامل واحد عمداً: عدّاد حدّ المعدل في الذاكرة لا يُشارَك بين العمليات
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
