#!/usr/bin/env python3
"""
Скрипт для проверки и исправления .env файла

Использование:
    python fix_env.py
"""

import os
import re

print("=" * 70)
print("ПРОВЕРКА И ИСПРАВЛЕНИЕ .ENV ФАЙЛА")
print("=" * 70)
print()

# Путь к .env файлу
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")

if not os.path.exists(env_path):
    print("❌ Файл .env не найден!")
    print(f"   Ожидается по пути: {env_path}")
    print()
    print("Создайте .env файл со следующим содержимым:")
    print()
    print("-" * 70)
    with open(os.path.join(os.path.dirname(__file__), "..", ".env.example"), "r") as f:
        print(f.read())
    print("-" * 70)
    exit(1)

# Читаем текущий .env
with open(env_path, "r", encoding="utf-8") as f:
    content = f.read()

print("✓ Файл .env найден")
print()

# Неправильные переменные (которые нужно исправить)
wrong_vars = {
    "board_id": "KAITEN_BOARD_ID",
    "lane_id": "KAITEN_LANE_ID",
    "column_to_sign_id": "KAITEN_COLUMN_TO_SIGN_ID",
    "column_outbox_id": "KAITEN_COLUMN_OUTBOX_ID",
    "column_head_review_id": "KAITEN_COLUMN_HEAD_REVIEW_ID",
    "property_incoming_no": "KAITEN_PROPERTY_INCOMING_NO",
    "property_incoming_date": "KAITEN_PROPERTY_INCOMING_DATE",
}

# Проверяем наличие неправильных переменных
found_issues = False
for wrong, correct in wrong_vars.items():
    pattern = re.compile(f"^{wrong}=", re.MULTILINE)
    if pattern.search(content):
        found_issues = True
        print(f"❌ Найдена неправильная переменная: {wrong}")
        print(f"   Должно быть: {correct}")
        print()

if found_issues:
    print("-" * 70)
    print("ИСПРАВЛЕНИЕ:")
    print("-" * 70)
    print()

    # Исправляем содержимое
    new_content = content
    for wrong, correct in wrong_vars.items():
        pattern = re.compile(f"^{wrong}=", re.MULTILINE)
        new_content = pattern.sub(f"{correct}=", new_content)

    # Сохраняем backup
    backup_path = env_path + ".backup"
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✓ Создан backup: {backup_path}")

    # Сохраняем исправленный файл
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"✓ Файл .env исправлен!")
    print()

    print("Исправленные строки:")
    print("-" * 70)
    for line in new_content.split("\n"):
        for correct in wrong_vars.values():
            if line.startswith(correct + "="):
                print(f"  {line}")
    print("-" * 70)
    print()
    print("✓ Готово! Теперь можете запустить приложение:")
    print("  ./run.sh")
    print()

else:
    print("✓ Все переменные названы правильно!")
    print()

    # Проверяем наличие всех обязательных переменных
    required_vars = [
        "KAITEN_API_URL",
        "KAITEN_API_TOKEN",
        "KAITEN_BOARD_ID",
        "KAITEN_LANE_ID",
        "KAITEN_COLUMN_TO_SIGN_ID",
        "KAITEN_COLUMN_OUTBOX_ID",
        "KAITEN_COLUMN_HEAD_REVIEW_ID",
        "KAITEN_PROPERTY_INCOMING_NO",
        "KAITEN_PROPERTY_INCOMING_DATE",
        "SECRET_KEY"
    ]

    missing_vars = []
    for var in required_vars:
        pattern = re.compile(f"^{var}=", re.MULTILINE)
        if not pattern.search(content):
            missing_vars.append(var)

    if missing_vars:
        print("⚠ Отсутствуют обязательные переменные:")
        for var in missing_vars:
            print(f"  - {var}")
        print()
        print("Добавьте их в .env файл")
    else:
        print("✓ Все обязательные переменные присутствуют!")
        print()
        print("Можете запустить приложение:")
        print("  cd backend")
        print("  ./run.sh")
        print()

print("=" * 70)
