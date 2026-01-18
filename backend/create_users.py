"""
Скрипт для создания пользователей из passwords.txt
"""
from pathlib import Path
from app.models.database import SessionLocal
from app.models.user import User
from bcrypt import hashpw, gensalt


def parse_passwords_file():
    """Читает файл passwords.txt и парсит пользователей"""
    # Ищем passwords.txt в разных возможных местах
    possible_paths = [
        Path(__file__).parent / "passwords.txt",
        Path("/home/vera/outbox/backend/passwords.txt"),
        Path.home() / "outbox" / "backend" / "passwords.txt",
    ]

    passwords_file = None
    for path in possible_paths:
        if path.exists():
            passwords_file = path
            break

    # Если не нашли passwords.txt, используем passwords.txt.example
    if not passwords_file:
        passwords_file = Path(__file__).parent / "passwords.txt.example"
        if not passwords_file.exists():
            print("[Error] Не найден ни passwords.txt, ни passwords.txt.example!")
            return []
        print(f"[Info] Используется {passwords_file}")
    else:
        print(f"[Info] Используется {passwords_file}")

    users = []
    with open(passwords_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Пропускаем пустые строки и комментарии
            if not line or line.startswith('#') or line.startswith('=') or line.startswith('ПАРОЛИ') or line.startswith('ВНИМАНИЕ') or line.startswith('Для'):
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


def create_users_from_passwords():
    """Создать пользователей из passwords.txt в БД"""
    db = SessionLocal()

    try:
        # Проверяем, есть ли уже пользователи
        existing_users = db.query(User).all()
        if existing_users:
            print(f"\n⚠️  В базе уже есть {len(existing_users)} пользователей:")
            for user in existing_users:
                print(f"  - {user.username} (role: {user.role})")

            response = input("\nПересоздать пользователей? (yes/no): ").strip().lower()
            if response != 'yes':
                print("Отмена операции.")
                return

            # Удаляем существующих пользователей
            for user in existing_users:
                db.delete(user)
            db.commit()
            print("✓ Существующие пользователи удалены")

        # Читаем пользователей из passwords.txt
        users_list = parse_passwords_file()

        if not users_list:
            print("[Error] Не удалось прочитать пользователей из файла паролей")
            return

        # Создаем пользователей в БД
        print("\n" + "="*70)
        print("Создание пользователей в базе данных:")
        print("="*70)

        for user_data in users_list:
            hashed_password = hashpw(
                user_data["password"].encode('utf-8'),
                gensalt()
            ).decode('utf-8')

            user = User(
                username=user_data["username"],
                hashed_password=hashed_password,
                role=user_data["role"]
            )
            db.add(user)
            print(f"✓ {user_data['full_name']:<20} | {user_data['username']:<12} | {user_data['role']:<10} | {user_data['password']}")

        db.commit()

        print("="*70)
        print(f"✓ Все пользователи ({len(users_list)}) успешно созданы в БД!")
        print("="*70)

    except Exception as e:
        print(f"\n❌ Ошибка при создании пользователей: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_users_from_passwords()
