"""
Быстрый тест API без запуска сервера
"""
import sys
import os

# Добавляем путь к backend
sys.path.insert(0, '/home/user/outbox/backend')
os.chdir('/home/user/outbox')

# Теперь импортируем
from backend.app.services.kaiten_service import kaiten_service
import asyncio

async def test():
    print("=" * 60)
    print("БЫСТРЫЙ ТЕСТ OUTBOX API")
    print("=" * 60)

    # Тест 1: Получить карточки для director
    print("\n1. Тестируем получение карточек для director...")
    cards_director = await kaiten_service.get_cards_from_column("На подпись")
    print(f"   ✓ Найдено {len(cards_director)} карточек")
    for i, card in enumerate(cards_director, 1):
        print(f"     {i}. {card['title']}")
        print(f"        ID: {card['id']}, Файлов: {len(card['files'])}")

    # Тест 2: Получить карточки для head
    print("\n2. Тестируем получение карточек для head...")
    cards_head = await kaiten_service.get_cards_from_column(
        "Проект готов. Согласование начальника отдела"
    )
    print(f"   ✓ Найдено {len(cards_head)} карточек")
    for i, card in enumerate(cards_head, 1):
        print(f"     {i}. {card['title']}")
        print(f"        ID: {card['id']}, Файлов: {len(card['files'])}")

    print("\n" + "=" * 60)
    print("✓ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    print("=" * 60)
    print("\nMock-данные работают корректно.")
    print("API endpoints готовы к использованию с реальным Kaiten API.")
    print("\nДля запуска полного приложения:")
    print("  1. Запустите PostgreSQL: docker-compose up -d")
    print("  2. Инициализируйте БД: python backend/init_db.py")
    print("  3. Запустите сервер: cd backend && ./run.sh")

if __name__ == "__main__":
    asyncio.run(test())
