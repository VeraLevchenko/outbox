from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
from app.services.kaiten_service import kaiten_service, KaitenService
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/kaiten", tags=["kaiten"])


@router.get("/cards")
async def get_cards(role: str = "director") -> Dict:
    """
    Получить карточки из Kaiten в зависимости от роли пользователя

    Args:
        role: Роль пользователя ("director" или "head")

    Returns:
        Объект с полем cards содержащим список карточек
    """
    try:
        logger.info(f"API: Getting cards for role={role}")

        # Определяем ID колонки в зависимости от роли
        if role == "director":
            column_id = settings.KAITEN_COLUMN_TO_SIGN_ID
            logger.info(f"Using column_id={column_id} for director (На подпись)")
        elif role == "head":
            column_id = settings.KAITEN_COLUMN_HEAD_REVIEW_ID
            logger.info(f"Using column_id={column_id} for head (Согласование начальника отдела)")
        else:
            raise HTTPException(status_code=400, detail="Invalid role. Use 'director' or 'head'")

        # Получаем карточки из Kaiten по ID колонки
        cards = await kaiten_service.get_cards_by_column_id(column_id)

        logger.info(f"Retrieved {len(cards)} cards for role={role}")

        # Форматируем карточки для frontend
        formatted_cards = []
        for card in cards:
            # Извлекаем свойства (custom fields)
            incoming_no = KaitenService.get_incoming_no(card)
            incoming_date = KaitenService.get_incoming_date(card)

            formatted_card = {
                "id": card.get("id"),
                "title": card.get("title"),
                "column_id": card.get("column_id"),
                "incoming_no": incoming_no,
                "incoming_date": incoming_date,
                "created_at": card.get("created_at"),
                "files": card.get("files", [])
            }

            formatted_cards.append(formatted_card)
            logger.debug(f"Formatted card: {formatted_card}")

        return {"cards": formatted_cards, "total": len(formatted_cards)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API: Error fetching cards: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching cards: {str(e)}")


@router.post("/cards/{card_id}/move")
async def move_card(
    card_id: int,
    target_column_id: int,
    comment: Optional[str] = None
) -> Dict:
    """
    Переместить карточку в другую колонку

    Args:
        card_id: ID карточки
        target_column_id: ID целевой колонки
        comment: Опциональный комментарий

    Returns:
        Результат операции
    """
    try:
        logger.info(f"API: Moving card {card_id} to column {target_column_id}")
        success = await kaiten_service.move_card(card_id, target_column_id, comment)

        if success:
            return {"status": "success", "message": f"Card {card_id} moved to column {target_column_id}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to move card")
    except Exception as e:
        logger.error(f"API: Error moving card: {e}")
        raise HTTPException(status_code=500, detail=f"Error moving card: {str(e)}")


@router.get("/boards")
async def get_boards() -> Dict:
    """
    Получить список всех досок (для отладки)

    Returns:
        Список досок
    """
    try:
        logger.info("API: Getting boards list")
        boards = await kaiten_service.get_boards()
        return {"boards": boards, "total": len(boards)}
    except Exception as e:
        logger.error(f"API: Error fetching boards: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching boards: {str(e)}")


@router.get("/boards/{board_id}/columns")
async def get_board_columns(board_id: int) -> Dict:
    """
    Получить колонки конкретной доски (для отладки и настройки)

    Args:
        board_id: ID доски

    Returns:
        Список колонок с ID и названиями
    """
    try:
        logger.info(f"API: Getting columns for board {board_id}")
        columns = await kaiten_service.get_board_columns(board_id)
        return {"columns": columns, "total": len(columns)}
    except Exception as e:
        logger.error(f"API: Error fetching columns: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching columns: {str(e)}")


@router.get("/debug/connection")
async def test_connection() -> Dict:
    """
    Проверить подключение к Kaiten API (для отладки)

    Returns:
        Статус подключения
    """
    try:
        logger.info("API: Testing Kaiten connection")
        # Пытаемся получить доски как тест подключения
        boards = await kaiten_service.get_boards()

        if boards is not None:
            return {
                "status": "success",
                "message": "Successfully connected to Kaiten API",
                "boards_count": len(boards),
                "api_url": kaiten_service.api_url,
                "use_mock": kaiten_service.use_mock
            }
        else:
            return {
                "status": "error",
                "message": "Failed to connect to Kaiten API",
                "api_url": kaiten_service.api_url,
                "use_mock": kaiten_service.use_mock
            }
    except Exception as e:
        logger.error(f"API: Connection test failed: {e}")
        return {
            "status": "error",
            "message": f"Connection test failed: {str(e)}",
            "api_url": kaiten_service.api_url,
            "use_mock": kaiten_service.use_mock
        }
