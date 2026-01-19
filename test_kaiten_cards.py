#!/usr/bin/env python3
"""
Тестовый скрипт для проверки получения карточек из Kaiten API
"""
import asyncio
import httpx
import json
from dotenv import load_dotenv
import os

# Загрузить переменные окружения из .env
load_dotenv('backend/.env')

# Настройки API
KAITEN_API_URL = os.getenv('KAITEN_API_URL')
KAITEN_API_TOKEN = os.getenv('KAITEN_API_TOKEN')
KAITEN_COLUMN_TO_SIGN_ID = int(os.getenv('KAITEN_COLUMN_TO_SIGN_ID'))
KAITEN_COLUMN_HEAD_REVIEW_ID = int(os.getenv('KAITEN_COLUMN_HEAD_REVIEW_ID'))


async def test_get_cards(column_id: int, column_name: str):
    """Тестовая функция для получения карточек из колонки"""
    headers = {
        "Authorization": f"Bearer {KAITEN_API_TOKEN}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            print(f"\n{'='*60}")
            print(f"Тестирование колонки: {column_name}")
            print(f"Column ID: {column_id}")
            print(f"URL: {KAITEN_API_URL}/cards?column_id={column_id}")
            print(f"{'='*60}\n")

            response = await client.get(
                f"{KAITEN_API_URL}/cards",
                headers=headers,
                params={"column_id": column_id},
                timeout=10.0
            )

            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                cards = response.json()
                print(f"Найдено карточек: {len(cards)}\n")

                for i, card in enumerate(cards, 1):
                    print(f"--- Карточка {i} ---")
                    print(f"ID: {card.get('id')}")
                    print(f"Название: {card.get('title')}")
                    print(f"Колонка: {card.get('column', {}).get('title')}")

                    # Свойства карточки
                    props = card.get('properties', {})
                    incoming_no = props.get('id_228499')
                    incoming_date = props.get('id_228500')
                    print(f"Входящий №: {incoming_no}")
                    print(f"Входящая дата: {incoming_date}")

                    # Файлы
                    files = card.get('files', [])
                    print(f"Файлов: {len(files)}")
                    for file in files:
                        print(f"  - {file.get('name')}")
                    print()

                # Вывести полный JSON первой карточки для отладки
                if cards:
                    print("\n--- Полный JSON первой карточки ---")
                    print(json.dumps(cards[0], indent=2, ensure_ascii=False))
            else:
                print(f"Ошибка: {response.status_code}")
                print(f"Ответ: {response.text}")

        except Exception as e:
            print(f"Исключение: {e}")


async def main():
    """Основная функция"""
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ KAITEN API")
    print("="*60)

    print(f"\nAPI URL: {KAITEN_API_URL}")
    print(f"API Token: {KAITEN_API_TOKEN[:20]}...")

    # Тест 1: Колонка "На подпись" (для director)
    await test_get_cards(KAITEN_COLUMN_TO_SIGN_ID, "На подпись")

    # Тест 2: Колонка "Проект готов. Согласование начальника отдела" (для head)
    await test_get_cards(KAITEN_COLUMN_HEAD_REVIEW_ID, "Проект готов. Согласование начальника отдела")


if __name__ == "__main__":
    asyncio.run(main())
