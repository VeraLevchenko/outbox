from fastapi import APIRouter, HTTPException
from typing import List, Dict
from app.services.kaiten_service import kaiten_service

router = APIRouter(prefix="/api/kaiten", tags=["kaiten"])


@router.get("/cards")
async def get_cards(role: str = "director") -> List[Dict]:
    """
    Получить карточки из Kaiten в зависимости от роли пользователя

    Args:
        role: Роль пользователя ("director" или "head")

    Returns:
        Список карточек из соответствующей колонки
    """
    try:
        # Определяем колонку в зависимости от роли
        if role == "director":
            column_name = "На подпись"
        elif role == "head":
            column_name = "Проект готов. Согласование начальника отдела"
        else:
            raise HTTPException(status_code=400, detail="Invalid role")

        # Получаем карточки из Kaiten
        cards = await kaiten_service.get_cards_from_column(column_name)

        return cards
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching cards: {str(e)}")


@router.post("/cards/{card_id}/move")
async def move_card(
    card_id: int,
    target_column: str,
    comment: str = None
) -> Dict:
    """
    Переместить карточку в другую колонку

    Args:
        card_id: ID карточки
        target_column: Название целевой колонки
        comment: Опциональный комментарий

    Returns:
        Результат операции
    """
    try:
        success = await kaiten_service.move_card(card_id, target_column, comment)

        if success:
            return {"status": "success", "message": f"Card {card_id} moved to '{target_column}'"}
        else:
            raise HTTPException(status_code=500, detail="Failed to move card")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error moving card: {str(e)}")
