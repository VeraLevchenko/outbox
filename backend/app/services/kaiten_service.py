import asyncio
import httpx
from typing import List, Dict, Optional
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

    async def get_cards_from_column(self, column_name: str) -> List[Dict]:
        """
        Получить карточки из указанной колонки

        Args:
            column_name: Название колонки ("На подпись" или "Проект готов. Согласование начальника отдела")

        Returns:
            Список карточек
        """
        async with httpx.AsyncClient() as client:
            try:
                # TODO: Реализовать запрос к Kaiten API
                # Пока возвращаем заглушку
                response = await client.get(
                    f"{self.api_url}/cards",
                    headers=self.headers,
                    timeout=10.0
                )

                if response.status_code == 200:
                    cards = response.json()
                    # Фильтровать по колонке
                    return [card for card in cards if card.get("column_name") == column_name]
                else:
                    print(f"Kaiten API error: {response.status_code}")
                    return []
            except Exception as e:
                print(f"Error fetching cards from Kaiten: {e}")
                return []

    async def move_card(self, card_id: int, target_column: str, comment: Optional[str] = None) -> bool:
        """
        Переместить карточку в другую колонку

        Args:
            card_id: ID карточки
            target_column: Название целевой колонки
            comment: Опциональный комментарий

        Returns:
            True если успешно, False если ошибка
        """
        async with httpx.AsyncClient() as client:
            try:
                payload = {
                    "column_name": target_column
                }

                if comment:
                    payload["comment"] = comment

                response = await client.post(
                    f"{self.api_url}/cards/{card_id}/move",
                    headers=self.headers,
                    json=payload,
                    timeout=10.0
                )

                return response.status_code in [200, 201]
            except Exception as e:
                print(f"Error moving card {card_id}: {e}")
                return False

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
