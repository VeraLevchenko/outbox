#!/bin/bash
# Скрипт для запуска backend приложения

cd "$(dirname "$0")"

echo "Starting Outbox API..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
