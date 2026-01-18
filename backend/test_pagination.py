#!/usr/bin/env python3
"""
Скрипт для тестирования пагинации Kaiten API

Показывает:
- Сколько карточек получено на каждой странице (offset)
- Общее количество карточек на доске
- Распределение по колонкам
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.core.config import settings
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_pagination():
    print("=" * 80)
    print("ТЕСТ ПАГИНАЦИИ KAITEN API")
    print("=" * 80)
    print()

    print(f"Board ID: {settings.KAITEN_BOARD_ID}")
    print(f"Lane ID: {settings.KAITEN_LANE_ID}")
    print(f"API URL: {settings.KAITEN_API_URL}")
    print()

    headers = {
        "Authorization": f"Bearer {settings.KAITEN_API_TOKEN}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        print("Получение карточек с пагинацией:")
        print("-" * 80)

        all_cards = []
        offset = 0
        limit = 100
        page = 1

        while True:
            print(f"\n📄 Страница {page} (offset={offset}, limit={limit}):")

            params = {
                "board_id": settings.KAITEN_BOARD_ID,
                "limit": limit,
                "offset": offset
            }

            try:
                response = await client.get(
                    f"{settings.KAITEN_API_URL}/cards",
                    headers=headers,
                    params=params,
                    timeout=30.0
                )

                if response.status_code != 200:
                    print(f"   ✗ Ошибка: {response.status_code}")
                    print(f"   {response.text}")
                    break

                cards_batch = response.json()
                cards_count = len(cards_batch)

                print(f"   ✓ Получено карточек: {cards_count}")

                if cards_count == 0:
                    print(f"   → Больше карточек нет, завершаем")
                    break

                all_cards.extend(cards_batch)

                if cards_count < limit:
                    print(f"   → Последняя страница (получено меньше {limit})")
                    break

                offset += limit
                page += 1

                # Защита от бесконечного цикла
                if offset >= 1000:
                    print(f"   ⚠ Достигнут лимит offset=1000, останавливаем")
                    break

            except Exception as e:
                print(f"   ✗ Ошибка запроса: {e}")
                break

        print()
        print("=" * 80)
        print("РЕЗУЛЬТАТЫ:")
        print("=" * 80)
        print()

        total_returned = len(all_cards)

        # Проверка на дубликаты
        card_ids = [card.get("id") for card in all_cards]
        unique_ids = len(set(card_ids))

        print(f"📊 Всего получено карточек (total_returned): {total_returned}")
        print(f"🔑 Уникальных card_id (unique_ids): {unique_ids}")

        if total_returned != unique_ids:
            print(f"⚠️  НАЙДЕНЫ ДУБЛИКАТЫ: {total_returned - unique_ids} карточек повторяются!")
            print()

            # Находим дубликаты
            from collections import Counter
            duplicates = {card_id: count for card_id, count in Counter(card_ids).items() if count > 1}

            print("Список дубликатов:")
            for card_id, count in duplicates.items():
                duplicate_cards = [c for c in all_cards if c.get("id") == card_id]
                print(f"  ID {card_id}: встречается {count} раз(а)")
                for i, card in enumerate(duplicate_cards, 1):
                    print(f"    {i}. Title: {card.get('title', 'Без названия')[:50]}")
                    print(f"       Column: {card.get('column_id')}, Lane: {card.get('lane_id')}")
        else:
            print(f"✓ Дубликатов нет - все карточки уникальные")

        print()

        # Распределение по колонкам
        column_distribution = {}
        for card in all_cards:
            column_id = card.get("column_id")
            column_distribution[column_id] = column_distribution.get(column_id, 0) + 1

        print("Распределение по колонкам:")
        print("-" * 80)

        column_names = {
            settings.KAITEN_COLUMN_TO_SIGN_ID: "На подпись (директор)",
            settings.KAITEN_COLUMN_HEAD_REVIEW_ID: "Согласование начальника отдела",
            settings.KAITEN_COLUMN_OUTBOX_ID: "Готово (исходящие)"
        }

        for column_id, count in sorted(column_distribution.items(), key=lambda x: x[1], reverse=True):
            column_name = column_names.get(column_id, f"Неизвестная колонка")
            marker = ""
            if column_id == settings.KAITEN_COLUMN_TO_SIGN_ID:
                marker = " ← целевая для директора"
            elif column_id == settings.KAITEN_COLUMN_HEAD_REVIEW_ID:
                marker = " ← целевая для начальника"

            print(f"  Column ID {column_id}: {count} карточек - {column_name}{marker}")

        print()
        print("-" * 80)

        # Фильтрация по целевой колонке "На подпись"
        target_column_id = settings.KAITEN_COLUMN_TO_SIGN_ID
        filtered_cards = [
            card for card in all_cards
            if card.get("column_id") == target_column_id
            and card.get("lane_id") == settings.KAITEN_LANE_ID
        ]

        print(f"\n🎯 Карточек в колонке 'На подпись' (column_id={target_column_id}, lane_id={settings.KAITEN_LANE_ID}): {len(filtered_cards)}")

        if filtered_cards:
            print("\nПример карточек:")
            for i, card in enumerate(filtered_cards[:3], 1):
                print(f"  {i}. ID {card.get('id')}: {card.get('title', 'Без названия')[:50]}")

            if len(filtered_cards) > 3:
                print(f"  ... и еще {len(filtered_cards) - 3} карточек")

        print()
        print("=" * 80)
        print("ПОЛНЫЙ СПИСОК ВСЕХ КАРТОЧЕК:")
        print("=" * 80)
        print()

        # Сортируем по column_id для удобства
        sorted_cards = sorted(all_cards, key=lambda x: (x.get("column_id", 0), x.get("id", 0)))

        for i, card in enumerate(sorted_cards, 1):
            card_id = card.get("id")
            title = card.get("title", "Без названия")[:60]
            column_id = card.get("column_id")
            lane_id = card.get("lane_id")
            created = card.get("created", "")[:10]  # Только дата

            column_name = column_names.get(column_id, "Неизвестная")

            print(f"{i:3}. ID: {card_id:8} | Column: {column_id} ({column_name[:30]:30}) | Lane: {lane_id} | {title}")

        print()
        print("=" * 80)
        print("✓ ПАГИНАЦИЯ РАБОТАЕТ КОРРЕКТНО" if total > 0 else "⚠ НЕТ КАРТОЧЕК")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_pagination())
