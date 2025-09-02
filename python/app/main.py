import os
os.environ.setdefault("ATEN_CPU_CAPABILITY", "default")
os.environ.setdefault("ATEN_NO_MKL", "1")
os.environ.setdefault("ATEN_NO_MKLDNN", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")


import uvicorn
from fastapi import FastAPI

from contextlib import asynccontextmanager
from app.utils.logger import logger

from app.services.check_service import CheckService
from app.metrics.metrics import start_metrics

from app.config.settings import settings

from app.middleware.cors import setup_cors
from app.middleware.rate_limit import setup_rate_limit_middleware

from app.handlers.errors import setup_error_handlers

from app.routes.health import router as health_router
from app.routes.courts import router as courts_router
from app.routes.sse import router as sse_router
from app.routes.metrics import router as metrics_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.check_service = CheckService()
    await start_metrics()
    yield

app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    lifespan=lifespan
)

setup_cors(app)
setup_error_handlers(app)
setup_rate_limit_middleware(app)

# Подключение роутов
app.include_router(courts_router)
app.include_router(sse_router)
app.include_router(health_router)
app.include_router(metrics_router)

if __name__ == "__main__":
    logger.info(f" Запуск FastAPI на http://{settings.HOST}:{settings.PORT}")
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)