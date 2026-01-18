#!/usr/bin/env python3
"""
Скрипт для тестирования подключения к Kaiten API

Использование:
    python test_kaiten_connection.py
"""

import asyncio
import sys
import os

# Добавляем путь к модулям приложения
sys.path.insert(0, os.path.dirname(__file__))

from app.services.kaiten_service import KaitenService
from app.core.config import settings
import logging

# Настройка подробного логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_connection():
    """Тестирование подключения к Kaiten API"""

    print("\n" + "="*70)
    print("ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ К KAITEN API")
    print("="*70 + "\n")

    # Проверка настроек
    print("1. Проверка настроек:")
    print(f"   API URL: {settings.KAITEN_API_URL}")
    print(f"   API Token: {'*' * 20}{settings.KAITEN_API_TOKEN[-4:] if len(settings.KAITEN_API_TOKEN) > 4 else '****'}")
    print(f"   Debug Mode: {settings.DEBUG}")
    print(f"   Use Mock: {settings.KAITEN_USE_MOCK}")
    print()

    # Создаем сервис с принудительным использованием реального API
    service = KaitenService(use_mock=False)

    # Тест 1: Получение списка досок
    print("2. Получение списка досок...")
    try:
        boards = await service.get_boards()

        if boards:
            print(f"   ✓ Успешно! Найдено досок: {len(boards)}")
            for idx, board in enumerate(boards[:5], 1):  # Показываем первые 5
                print(f"     {idx}. ID: {board.get('id')}, Название: {board.get('title') or board.get('name')}")
            if len(boards) > 5:
                print(f"     ... и еще {len(boards) - 5} досок")
        else:
            print("   ✗ Ошибка: Доски не найдены")
            print("   Проверьте:")
            print("     - Правильность API URL")
            print("     - Валидность токена")
            print("     - Доступность Kaiten API")
            return False

    except Exception as e:
        print(f"   ✗ Ошибка при получении досок: {e}")
        return False

    print()

    # Тест 2: Получение колонок для каждой доски
    if boards:
        board = boards[0]
        board_id = board.get('id')
        board_name = board.get('title') or board.get('name')

        print(f"3. Получение колонок для доски '{board_name}' (ID: {board_id})...")
        try:
            columns = await service.get_board_columns(board_id)

            if columns:
                print(f"   ✓ Успешно! Найдено колонок: {len(columns)}")
                for idx, col in enumerate(columns, 1):
                    col_id = col.get('id')
                    col_name = col.get('name') or col.get('title')
                    print(f"     {idx}. ID: {col_id}, Название: {col_name}")
            else:
                print("   ⚠ Колонки не найдены (возможно доска пустая)")

        except Exception as e:
            print(f"   ✗ Ошибка при получении колонок: {e}")

        print()

    # Тест 3: Получение карточек
    print("4. Получение всех карточек...")
    try:
        # Временно изменим метод, чтобы получить ВСЕ карточки без фильтрации
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.KAITEN_API_URL}/cards",
                headers={
                    "Authorization": f"Bearer {settings.KAITEN_API_TOKEN}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )

            if response.status_code == 200:
                all_cards = response.json()
                print(f"   ✓ Успешно! Найдено карточек: {len(all_cards)}")

                # Анализируем структуру карточек
                if all_cards:
                    print("\n   Анализ структуры первой карточки:")
                    first_card = all_cards[0]

                    print(f"     ID: {first_card.get('id')}")
                    print(f"     Title: {first_card.get('title')}")
                    print(f"     Board ID: {first_card.get('board_id')}")

                    # Проверяем разные варианты поля колонки
                    column_info = []
                    if 'column_id' in first_card:
                        column_info.append(f"column_id={first_card['column_id']}")
                    if 'column_name' in first_card:
                        column_info.append(f"column_name={first_card['column_name']}")
                    if 'column' in first_card and isinstance(first_card['column'], dict):
                        column_info.append(f"column={{id={first_card['column'].get('id')}, name={first_card['column'].get('name')}}}")

                    print(f"     Column: {', '.join(column_info) if column_info else 'НЕ НАЙДЕНО'}")

                    # Проверяем properties (custom fields)
                    if 'properties' in first_card:
                        print(f"     Properties: {first_card['properties']}")
                    elif 'custom_fields' in first_card:
                        print(f"     Custom Fields: {first_card['custom_fields']}")

                    # Файлы
                    if 'files' in first_card:
                        print(f"     Files: {len(first_card.get('files', []))} файлов")

                    # Показываем все ключи для полного понимания структуры
                    print(f"\n     Все ключи в карточке: {list(first_card.keys())}")

                    # Группируем карточки по колонкам
                    print("\n   Распределение карточек по колонкам:")
                    column_stats = {}
                    for card in all_cards:
                        col_name = card.get('column_name') or (card.get('column', {}).get('name') if isinstance(card.get('column'), dict) else None) or 'Unknown'
                        column_stats[col_name] = column_stats.get(col_name, 0) + 1

                    for col_name, count in sorted(column_stats.items()):
                        print(f"     - {col_name}: {count} карточек")

            elif response.status_code == 401:
                print("   ✗ Ошибка авторизации (401)")
                print("   Проверьте правильность API токена")
            elif response.status_code == 403:
                print("   ✗ Доступ запрещен (403)")
                print("   Проверьте права доступа токена")
            else:
                print(f"   ✗ Ошибка {response.status_code}: {response.text}")

    except Exception as e:
        print(f"   ✗ Ошибка при получении карточек: {e}")

    print("\n" + "="*70)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("="*70 + "\n")

    return True


if __name__ == "__main__":
    # Проверяем наличие .env файла
    if not os.path.exists(".env"):
        print("⚠ ВНИМАНИЕ: .env файл не найден!")
        print("Создайте .env файл на основе .env.example и заполните:")
        print("  - KAITEN_API_URL")
        print("  - KAITEN_API_TOKEN")
        sys.exit(1)

    # Запускаем тесты
    asyncio.run(test_connection())
