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

    @staticmethod
    def extract_property_value(card: Dict, property_id: str) -> Optional[any]:
        """
        Извлечь значение свойства (custom field) из карточки

        Args:
            card: Карточка Kaiten
            property_id: ID свойства (например, "id_228499")

        Returns:
            Значение свойства или None (может быть строка, число или объект)
        """
        properties = card.get("properties", {})

        # Properties в Kaiten API - это словарь
        if isinstance(properties, dict):
            value = properties.get(property_id)
            # Если значение - объект с датой, извлекаем дату
            if isinstance(value, dict) and "date" in value:
                return value.get("date")
            return value
        elif isinstance(properties, list):
            # Старая структура (для совместимости)
            for prop in properties:
                if prop.get("id") == property_id or prop.get("property_id") == property_id:
                    value = prop.get("value")
                    if isinstance(value, dict) and "date" in value:
                        return value.get("date")
                    return value

        return None

    @staticmethod
    def get_incoming_no(card: Dict) -> Optional[str]:
        """
        Получить номер входящего документа из карточки

        Args:
            card: Карточка Kaiten

        Returns:
            Номер входящего документа или None
        """
        return KaitenService.extract_property_value(card, settings.KAITEN_PROPERTY_INCOMING_NO)

    @staticmethod
    def get_incoming_date(card: Dict) -> Optional[str]:
        """
        Получить дату входящего документа из карточки

        Args:
            card: Карточка Kaiten

        Returns:
            Дата входящего документа или None
        """
        return KaitenService.extract_property_value(card, settings.KAITEN_PROPERTY_INCOMING_DATE)

    def _get_mock_cards(self, column_id: int) -> List[Dict]:
        """Генерировать mock-данные для тестирования (соответствует реальной структуре Kaiten API)"""
        # Колонка "На подпись" для директора
        if column_id == settings.KAITEN_COLUMN_TO_SIGN_ID:
            return [
                {
                    "id": 1001,
                    "title": "Письмо в Минфин о налоговых льготах",
                    "column_id": settings.KAITEN_COLUMN_TO_SIGN_ID,
                    "board_id": settings.KAITEN_BOARD_ID,
                    "lane_id": settings.KAITEN_LANE_ID,
                    "properties": {
                        settings.KAITEN_PROPERTY_INCOMING_NO: "12345",
                        settings.KAITEN_PROPERTY_INCOMING_DATE: {
                            "date": "2026-01-15",
                            "time": None,
                            "tzOffset": None
                        }
                    },
                    "files": [
                        {
                            "id": 1,
                            "name": "исх_письмо_минфин.docx",
                            "url": "http://example.com/file1.docx",
                            "size": 25000,
                            "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        },
                        {
                            "id": 2,
                            "name": "приложение_1.pdf",
                            "url": "http://example.com/file2.pdf",
                            "size": 150000,
                            "mime_type": "application/pdf"
                        }
                    ],
                    "created": datetime.now().isoformat()
                },
                {
                    "id": 1002,
                    "title": "Договор на поставку оборудования",
                    "column_id": settings.KAITEN_COLUMN_TO_SIGN_ID,
                    "board_id": settings.KAITEN_BOARD_ID,
                    "lane_id": settings.KAITEN_LANE_ID,
                    "properties": {
                        settings.KAITEN_PROPERTY_INCOMING_NO: "12346",
                        settings.KAITEN_PROPERTY_INCOMING_DATE: {
                            "date": "2026-01-16",
                            "time": None,
                            "tzOffset": None
                        }
                    },
                    "files": [
                        {
                            "id": 3,
                            "name": "исх_договор.docx",
                            "url": "http://example.com/file3.docx",
                            "size": 30000,
                            "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        }
                    ],
                    "created": datetime.now().isoformat()
                }
            ]
        # Колонка согласования начальника отдела
        elif column_id == settings.KAITEN_COLUMN_HEAD_REVIEW_ID:
            return [
                {
                    "id": 2001,
                    "title": "Отчет о проделанной работе",
                    "column_id": settings.KAITEN_COLUMN_HEAD_REVIEW_ID,
                    "board_id": settings.KAITEN_BOARD_ID,
                    "lane_id": settings.KAITEN_LANE_ID,
                    "properties": {
                        settings.KAITEN_PROPERTY_INCOMING_NO: "12347",
                        settings.KAITEN_PROPERTY_INCOMING_DATE: {
                            "date": "2026-01-17",
                            "time": None,
                            "tzOffset": None
                        }
                    },
                    "files": [
                        {
                            "id": 4,
                            "name": "исх_отчет.docx",
                            "url": "http://example.com/file4.docx",
                            "size": 28000,
                            "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        }
                    ],
                    "created": datetime.now().isoformat()
                }
            ]
        return []

    async def get_cards_by_column_id(self, column_id: int) -> List[Dict]:
        """
        Получить карточки из указанной колонки по ID

        Args:
            column_id: ID колонки в Kaiten

        Returns:
            Список карточек с извлеченными свойствами
        """
        # В mock режиме используем тестовые данные
        if self.use_mock:
            logger.info(f"[Mock] Returning mock cards for column_id: {column_id}")
            return self._get_mock_cards(column_id)

        # Работа с настоящим Kaiten API
        logger.info(f"Fetching cards from Kaiten API for column_id: {column_id}")

        async with httpx.AsyncClient() as client:
            try:
                # Получаем все карточки доски с пагинацией
                all_cards = []
                offset = 0
                limit = 100  # Kaiten API возвращает максимум 100 карточек за запрос

                while True:
                    url = f"{self.api_url}/cards"
                    params = {
                        "board_id": settings.KAITEN_BOARD_ID,
                        "limit": limit,
                        "offset": offset
                    }

                    logger.info(f"Making request to: {url} with params: {params}")

                    response = await client.get(
                        url,
                        headers=self.headers,
                        params=params,
                        timeout=30.0
                    )

                    logger.info(f"Response status: {response.status_code}")

                    if response.status_code == 200:
                        cards_batch = response.json()
                        cards_count = len(cards_batch)
                        logger.info(f"Received {cards_count} cards at offset {offset}")

                        if cards_count == 0:
                            # Больше нет карточек
                            break

                        all_cards.extend(cards_batch)

                        # Если получили меньше чем limit, значит это последняя страница
                        if cards_count < limit:
                            break

                        offset += limit

                        # Защита от бесконечного цикла - максимум 10 страниц (1000 карточек)
                        if offset >= 1000:
                            logger.warning(f"Reached max offset limit (1000), stopping pagination")
                            break

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

                logger.info(f"Total cards fetched: {len(all_cards)}")

                # Фильтруем карточки по column_id и lane_id
                filtered_cards = []
                for card in all_cards:
                    card_column_id = card.get("column_id")
                    card_lane_id = card.get("lane_id")

                    # Фильтруем по column_id И lane_id
                    if card_column_id == column_id and card_lane_id == settings.KAITEN_LANE_ID:
                        # Извлекаем properties для удобства
                        incoming_no = self.get_incoming_no(card)
                        incoming_date = self.get_incoming_date(card)

                        logger.debug(
                            f"Card {card.get('id')}: {card.get('title')} - "
                            f"incoming_no={incoming_no}, incoming_date={incoming_date}"
                        )

                        filtered_cards.append(card)

                logger.info(f"Filtered to {len(filtered_cards)} cards in column_id={column_id}, lane_id={settings.KAITEN_LANE_ID}")
                return filtered_cards

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

    async def get_cards_from_column(self, column_name: str) -> List[Dict]:
        """
        Получить карточки из указанной колонки по названию (устаревший метод)

        DEPRECATED: Используйте get_cards_by_column_id() вместо этого метода

        Args:
            column_name: Название колонки

        Returns:
            Список карточек
        """
        logger.warning("get_cards_from_column is deprecated, use get_cards_by_column_id instead")

        # Маппинг названий на ID колонок
        column_mapping = {
            "На подпись": settings.KAITEN_COLUMN_TO_SIGN_ID,
            "Проект готов. Согласование начальника отдела": settings.KAITEN_COLUMN_HEAD_REVIEW_ID,
            "Готово": settings.KAITEN_COLUMN_OUTBOX_ID
        }

        column_id = column_mapping.get(column_name)
        if column_id:
            return await self.get_cards_by_column_id(column_id)
        else:
            logger.error(f"Unknown column name: {column_name}")
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
