import asyncio
import httpx
import logging
from typing import List, Dict, Optional
from datetime import datetime
from app.core.config import settings

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KaitenService:
    """Сервис для работы с Kaiten API"""

    def __init__(self, use_mock: bool = None):
        """
        Args:
            use_mock: Принудительно использовать mock данные.
                     Если None, то используется значение из settings.DEBUG
        """
        self.api_url = settings.KAITEN_API_URL
        self.api_token = settings.KAITEN_API_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        # Использовать mock-данные: либо из параметра, либо из DEBUG режима
        self.use_mock = use_mock if use_mock is not None else settings.DEBUG

        logger.info(f"KaitenService initialized: API URL={self.api_url}, use_mock={self.use_mock}")

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
        # В mock режиме используем тестовые данные
        if self.use_mock:
            logger.info(f"[Mock] Returning mock cards for column: {column_name}")
            return self._get_mock_cards(column_name)

        # Работа с настоящим Kaiten API
        logger.info(f"Fetching cards from Kaiten API for column: {column_name}")

        async with httpx.AsyncClient() as client:
            try:
                # Kaiten API эндпоинт для получения карточек
                url = f"{self.api_url}/cards"

                logger.info(f"Making request to: {url}")
                logger.debug(f"Headers: {self.headers}")

                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=30.0  # Увеличен таймаут для больших досок
                )

                logger.info(f"Response status: {response.status_code}")

                if response.status_code == 200:
                    cards = response.json()
                    logger.info(f"Received {len(cards)} total cards from API")

                    # Фильтруем карточки по названию колонки
                    # Kaiten может возвращать column_name или column_title
                    filtered_cards = []
                    for card in cards:
                        card_column = card.get("column_name") or card.get("column", {}).get("name")
                        if card_column == column_name:
                            filtered_cards.append(card)
                            logger.debug(f"Card {card.get('id')}: {card.get('title')} - matched column")

                    logger.info(f"Filtered to {len(filtered_cards)} cards in column '{column_name}'")
                    return filtered_cards

                elif response.status_code == 401:
                    logger.error("Kaiten API authentication failed - check your API token")
                    logger.error(f"Response: {response.text}")
                    return []

                elif response.status_code == 403:
                    logger.error("Kaiten API access forbidden - check permissions")
                    logger.error(f"Response: {response.text}")
                    return []

                else:
                    logger.error(f"Kaiten API error: {response.status_code}")
                    logger.error(f"Response text: {response.text}")
                    return []

            except httpx.TimeoutException as e:
                logger.error(f"Timeout fetching cards from Kaiten: {e}")
                return []
            except httpx.ConnectError as e:
                logger.error(f"Connection error to Kaiten API: {e}")
                logger.error(f"Check if API URL is correct: {self.api_url}")
                return []
            except Exception as e:
                logger.error(f"Unexpected error fetching cards from Kaiten: {e}", exc_info=True)
                return []

    async def move_card(self, card_id: int, target_column_id: int, comment: Optional[str] = None) -> bool:
        """
        Переместить карточку в другую колонку

        Args:
            card_id: ID карточки
            target_column_id: ID целевой колонки (не название!)
            comment: Опциональный комментарий

        Returns:
            True если успешно, False если ошибка
        """
        logger.info(f"Moving card {card_id} to column {target_column_id}")

        async with httpx.AsyncClient() as client:
            try:
                # В Kaiten API обновление карточки обычно через PATCH /cards/{id}
                payload = {
                    "column_id": target_column_id
                }

                if comment:
                    # Добавляем комментарий отдельным запросом или в description
                    logger.info(f"Adding comment to card {card_id}: {comment}")

                logger.debug(f"Move payload: {payload}")

                response = await client.patch(
                    f"{self.api_url}/cards/{card_id}",
                    headers=self.headers,
                    json=payload,
                    timeout=10.0
                )

                logger.info(f"Move card response status: {response.status_code}")

                if response.status_code in [200, 201, 204]:
                    logger.info(f"Card {card_id} successfully moved to column {target_column_id}")
                    return True
                else:
                    logger.error(f"Failed to move card {card_id}: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return False

            except Exception as e:
                logger.error(f"Error moving card {card_id}: {e}", exc_info=True)
                return False

    async def get_boards(self) -> List[Dict]:
        """
        Получить список всех досок

        Returns:
            Список досок с их колонками
        """
        if self.use_mock:
            logger.info("[Mock] Returning empty boards list")
            return []

        logger.info("Fetching boards from Kaiten API")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.api_url}/boards",
                    headers=self.headers,
                    timeout=30.0
                )

                if response.status_code == 200:
                    boards = response.json()
                    logger.info(f"Received {len(boards)} boards")
                    return boards
                else:
                    logger.error(f"Failed to get boards: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return []

            except Exception as e:
                logger.error(f"Error fetching boards: {e}", exc_info=True)
                return []

    async def get_board_columns(self, board_id: int) -> List[Dict]:
        """
        Получить колонки конкретной доски

        Args:
            board_id: ID доски

        Returns:
            Список колонок с их ID и названиями
        """
        if self.use_mock:
            logger.info(f"[Mock] Returning mock columns for board {board_id}")
            return [
                {"id": 1, "name": "На подпись"},
                {"id": 2, "name": "Проект готов. Согласование начальника отдела"},
                {"id": 3, "name": "Готово"}
            ]

        logger.info(f"Fetching columns for board {board_id}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.api_url}/boards/{board_id}",
                    headers=self.headers,
                    timeout=30.0
                )

                if response.status_code == 200:
                    board = response.json()
                    columns = board.get("columns", [])
                    logger.info(f"Board {board_id} has {len(columns)} columns")

                    for col in columns:
                        logger.info(f"  Column: {col.get('id')} - {col.get('name')}")

                    return columns
                else:
                    logger.error(f"Failed to get board columns: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return []

            except Exception as e:
                logger.error(f"Error fetching board columns: {e}", exc_info=True)
                return []

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
            logger.info(f"[Polling] Found {len(cards)} cards in '{column_name}'")
            # TODO: Отправить карточки через WebSocket или другой механизм
            await asyncio.sleep(interval)


# Singleton instance
# use_mock=False означает, что будет использоваться реальный API,
# если только DEBUG=True в настройках
kaiten_service = KaitenService()
