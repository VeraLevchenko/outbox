from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import kaiten

app = FastAPI(
    title="Outbox API",
    description="API для работы с исходящей корреспонденцией",
    version="0.1.0",
    debug=settings.DEBUG
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
app.include_router(kaiten.router)


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
