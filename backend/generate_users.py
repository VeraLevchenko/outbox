#!/usr/bin/env python3
"""
Скрипт для создания файла users.json с пользователями (использует bcrypt напрямую)
"""
import json
import bcrypt

# Пароль для всех пользователей
PASSWORD = "логин123"

# Создаем хеш пароля
password_hash = bcrypt.hashpw(PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

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
