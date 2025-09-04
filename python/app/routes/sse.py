import asyncio
import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.celery.celery_app import celery_app
from celery.result import GroupResult, AsyncResult
from app.metrics.redis_client import (get_court_check_size,
                                      get_court_verify_size, get_queue_size_redis,
                                      get_court_last_check_time)

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
        results = group_result.get()
        yield f"data: {json.dumps({'status': 'success', 'result': results}, ensure_ascii=False)}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/metrics/queue_size/stream")
async def stream_queue_size(request: Request):
    """
    SSE-эндпоинт для стриминга размера очередей задач.
    """
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            result = {}
            result["redis_courts"] = get_queue_size_redis("court_checks") or 0
            result["redis_verify"] = get_queue_size_redis("court_verifications") or 0
            result["court"] = get_court_check_size() or 0
            result["verify"] = get_court_verify_size() or 0
            result["celery_court_last_check_time_blue"] = float(get_court_last_check_time("blue") or 0.0)
            result["celery_court_last_check_time_yellow"] = float(get_court_last_check_time("yellow") or 0.0)
            result["celery_court_last_check_time_spb"] = float(get_court_last_check_time("spb") or 0.0)
            data = {
                "redis_check_courts_queue_size": result["redis_courts"],
                "redis_verify_courts_queue_size": result["redis_verify"],
                "celery_check_courts_queue_size": result["court"],
                "celery_verify_courts_queue_size": result["verify"],
                "celery_court_last_check_time_blue": result["celery_court_last_check_time_blue"],
                "celery_court_last_check_time_yellow": result["celery_court_last_check_time_yellow"],
                "celery_court_last_check_time_spb": result["celery_court_last_check_time_spb"]
            }
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            await asyncio.sleep(15)  # интервал обновления в секундах

    return StreamingResponse(event_generator(), media_type="text/event-stream")