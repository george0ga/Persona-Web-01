FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    ca-certificates \
    fonts-liberation \
    libnss3 \
    libatk-bridge2.0-0 \
    libxkbcommon0 \
    libgbm1 \
    libgtk-3-0 \
    curl \
  && rm -rf /var/lib/apt/lists/*

ENV CHROMIUM_BIN=/usr/bin/chromium \
    CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER=/usr/bin/chromedriver

WORKDIR /app

COPY python/app/requirements.txt /app/python/app/requirements.txt

RUN pip install --no-cache-dir -r /app/python/app/requirements.txt

COPY . /app

WORKDIR /app/python

CMD ["python", "-m", "app.main"]
