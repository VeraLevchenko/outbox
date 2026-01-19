"""
Скрипт для создания тестовых пользователей в БД
Запуск: python generate_users.py
"""
from app.models.database import SessionLocal
from app.models.user import User
from app.services.auth_service import auth_service


def create_users():
    """Создать тестовых пользователей"""
    db = SessionLocal()

    try:
        # Проверяем существующих пользователей
        existing_users = db.query(User).all()
        print(f"Found {len(existing_users)} existing users:")
        for user in existing_users:
            print(f"  - {user.username} (role: {user.role})")

        # Создаем пользователей если их нет
        users_to_create = [
            {
                'username': 'director',
                'password': 'director123',
                'role': 'director'
            },
            {
                'username': 'head',
                'password': 'head123',
                'role': 'head'
            }
        ]

        for user_data in users_to_create:
            # Проверяем есть ли уже такой пользователь
            existing = db.query(User).filter(User.username == user_data['username']).first()
            if existing:
                print(f"\nUser '{user_data['username']}' already exists. Skipping.")
                continue

            # Создаем нового пользователя
            hashed_password = auth_service.get_password_hash(user_data['password'])
            new_user = User(
                username=user_data['username'],
                hashed_password=hashed_password,
                role=user_data['role']
            )
            db.add(new_user)
            print(f"\nCreated user '{user_data['username']}' with password '{user_data['password']}'")

        db.commit()
        print("\n✅ Users created successfully!")

        # Показываем всех пользователей
        all_users = db.query(User).all()
        print(f"\nTotal users in database: {len(all_users)}")
        for user in all_users:
            print(f"  - {user.username} (role: {user.role})")

    except Exception as e:
        print(f"❌ Error creating users: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_users()
