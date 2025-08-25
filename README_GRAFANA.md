# 🚀 Grafana Dashboard для Courts API

## 📋 Описание

Этот проект включает готовую систему мониторинга с Grafana и Prometheus для отслеживания метрик вашего Courts API.

## 🏗️ Структура проекта

```
Python_Parse/
├── docker-compose.yml              # Конфигурация Docker контейнеров
├── prometheus.yml                  # Конфигурация Prometheus
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── prometheus.yml     # Источник данных Prometheus
│   │   └── dashboards/
│   │       └── dashboard.yml      # Автозагрузка дашбордов
│   └── dashboards/
│       └── courts-api-dashboard.json  # Готовый дашборд
└── python/app/                     # Ваш Python API
```

## 🚀 Быстрый запуск

### 1. **Установите Docker Desktop для Windows**
- Скачайте с [docker.com](https://www.docker.com/products/docker-desktop/)
- Установите и перезагрузите компьютер
- Запустите Docker Desktop

### 2. **Запустите систему мониторинга**
```powershell
# В PowerShell, в папке проекта
docker-compose up -d
```

### 3. **Откройте в браузере**
- **Grafana**: http://localhost:3000
  - Логин: `admin`
  - Пароль: `admin123`
- **Prometheus**: http://localhost:9090

## 📊 Что показывает дашборд

### Основные метрики:
- **Total HTTP Requests** - Общее количество запросов
- **Success Rate (%)** - Процент успешных запросов
- **Average Response Time** - Среднее время ответа
- **Active Tasks** - Активные задачи парсинга

### Графики:
- **Request Duration by Endpoint** - Время ответа по эндпоинтам
- **Requests by Endpoint** - Распределение запросов
- **Status Codes Distribution** - Распределение статус-кодов
- **Court Parsing Success Rate** - Успешность парсинга судов

## 🔧 Настройка

### Изменение портов:
Отредактируйте `docker-compose.yml`:
```yaml
ports:
  - "3001:3000"  # Grafana на порту 3001
  - "9091:9090"  # Prometheus на порту 9091
```

### Изменение пароля Grafana:
```yaml
environment:
  - GF_SECURITY_ADMIN_PASSWORD=ваш_новый_пароль
```

## 🧪 Тестирование

### 1. **Запустите ваш Python API:**
```bash
cd python/app
python main.py
```

### 2. **Отправьте несколько запросов:**
```bash
# POST /api/v1/check_courts
# POST /api/v1/verify_court
```

### 3. **Проверьте метрики:**
- Откройте http://localhost:8000/metrics
- Должны появиться метрики Prometheus

### 4. **Проверьте дашборд:**
- Откройте Grafana
- Дашборд "Courts API Dashboard" должен показать данные

## 🐛 Устранение проблем

### Порт занят:
```powershell
# Проверьте, что порты свободны
netstat -an | findstr :3000
netstat -an | findstr :9090
```

### Docker не запускается:
- Убедитесь, что Docker Desktop запущен
- Проверьте, что WSL2 включен
- Перезапустите Docker Desktop

### Метрики не появляются:
- Проверьте, что ваш API работает на порту 8000
- Убедитесь, что эндпоинт `/metrics` доступен
- Проверьте логи Prometheus

## 📈 Расширение дашборда

### Добавление новых панелей:
1. Откройте Grafana
2. Создайте новую панель
3. Используйте PromQL запросы к вашим метрикам

### Примеры PromQL запросов:
```promql
# Количество запросов за последние 5 минут
rate(http_requests_total[5m])

# 95-й процентиль времени ответа
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Ошибки по типам
sum(errors_total) by (error_type)
```

## 🚀 Команды управления

```powershell
# Запуск
docker-compose up -d

# Остановка
docker-compose down

# Перезапуск
docker-compose restart

# Просмотр логов
docker-compose logs -f grafana
docker-compose logs -f prometheus

# Обновление образов
docker-compose pull
docker-compose up -d
```

## 📚 Полезные ссылки

- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Query Language](https://prometheus.io/docs/prometheus/latest/querying/)
- [Docker Compose](https://docs.docker.com/compose/)

## 🎯 Следующие шаги

1. **Настройте алерты** в Grafana для критических метрик
2. **Добавьте больше метрик** в ваш Python API
3. **Создайте дополнительные дашборды** для разных команд
4. **Настройте retention** для долгосрочного хранения метрик

---

**Удачного мониторинга! 🚀**

