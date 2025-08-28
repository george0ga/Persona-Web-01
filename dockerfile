# Используем slim (Debian bookworm). Небольшой, но с нормальными репами для Chromium.
FROM python:3.11-slim

# Неинтерактивный apt и предсказуемые локации
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Обновление и установка системных пакетов + Chromium и ChromeDriver для Selenium
# Пакеты шрифтов/сертификатов — чтобы страницы рендерились корректно
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

# Опционально: переменные окружения для явных путей к бинарям
ENV CHROMIUM_BIN=/usr/bin/chromium \
    CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER=/usr/bin/chromedriver

# Создаём рабочую директорию проекта
WORKDIR /app

# Копируем только requirements сначала — для кеша слоёв
# У тебя requirements лежит в python/app/requirements.txt
COPY python/app/requirements.txt /app/python/app/requirements.txt

# Установка Python-зависимостей (включая FastAPI, Celery, Selenium и т.д.)
RUN pip install --no-cache-dir -r /app/python/app/requirements.txt

# Копируем весь проект (модели .pt тоже попадут в образ)
COPY . /app

# ВАЖНО: для твоих команд мы будем работать из /app/python
WORKDIR /app/python

# По умолчанию контейнер будет запускать сервер
# (команду для воркера зададим в docker-compose)
CMD ["python", "-m", "app.main"]
