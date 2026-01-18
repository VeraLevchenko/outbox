#!/usr/bin/env python3
"""
Скрипт для создания файла users.json с пользователями (использует bcrypt напрямую)
"""
import json
import bcrypt

# Пользователи с индивидуальными паролями
users_list = [
    {
        "username": "levchenko",
        "password": "levchenko123",
        "role": "director",
        "full_name": "Левченко В.С."
    },
    {
        "username": "gabidulina",
        "password": "gabidulina123",
        "role": "head",
        "full_name": "Габидулина Р.Р."
    },
    {
        "username": "gorskaya",
        "password": "gorskaya123",
        "role": "head",
        "full_name": "Горская Т.К."
    }
]

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

# Сохраняем пароли в отдельный файл для справки
with open('passwords.txt', 'w', encoding='utf-8') as f:
    f.write("ПАРОЛИ ПОЛЬЗОВАТЕЛЕЙ (для справки)\n")
    f.write("=" * 50 + "\n\n")
    for user in users_list:
        f.write(f"{user['username']}: {user['password']}\n")
    f.write("\n" + "=" * 50 + "\n")
    f.write("ВНИМАНИЕ: Храните этот файл в безопасности!\n")

print("✓ Файл users.json успешно создан!")
print("✓ Файл passwords.txt создан (для справки паролей)")
print("\nСозданы пользователи:")
print("┌─────────────┬──────────────────┬──────────┬────────────────┐")
print("│ Логин       │ Имя              │ Роль     │ Пароль         │")
print("├─────────────┼──────────────────┼──────────┼────────────────┤")
for user in users_list:
    print(f"│ {user['username']:<11} │ {user['full_name']:<16} │ {user['role']:<8} │ {user['password']:<14} │")
print("└─────────────┴──────────────────┴──────────┴────────────────┘")
