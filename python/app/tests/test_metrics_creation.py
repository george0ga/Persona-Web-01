#!/usr/bin/env python3
"""
Тест создания метрик
"""
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "python", "app")))

from metrics import (
    HTTP_REQUESTS_TOTAL, 
    HTTP_REQUEST_DURATION,
    initialize_metrics,
    track_http_metrics
)
from fastapi import Request
from unittest.mock import Mock
import asyncio

print("🔍 Тестируем создание метрик...")

async def test_metrics():
    """Тестируем создание метрик"""
    try:
        # 1. Инициализируем метрики
        print("🚀 Инициализируем метрики...")
        initialize_metrics()
        print("✅ Метрики инициализированы")
        
        # 2. Создаем мок Request
        mock_request = Mock()
        mock_request.method = "POST"
        mock_request.url.path = "/api/v1/check_courts"
        mock_request.client.host = "127.0.0.1"
        
        # 3. Тестируем декоратор
        @track_http_metrics()
        async def test_function(request: Request):
            print("📝 Выполняется тестовая функция...")
            await asyncio.sleep(0.1)
            return {"status": "success"}
        
        print("🚀 Вызываем функцию с декоратором...")
        result = await test_function(mock_request)
        print(f"✅ Результат: {result}")
        
        # 4. Проверяем, что метрики созданы
        print("📊 Проверяем создание метрик...")
        print(f"HTTP_REQUESTS_TOTAL: {HTTP_REQUESTS_TOTAL}")
        print(f"HTTP_REQUEST_DURATION: {HTTP_REQUEST_DURATION}")
        
        # 5. Проверяем экспорт
        from prometheus_client import generate_latest
        metrics_text = generate_latest().decode('utf-8')
        
        print("📋 Экспортированные метрики:")
        print("=" * 50)
        print(metrics_text)
        print("=" * 50)
        
        # 6. Проверяем наличие наших метрик
        if "http_requests_total" in metrics_text:
            print("✅ http_requests_total найден в экспорте!")
        else:
            print("❌ http_requests_total НЕ найден в экспорте!")
            
        if "http_request_duration_seconds" in metrics_text:
            print("✅ http_request_duration_seconds найден в экспорте!")
        else:
            print("❌ http_request_duration_seconds НЕ найден в экспорте!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_metrics())


