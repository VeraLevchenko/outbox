#!/usr/bin/env python3
"""
Скрипт для генерации users.json на основе passwords.txt
Читает пароли из passwords.txt и создаёт users.json с хешированными паролями
"""
import json
import bcrypt
from pathlib import Path

# Путь к файлу с паролями
PASSWORDS_FILE = Path(__file__).parent / "passwords.txt"


def parse_passwords_file():
    """Читает файл passwords.txt и парсит пользователей"""
    users = []

    if not PASSWORDS_FILE.exists():
        print(f"[Error] Файл {PASSWORDS_FILE} не найден!")
        return users

    with open(PASSWORDS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Пропускаем пустые строки и комментарии
            if not line or line.startswith('#') or line.startswith('=') or line.startswith('ПАРОЛИ') or line.startswith('ВНИМАНИЕ') or line.startswith('Для обновления'):
                continue

            # Парсим строку формата: username:password:role:full_name
            parts = line.split(':')
            if len(parts) == 4:
                users.append({
                    'username': parts[0].strip(),
                    'password': parts[1].strip(),
                    'role': parts[2].strip(),
                    'full_name': parts[3].strip()
                })

    return users


def generate_users_json():
    """Генерирует users.json с хешированными паролями"""

    # Читаем пользователей из passwords.txt
    users_list = parse_passwords_file()

    if not users_list:
        print("[Error] Не удалось прочитать пользователей из passwords.txt")
        return

    # Создаем хеши паролей для каждого пользователя
    users_data = {"users": []}

    for user in users_list:
        password_hash = bcrypt.hashpw(user['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        users_data["users"].append({
            "username": user['username'],
            "password_hash": password_hash,
            "role": user['role'],
            "full_name": user['full_name']
        })

    # Сохраняем в файл users.json
    with open('users.json', 'w', encoding='utf-8') as f:
        json.dump(users_data, f, ensure_ascii=False, indent=2)

    # Выводим результат
    print("✓ Файл users.json успешно создан на основе passwords.txt!")
    print("\nСозданы пользователи:")
    print("┌─────────────┬──────────────────┬──────────┬────────────────┐")
    print("│ Логин       │ Имя              │ Роль     │ Пароль         │")
    print("├─────────────┼──────────────────┼──────────┼────────────────┤")
    for user in users_list:
        print(f"│ {user['username']:<11} │ {user['full_name']:<16} │ {user['role']:<8} │ {user['password']:<14} │")
    print("└─────────────┴──────────────────┴──────────┴────────────────┘")


if __name__ == "__main__":
    generate_users_json()
