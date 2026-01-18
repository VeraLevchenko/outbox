"""
Скрипт для инициализации базы данных
Создает все таблицы в БД
"""
from app.models.database import Base, engine
from app.models.user import User
from app.models.outbox_journal import OutboxJournal


def init_db():
    """Создать все таблицы в базе данных"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


if __name__ == "__main__":
    init_db()
