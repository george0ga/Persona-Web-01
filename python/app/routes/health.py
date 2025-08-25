# routes/health.py
import time
import ipaddress
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from app.utils.logger import logger
from app.config.settings import settings
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/v1",tags=["health"])

def is_health_check_allowed(client_ip: str) -> bool:
    """Проверяет доступ к health check"""
    try:
        client_ip_obj = ipaddress.ip_address(client_ip)
        for allowed in settings.ALLOWED_HEALTH_IPS:
            if client_ip_obj in ipaddress.ip_network(allowed.strip()):
                return True
        return False
    except ValueError:
        return False

def check_health_access(request: Request):
    """Проверка доступа к health check эндпоинтам"""
    client_ip = request.client.host
    
    if not is_health_check_allowed(client_ip):
        logger.warning(f"Попытка несанкционированного доступа к health check с IP: {client_ip}")
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    logger.info(f"Health check запрос с разрешенного IP: {client_ip}")

@router.get("/health")
@limiter.limit(settings.RATE_LIMIT_HEALTH)
async def health_check(request: Request):
    check_health_access(request)
    try:
        # Получаем app из request
        check_manager_ok = request.app.state.check_manager is not None
        status_manager_ok = request.app.state.status_manager is not None
        
        health_status = {
            "status": "healthy" if check_manager_ok and status_manager_ok else "degraded",
            "timestamp": time.time(),
            "version": settings.API_VERSION,
            "components": {
                "check_manager": "ok" if check_manager_ok else "error",
                "status_manager": "ok" if status_manager_ok else "error"
            }
        }
        
        if health_status["status"] == "healthy":
            return health_status
        else:
            return JSONResponse(status_code=503, content=health_status)
            
    except Exception as e:
        logger.exception(f"Ошибка при проверке здоровья сервера: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": time.time(),
                "error": str(e)
            }
        )

@router.get("/health/ready")
@limiter.limit(settings.RATE_LIMIT_HEALTH)
async def readiness_check(request: Request):
    check_health_access(request)
    return {"status": "ready", "timestamp": time.time()}

@router.get("/health/live")
@limiter.limit(settings.RATE_LIMIT_HEALTH)
async def liveness_check(request: Request):
    check_health_access(request)
    return {"status": "alive", "timestamp": time.time()}