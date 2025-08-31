"""
Скрипт для тестирования API и генерации метрик
"""
import requests
import time
import json

API_BASE = "http://localhost:8000"

def test_api():
    """Тестируем API эндпоинты"""
    
    print("Тестируем /api/v1/check_courts...")
    try:
        response = requests.post(
            f"{API_BASE}/api/v1/check_courts",
            json={
                "address": "http://test.ru",
                "fullname": {
                    "surname": "Иванов",
                    "name": "Иван"
                }
            },
            timeout=10
        )
        print(f"Статус: {response.status_code}")
        if response.status_code == 200:
            print("Ответ получен")
        else:
            print(f"Ошибка: {response.text}")
    except Exception as e:
        print(f"Ошибка запроса: {e}")
    
    time.sleep(1)
    
    print("\n Тестируем /api/v1/verify_court...")
    try:
        response = requests.post(
            f"{API_BASE}/api/v1/verify_court",
            json={
                "address": "http://test.ru"
            },
            timeout=10
        )
        print(f"Статус: {response.status_code}")
        if response.status_code == 200:
            print("Ответ получен")
        else:
            print(f"Ошибка: {response.text}")
    except Exception as e:
        print(f"Ошибка запроса: {e}")
    
    time.sleep(1)
    
    print("\n Тестируем /health...")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        print(f"Статус: {response.status_code}")
        if response.status_code == 200:
            print("Ответ получен")
        else:
            print(f"Ошибка: {response.text}")
    except Exception as e:
        print(f"Ошибка запроса: {e}")

if __name__ == "__main__":
    print("Запуск тестирования API...")
    print(f"API URL: {API_BASE}")
    print("=" * 50)
    
    test_api()
    
    print("\n" + "=" * 50)
    print("Тестирование завершено!")
    print("Теперь проверьте метрики в Prometheus и Grafana")
    print("Prometheus: http://localhost:9090")
    print("Grafana: http://localhost:3000")

