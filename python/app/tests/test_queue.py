import time
import requests
import pytest

API_URL = "http://localhost:8000/api/v1/courts/batch-verify"  # Измени на свой endpoint, если нужно

def test_celery_task_result():
    # Отправляем задачу
    response = requests.post(API_URL, json={
        "address": ["https://k-h2.ros.msudrf.ru"],
        "fullname": {"surname": "TestFio", "name": "Test", "patronymic": ""}
    })
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    task_id = data["task_id"]

    # Ожидаем и опрашиваем результат (пример: /api/v1/task-result/{task_id})
    for _ in range(20):
        result_resp = requests.get(f"http://localhost:8000/api/v1/task-result/{task_id}")
        if result_resp.status_code == 200:
            result_data = result_resp.json()
            assert result_data.get("status") == "success"
            break
        time.sleep(1)
    else:
        pytest.fail("Task did not complete in time")