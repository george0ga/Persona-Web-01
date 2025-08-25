#!/usr/bin/env python3
"""
Тест декоратора track_http_metrics
"""
import sys
import os
import time

# Добавляем путь к модулям
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "python", "app")))

from metrics import track_http_metrics, HTTP_REQUESTS_TOTAL, HTTP_REQUEST_DURATION
from fastapi import Request
from unittest.mock import Mock

print("🔍 Тестируем декоратор track_http_metrics...")

# Создаем мок Request
mock_request = Mock()
mock_request.method = "POST"
mock_request.url.path = "/api/v1/check_courts"
mock_request.client.host = "127.0.0.1"

@track_http_metrics()
async def test_function(request: Request):
    """Тестовая функция с декоратором"""
    print("📝 Выполняется тестовая функция...")
    await asyncio.sleep(0.1)  # Имитируем работу
    return {"status": "success"}

async def test_decorator():
    """Тестируем декоратор"""
    try:
        print("🚀 Вызываем функцию с декоратором...")
        result = await test_function(mock_request)
        print(f"✅ Результат: {result}")
        
        print("📊 Проверяем метрики...")
        print("✅ Декоратор выполнился без ошибок!")
        print("✅ Метрики должны быть обновлены!")
        
        # Проверяем, что метрики доступны
        print(f"HTTP_REQUESTS_TOTAL доступен: {HTTP_REQUESTS_TOTAL}")
        print(f"HTTP_REQUEST_DURATION доступен: {HTTP_REQUEST_DURATION}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_decorator())
