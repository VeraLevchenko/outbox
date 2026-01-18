from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from app.core.config import settings
from app.api import kaiten, files, auth
from app.services.kaiten_service import kaiten_service


# Фоновые задачи для polling
background_tasks = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup: запускаем фоновые задачи
    print("[Startup] Starting background polling tasks...")

    # Создаем задачу для polling колонки "На подпись" (для director)
    task_director = asyncio.create_task(
        kaiten_service.poll_cards("На подпись")
    )
    background_tasks.add(task_director)

    # Создаем задачу для polling колонки начальника отдела
    task_head = asyncio.create_task(
        kaiten_service.poll_cards("Проект готов. Согласование начальника отдела")
    )
    background_tasks.add(task_head)

    print("[Startup] Background tasks started")

    yield

    # Shutdown: останавливаем фоновые задачи
    print("[Shutdown] Stopping background tasks...")
    for task in background_tasks:
        task.cancel()
    await asyncio.gather(*background_tasks, return_exceptions=True)
    print("[Shutdown] All tasks stopped")


app = FastAPI(
    title="Outbox API",
    description="API для работы с исходящей корреспонденцией",
    version="0.1.0",
    debug=settings.DEBUG,
    lifespan=lifespan
)

# CORS middleware для frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене заменить на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(auth.router)
app.include_router(kaiten.router)
app.include_router(files.router)


@app.get("/")
async def root():
    return {
        "message": "Outbox API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
