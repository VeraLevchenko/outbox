#!/usr/bin/env python3
"""
Скрипт для создания файла users.json с пользователями
Запустите один раз для создания файла с захешированными паролями
"""
import json
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Пароль для всех пользователей
PASSWORD = "логин123"

# Создаем хеш пароля
password_hash = pwd_context.hash(PASSWORD)

# Пользователи
users_data = {
    "users": [
        {
            "username": "levchenko",
            "password_hash": password_hash,
            "role": "director",
            "full_name": "Левченко В.С."
        },
        {
            "username": "gabidulina",
            "password_hash": password_hash,
            "role": "head",
            "full_name": "Габидулина Р.Р."
        },
        {
            "username": "gorskaya",
            "password_hash": password_hash,
            "role": "head",
            "full_name": "Горская Т.К."
        }
    ]
}

# Сохраняем в файл
with open('users.json', 'w', encoding='utf-8') as f:
    json.dump(users_data, f, ensure_ascii=False, indent=2)

print("✓ Файл users.json успешно создан!")
print("\nСозданы пользователи:")
print("┌─────────────┬──────────────────┬──────────┐")
print("│ Логин       │ Имя              │ Роль     │")
print("├─────────────┼──────────────────┼──────────┤")
for user in users_data['users']:
    print(f"│ {user['username']:<11} │ {user['full_name']:<16} │ {user['role']:<8} │")
print("└─────────────┴──────────────────┴──────────┘")
print(f"\nПароль для всех: {PASSWORD}")
