#!/usr/bin/env python3
"""
Скрипт для отладки структуры карточки Kaiten и вывода писем (файлов)
"""

import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.dirname(__file__))

from app.services.kaiten_service import KaitenService
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def debug_cards():
    print("=" * 80)
    print("ОТЛАДКА СТРУКТУРЫ КАРТОЧЕК И ВЫВОДА ПИСЕМ")
    print("=" * 80)
    print()

    # Создаем сервис без моков
    service = KaitenService(use_mock=False)

    # Получаем карточки из колонки "На подпись"
    column_id = settings.KAITEN_COLUMN_TO_SIGN_ID
    print(f"Получение карточек из колонки 'На подпись' (ID: {column_id})...")
    print()

    cards = await service.get_cards_by_column_id(column_id)

    print(f"Найдено карточек: {len(cards)}")
    print("-" * 80)
    print()

    for idx, card in enumerate(cards, 1):
        print(f"📋 КАРТОЧКА #{idx}")
        print("=" * 80)

        # Основная информация
        card_id = card.get("id")
        title = card.get("title")
        column_id = card.get("column_id")
        board_id = card.get("board_id")
        lane_id = card.get("lane_id")

        print(f"ID карточки: {card_id}")
        print(f"Название: {title}")
        print(f"Column ID: {column_id}")
        print(f"Board ID: {board_id}")
        print(f"Lane ID: {lane_id}")
        print()

        # Свойства (properties) - custom fields
        print("🔧 СВОЙСТВА (Properties - Custom Fields):")
        print("-" * 80)
        properties = card.get("properties", {})

        if isinstance(properties, dict):
            print(f"Тип: dict (словарь)")
            print(f"Количество свойств: {len(properties)}")
            print()

            for prop_id, prop_value in properties.items():
                print(f"  • {prop_id}: {prop_value}")
                if isinstance(prop_value, dict):
                    print(f"    Тип значения: dict")
                    for k, v in prop_value.items():
                        print(f"      - {k}: {v}")
        elif isinstance(properties, list):
            print(f"Тип: list (список)")
            print(f"Количество свойств: {len(properties)}")
            print()
            for prop in properties:
                print(f"  • {prop}")
        else:
            print(f"Тип: {type(properties)}")
            print(f"Значение: {properties}")

        print()

        # Извлекаем номер и дату входящего документа
        incoming_no = KaitenService.get_incoming_no(card)
        incoming_date = KaitenService.get_incoming_date(card)

        print(f"📄 ВХОДЯЩИЙ ДОКУМЕНТ:")
        print(f"  Номер (id_228499): {incoming_no}")
        print(f"  Дата (id_228500): {incoming_date}")
        print()

        # Файлы (files)
        print("📎 ФАЙЛЫ (Files):")
        print("-" * 80)
        files = card.get("files", [])

        if files:
            print(f"Количество файлов: {len(files)}")
            print()

            for file_idx, file_info in enumerate(files, 1):
                file_id = file_info.get("id")
                file_name = file_info.get("name")
                file_url = file_info.get("url")
                file_size = file_info.get("size")
                file_mime = file_info.get("mime_type")

                print(f"  {file_idx}. {file_name}")
                print(f"     ID: {file_id}")
                print(f"     URL: {file_url}")
                print(f"     Размер: {file_size} байт")
                print(f"     MIME: {file_mime}")

                # Проверяем, это главный DOCX или приложение
                is_main = file_name.startswith("исх_") and file_name.endswith(".docx")
                if is_main:
                    print(f"     ⭐ ГЛАВНЫЙ ДОКУМЕНТ (исх_*.docx)")
                else:
                    print(f"     📋 Приложение")
                print()
        else:
            print("Файлов нет")

        print()

        # Полная структура карточки в JSON
        print("📦 ПОЛНАЯ СТРУКТУРА КАРТОЧКИ (JSON):")
        print("-" * 80)
        print(json.dumps(card, indent=2, ensure_ascii=False))
        print()
        print("=" * 80)
        print()
        print()


if __name__ == "__main__":
    asyncio.run(debug_cards())
