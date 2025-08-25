from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

router = APIRouter(tags=["dashboard"])

# Путь к HTML файлу дашборда
DASHBOARD_PATH = os.path.join(os.path.dirname(__file__), "..", "ui_web", "metrics_dashboard.html")

@router.get("/dashboard", response_class=HTMLResponse)
async def get_metrics_dashboard():
    """
    Возвращает HTML страницу с дашбордом метрик
    """
    try:
        with open(DASHBOARD_PATH, 'r', encoding='utf-8') as file:
            html_content = file.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Ошибка</h1><p>Файл дашборда не найден</p>",
            status_code=404
        )
    except Exception as e:
        return HTMLResponse(
            content=f"<h1>Ошибка</h1><p>Не удалось загрузить дашборд: {e}</p>",
            status_code=500
        )

@router.get("/dashboard/health")
async def dashboard_health():
    """
    Проверка доступности файла дашборда
    """
    try:
        if os.path.exists(DASHBOARD_PATH):
            return {"status": "ok", "message": "Dashboard file exists"}
        else:
            return {"status": "error", "message": "Dashboard file not found"}
    except Exception as e:
        return {"status": "error", "message": f"Error checking dashboard: {e}"}
