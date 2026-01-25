import asyncio
import httpx
from typing import List, Dict, Optional
from datetime import datetime
from app.core.config import settings


class KaitenService:
    """Сервис для работы с Kaiten API"""

    def __init__(self):
        self.api_url = settings.KAITEN_API_URL
        self.api_token = settings.KAITEN_API_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        self.use_mock = settings.KAITEN_USE_MOCK  # Использовать mock-данные только если явно указано

    def _get_mock_cards(self, column_name: str) -> List[Dict]:
        """Генерировать mock-данные для тестирования"""
        if column_name == "На подпись":
            return [
                {
                    "id": 1001,
                    "title": "Письмо в Минфин о налоговых льготах",
                    "column_name": "На подпись",
                    "properties": {
                        "id_228499": "12345"  # incoming_no
                    },
                    "files": [
                        {"name": "исх_письмо_минфин.docx", "url": "http://example.com/file1.docx"},
                        {"name": "приложение_1.pdf", "url": "http://example.com/file2.pdf"}
                    ],
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": 1002,
                    "title": "Договор на поставку оборудования",
                    "column_name": "На подпись",
                    "properties": {
                        "id_228499": "12346"
                    },
                    "files": [
                        {"name": "исх_договор.docx", "url": "http://example.com/file3.docx"}
                    ],
                    "created_at": datetime.now().isoformat()
                }
            ]
        elif column_name == "Проект готов. Согласование начальника отдела":
            return [
                {
                    "id": 2001,
                    "title": "Отчет о проделанной работе",
                    "column_name": "Проект готов. Согласование начальника отдела",
                    "properties": {
                        "id_228499": "12347"
                    },
                    "files": [
                        {"name": "исх_отчет.docx", "url": "http://example.com/file4.docx"}
                    ],
                    "created_at": datetime.now().isoformat()
                }
            ]
        return []

    async def get_cards_from_column(self, column_name: str) -> List[Dict]:
        """
        Получить карточки из указанной колонки

        Args:
            column_name: Название колонки ("На подпись" или "Проект готов. Согласование начальника отдела")

        Returns:
            Список карточек
        """
        # В mock режиме используем mock-данные
        if self.use_mock:
            print(f"[Mock] Returning mock cards for column: {column_name}")
            return self._get_mock_cards(column_name)

        # Определяем ID колонки по названию
        column_id = None
        if column_name == "На подпись":
            column_id = settings.KAITEN_COLUMN_TO_SIGN_ID
        elif column_name == "Проект готов. Согласование начальника отдела":
            column_id = settings.KAITEN_COLUMN_HEAD_REVIEW_ID

        if not column_id:
            print(f"Unknown column name: {column_name}")
            return []

        # Используем настоящий Kaiten API
        async with httpx.AsyncClient() as client:
            try:
                # Получаем карточки из конкретной колонки
                response = await client.get(
                    f"{self.api_url}/cards",
                    headers=self.headers,
                    params={"column_id": column_id},
                    timeout=10.0
                )

                if response.status_code == 200:
                    cards = response.json()
                    print(f"[Kaiten API] Found {len(cards)} cards in column '{column_name}' (ID: {column_id})")
                    return cards
                else:
                    print(f"Kaiten API error: {response.status_code}, Response: {response.text}")
                    return []
            except Exception as e:
                print(f"Error fetching cards from Kaiten: {e}")
                return []

    async def move_card(
        self,
        card_id: int,
        target_column: str,
        comment: Optional[str] = None,
        outgoing_no: Optional[str] = None,
        outgoing_date: Optional[str] = None
    ) -> bool:
        """
        Переместить карточку в другую колонку

        Args:
            card_id: ID карточки
            target_column: Название целевой колонки
            comment: Опциональный комментарий
            outgoing_no: Исходящий номер (форматированный, например "04-01")
            outgoing_date: Исходящая дата (формат YYYY-MM-DD)

        Returns:
            True если успешно, False если ошибка
        """
        # Определяем ID целевой колонки
        column_id = None
        if target_column == "На подпись":
            column_id = settings.KAITEN_COLUMN_TO_SIGN_ID
        elif target_column == "Отправка":
            column_id = settings.KAITEN_COLUMN_OUTBOX_ID
        elif target_column == "Проект готов. Согласование начальника отдела":
            column_id = settings.KAITEN_COLUMN_HEAD_REVIEW_ID

        if not column_id:
            print(f"Unknown target column: {target_column}")
            return False

        async with httpx.AsyncClient() as client:
            try:
                payload = {
                    "column_id": column_id
                }

                if comment:
                    payload["comment"] = comment

                # Добавляем properties, если указаны исходящий номер и дата
                if outgoing_no or outgoing_date:
                    properties = {}

                    if outgoing_no:
                        properties[settings.KAITEN_PROPERTY_OUTGOING_NO] = outgoing_no

                    if outgoing_date:
                        properties[settings.KAITEN_PROPERTY_OUTGOING_DATE] = {
                            "date": outgoing_date
                        }

                    payload["properties"] = properties
                    print(f"[Kaiten API] Setting properties: outgoing_no={outgoing_no}, outgoing_date={outgoing_date}")

                response = await client.patch(
                    f"{self.api_url}/cards/{card_id}",
                    headers=self.headers,
                    json=payload,
                    timeout=10.0
                )

                if response.status_code in [200, 201]:
                    print(f"[Kaiten API] Card {card_id} moved to '{target_column}' (ID: {column_id})")
                    return True
                else:
                    print(f"[Kaiten API] Error moving card {card_id}: {response.status_code}, Response: {response.text}")
                    return False
            except Exception as e:
                print(f"Error moving card {card_id}: {e}")
                return False

    async def get_card_by_id(self, card_id: int) -> Optional[Dict]:
        """
        Получить одну карточку по ID

        Args:
            card_id: ID карточки

        Returns:
            Данные карточки или None если не найдена
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.api_url}/cards/{card_id}",
                    headers=self.headers,
                    timeout=10.0
                )

                if response.status_code == 200:
                    card = response.json()
                    print(f"[Kaiten API] Found card {card_id}: {card.get('title')}")
                    return card
                else:
                    print(f"[Kaiten API] Card {card_id} not found: {response.status_code}")
                    return None
            except Exception as e:
                print(f"Error fetching card {card_id}: {e}")
                return None

    async def get_card_members(self, card_id: int) -> List[Dict]:
        """
        Получить участников карточки

        Args:
            card_id: ID карточки

        Returns:
            Список участников карточки с информацией о типе
        """
        # В mock режиме возвращаем тестовые данные
        if self.use_mock:
            print(f"[Mock] Returning mock members for card {card_id}")
            return [
                {
                    "user_id": 531592,
                    "full_name": "Евгения",
                    "type": 2  # исполнитель
                },
                {
                    "user_id": 123456,
                    "full_name": "Иван Иванов",
                    "type": 1  # наблюдатель
                }
            ]

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.api_url}/cards/{card_id}/members",
                    headers=self.headers,
                    timeout=10.0
                )

                if response.status_code == 200:
                    members = response.json()
                    print(f"[Kaiten API] Found {len(members)} members for card {card_id}")
                    return members
                else:
                    print(f"[Kaiten API] Error fetching members for card {card_id}: {response.status_code}")
                    return []
            except Exception as e:
                print(f"Error fetching members for card {card_id}: {e}")
                return []

    async def get_executor_from_card(self, card_id: int) -> Optional[Dict]:
        """
        Получить исполнителя карточки (member с type=2)

        Args:
            card_id: ID карточки

        Returns:
            Данные исполнителя или None если не найден
        """
        members = await self.get_card_members(card_id)

        # Ищем участника с type=2 (исполнитель)
        for member in members:
            if member.get('type') == 2:
                print(f"[Kaiten API] Found executor for card {card_id}: {member.get('full_name')}")
                return member

        print(f"[Kaiten API] No executor (type=2) found for card {card_id}")
        return None

    async def poll_cards(self, column_name: str, interval: int = None):
        """
        Polling карточек из колонки

        Args:
            column_name: Название колонки для polling
            interval: Интервал опроса в секундах (по умолчанию из настроек)
        """
        if interval is None:
            interval = settings.KAITEN_POLL_INTERVAL

        while True:
            cards = await self.get_cards_from_column(column_name)
            print(f"[Polling] Found {len(cards)} cards in '{column_name}'")
            # TODO: Отправить карточки через WebSocket или другой механизм
            await asyncio.sleep(interval)


# Singleton instance
kaiten_service = KaitenService()
