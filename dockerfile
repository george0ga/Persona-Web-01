# Dockerfile (или твой 'dockerfile'), базовый образ на Debian 12 (stable)
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 DEBIAN_FRONTEND=noninteractive

# HTTPS-репы + ретраи, ставим chromium и chromedriver из apt
RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list /etc/apt/sources.list.d/debian.sources || true \
 && apt-get update -o Acquire::Retries=5 \
 && apt-get install -y --no-install-recommends \
      chromium chromium-driver ca-certificates fonts-liberation libnss3 libatk-bridge2.0-0 \
      libxkbcommon0 libgbm1 libgtk-3-0 libasound2 curl \
 && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver \
    CHROMIUM_FLAGS="--no-sandbox --disable-dev-shm-usage --disable-gpu --headless=new"

WORKDIR /app
COPY python/app /app/app
RUN pip install --upgrade pip && pip install -r /app/app/requirements.txt

EXPOSE 8000
CMD ["python", "-m", "app.main"]