#!/usr/bin/env python3
"""
Скрипт для отладки получения карточек из Kaiten

Показывает все карточки в колонке "На подпись" независимо от lane_id
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.services.kaiten_service import KaitenService
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    print("=" * 80)
    print("ОТЛАДКА КАРТОЧЕК В КОЛОНКЕ 'НА ПОДПИСЬ'")
    print("=" * 80)
    print()

    # Создаем сервис с реальным API
    service = KaitenService(use_mock=False)

    print(f"Column ID 'На подпись': {settings.KAITEN_COLUMN_TO_SIGN_ID}")
    print(f"Lane ID для фильтрации: {settings.KAITEN_LANE_ID}")
    print()

    # Получаем ВСЕ карточки без фильтра по lane
    import httpx
    async with httpx.AsyncClient() as client:
        # Запрос 1: Только по board_id
        print("1. Запрос ВСЕХ карточек с board_id (без фильтра lane_id):")
        print("-" * 80)

        response = await client.get(
            f"{settings.KAITEN_API_URL}/cards",
            headers={
                "Authorization": f"Bearer {settings.KAITEN_API_TOKEN}",
                "Content-Type": "application/json"
            },
            params={"board_id": settings.KAITEN_BOARD_ID},
            timeout=30.0
        )

        if response.status_code == 200:
            all_cards = response.json()
            print(f"   ✓ Получено {len(all_cards)} карточек всего")

            # Фильтруем по column_id "На подпись"
            cards_in_column = [c for c in all_cards if c.get("column_id") == settings.KAITEN_COLUMN_TO_SIGN_ID]

            print(f"   ✓ Карточек в колонке 'На подпись' (column_id={settings.KAITEN_COLUMN_TO_SIGN_ID}): {len(cards_in_column)}")
            print()

            if cards_in_column:
                print("   Детали карточек в колонке 'На подпись':")
                print("   " + "-" * 76)

                lane_distribution = {}

                for idx, card in enumerate(cards_in_column, 1):
                    card_id = card.get("id")
                    title = card.get("title", "Без названия")
                    lane_id = card.get("lane_id")
                    column_id = card.get("column_id")

                    # Извлекаем properties
                    incoming_no = service.get_incoming_no(card)
                    incoming_date = service.get_incoming_date(card)

                    print(f"   {idx}. ID: {card_id}")
                    print(f"      Название: {title}")
                    print(f"      Lane ID: {lane_id} {'✓ (нужный)' if lane_id == settings.KAITEN_LANE_ID else '✗ (другой lane!)'}")
                    print(f"      Column ID: {column_id}")
                    print(f"      Incoming No: {incoming_no}")
                    print(f"      Incoming Date: {incoming_date}")

                    # Файлы
                    files = card.get("files", [])
                    print(f"      Файлов: {len(files)}")
                    if files:
                        for f in files:
                            fname = f.get("name", "без имени")
                            print(f"        - {fname}")

                    print()

                    # Статистика по lane_id
                    lane_distribution[lane_id] = lane_distribution.get(lane_id, 0) + 1

                print("   " + "-" * 76)
                print("   Распределение по Lane ID:")
                for lane_id, count in sorted(lane_distribution.items()):
                    marker = "✓ (используется в фильтре)" if lane_id == settings.KAITEN_LANE_ID else ""
                    print(f"     Lane ID {lane_id}: {count} карточек {marker}")

                print()

        else:
            print(f"   ✗ Ошибка: {response.status_code}")
            print(f"   {response.text}")

        print()
        print("=" * 80)

        # Запрос 2: С фильтром по lane_id (как в текущем коде)
        print("2. Запрос с фильтром по board_id И lane_id (текущая логика):")
        print("-" * 80)

        response2 = await client.get(
            f"{settings.KAITEN_API_URL}/cards",
            headers={
                "Authorization": f"Bearer {settings.KAITEN_API_TOKEN}",
                "Content-Type": "application/json"
            },
            params={
                "board_id": settings.KAITEN_BOARD_ID,
                "lane_id": settings.KAITEN_LANE_ID
            },
            timeout=30.0
        )

        if response2.status_code == 200:
            filtered_cards = response2.json()
            print(f"   ✓ Получено {len(filtered_cards)} карточек с фильтром lane_id={settings.KAITEN_LANE_ID}")

            cards_in_column_filtered = [c for c in filtered_cards if c.get("column_id") == settings.KAITEN_COLUMN_TO_SIGN_ID]
            print(f"   ✓ Из них в колонке 'На подпись': {len(cards_in_column_filtered)}")

        print()
        print("=" * 80)
        print("ВЫВОДЫ:")
        print("-" * 80)
        print()

        if len(cards_in_column) > len(cards_in_column_filtered):
            print(f"⚠ ПРОБЛЕМА НАЙДЕНА!")
            print(f"  Всего карточек в колонке: {len(cards_in_column)}")
            print(f"  Получено с фильтром lane_id: {len(cards_in_column_filtered)}")
            print(f"  Не хватает: {len(cards_in_column) - len(cards_in_column_filtered)} карточек")
            print()
            print(f"РЕШЕНИЕ:")
            print(f"  Карточки находятся в разных Lane (дорожках).")
            print(f"  Нужно либо:")
            print(f"    1. Убрать фильтр по lane_id (получать все карточки доски)")
            print(f"    2. Фильтровать по нескольким lane_id")
            print(f"    3. Проверить правильность KAITEN_LANE_ID в .env")
        else:
            print(f"✓ Все карточки получены корректно")
            print(f"  Карточек в колонке: {len(cards_in_column)}")

        print()
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
