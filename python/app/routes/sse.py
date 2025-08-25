# routes/sse.py
import asyncio
import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.celery.celery_app import celery_app
from celery.result import GroupResult, AsyncResult

router = APIRouter(prefix="/api/v1",tags=["sse"])

@router.get("/courts/verify/stream/{task_id}")
async def stream_verify_courts_result(task_id: str, request: Request):
    async def event_generator():
        result = AsyncResult(task_id, app=celery_app)
        if not result or not result.id:
            yield f"data: {{\"error\": \"Задача не найдена\"}}\n\n"
            return
        while not result.ready():
            if await request.is_disconnected():
                break
            await asyncio.sleep(1)
            yield f"data: {{\"status\": \"pending\"}}\n\n"
        if result.ready():
            data = result.get()
            import json
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/courts/check/stream/{task_id}")
async def stream_check_courts_result(task_id: str, request: Request):
    async def event_generator():
        group_result = GroupResult.restore(task_id, app=celery_app)
        if not group_result:
            yield f"data: {{\"error\": \"Задача не найдена\"}}\n\n"
            return
        last_statuses = {}
        while not group_result.ready():
            if await request.is_disconnected():
                break
            statuses = []
            for subtask in group_result.results:
                meta = subtask.info if isinstance(subtask.info, dict) else {}
                status_text = meta.get("status", subtask.state)
                court_name = meta.get("court_name", None)
                # Отправляем только если статус изменился
                if last_statuses.get(subtask.id) != status_text:
                    statuses.append({
                        "task_id": subtask.id,
                        "court_name": court_name,
                        "state": subtask.state,
                        "status": status_text
                    })
                    last_statuses[subtask.id] = status_text
            if statuses:
                yield f"data: {json.dumps({'status': 'progress', 'subtasks': statuses}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(1)
        # Финальный результат
        results = group_result.get()
        yield f"data: {json.dumps({'status': 'success', 'result': results}, ensure_ascii=False)}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")