"""
Скрипт для создания тестовых пользователей
"""
from app.models.database import SessionLocal
from app.models.user import User
from bcrypt import hashpw, gensalt


def create_test_users():
    """Создать тестовых пользователей"""
    db = SessionLocal()

    try:
        # Проверяем, есть ли уже пользователи
        existing_users = db.query(User).all()
        if existing_users:
            print(f"В базе уже есть {len(existing_users)} пользователей:")
            for user in existing_users:
                print(f"  - {user.username} (role: {user.role})")
            return

        # Создаем тестовых пользователей
        users_to_create = [
            {"username": "admin", "password": "admin123", "role": "director"},
            {"username": "head", "password": "head123", "role": "head"},
        ]

        for user_data in users_to_create:
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
            print(f"Создан пользователь: {user_data['username']} / {user_data['password']} ({user_data['role']})")

        db.commit()
        print("\nВсе тестовые пользователи успешно созданы!")

    except Exception as e:
        print(f"Ошибка при создании пользователей: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_test_users()
