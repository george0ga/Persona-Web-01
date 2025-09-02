FROM python:3.9-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list /etc/apt/sources.list.d/debian.sources || true \
 && apt-get update -o Acquire::Retries=5 \
 && apt-get install -y --no-install-recommends \
      chromium \
      chromium-driver \
      ca-certificates \
      curl \
      libnss3 \
      libatk-bridge2.0-0 \
      libxkbcommon0 \
      libgbm1 \
      libgtk-3-0 \
      libasound2 \
      libdrm2 \
      libxcomposite1 \
      libxrandr2 \
      libxi6 \
      libxdamage1 \
      libxshmfence1 \
      fonts-dejavu \
      fonts-noto \
      fonts-noto-cjk \
      fonts-noto-color-emoji \
 && ln -sf /usr/bin/chromium /usr/bin/google-chrome \
 && ln -sf /usr/bin/chromedriver /usr/local/bin/chromedriver \
 && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER=/usr/bin/chromedriver \
    CHROMIUM_FLAGS="--no-sandbox --disable-dev-shm-usage --disable-gpu --headless=new --window-size=1920,1080"

WORKDIR /app

COPY python/app/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r /tmp/requirements.txt \
      -f https://download.pytorch.org/whl/lts/1.8/torch_lts.html

COPY python/app /app/app

RUN useradd -ms /bin/bash appuser \
 && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["python", "-m", "app.main"]
