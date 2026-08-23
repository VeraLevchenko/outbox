from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Optional
from pydantic import BaseModel
from app.services.kaiten_service import kaiten_service
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/kaiten", tags=["kaiten"])


class MoveCardRequest(BaseModel):
    target_column: str
    comment: Optional[str] = None
    outgoing_no: Optional[str] = None
    outgoing_date: Optional[str] = None


@router.get("/cards")
async def get_cards(current_user: dict = Depends(get_current_user)) -> List[Dict]:
    """
    Получить карточки из Kaiten в зависимости от роли пользователя

    Args:
        role: Роль пользователя ("director" или "head")

    Returns:
        Список карточек из соответствующей колонки
    """
    try:
        # Роль берём только из проверенного токена, а не из параметра браузера
        role = current_user.get("role")
        if role in {"director", "acting_director"}:
            column_name = "На подпись"
        elif role == "head":
            column_name = "Проект готов. Согласование начальника отдела"
        else:
            raise HTTPException(status_code=400, detail="Invalid role")

        # Получаем карточки из Kaiten
        cards = await kaiten_service.get_cards_from_column(column_name)

        # Начальник видит только карточки, где он назначен ответственным
        if role == "head":
            visible_cards = []
            for card in cards:
                if await kaiten_service.is_responsible(card["id"], current_user["username"], card.get("members")):
                    visible_cards.append(card)
            cards = visible_cards

        return cards
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching cards: {str(e)}")


@router.post("/cards/{card_id}/move")
async def move_card(
    card_id: int,
    request: MoveCardRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict:
    """
    Переместить карточку в другую колонку

    Args:
        card_id: ID карточки
        request: Тело запроса с target_column и comment

    Returns:
        Результат операции
    """
    try:
        role = current_user.get("role")
        allowed_targets = {
            "director": {"Отправка", "На доработку", "На подпись Кирова 71"},
            "acting_director": {"Отправка", "На доработку", "На подпись Кирова 71"},
            "head": {"В работе"},
        }
        if request.target_column not in allowed_targets.get(role, set()):
            raise HTTPException(status_code=403, detail="Недопустимое перемещение для вашей роли")
        if role == "head" and not await kaiten_service.is_responsible(card_id, current_user["username"]):
            raise HTTPException(status_code=403, detail="Карточка назначена другому начальнику отдела")

        success = await kaiten_service.move_card(
            card_id,
            request.target_column,
            request.comment,
            request.outgoing_no,
            request.outgoing_date
        )

        if success:
            return {"status": "success", "message": f"Card {card_id} moved to '{request.target_column}'"}
        else:
            raise HTTPException(status_code=500, detail="Failed to move card")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error moving card: {str(e)}")


@router.get("/cards/{card_id}/members")
async def get_card_members(card_id: int) -> List[Dict]:
    """
    Получить участников карточки

    Args:
        card_id: ID карточки

    Returns:
        Список участников карточки
    """
    try:
        members = await kaiten_service.get_card_members(card_id)
        return members
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching card members: {str(e)}")


@router.get("/cards/{card_id}/executor")
async def get_card_executor(card_id: int) -> Dict:
    """
    Получить исполнителя карточки (member с type=2)

    Args:
        card_id: ID карточки

    Returns:
        Данные исполнителя
    """
    try:
        executor = await kaiten_service.get_executor_from_card(card_id)

        if executor:
            return executor
        else:
            raise HTTPException(status_code=404, detail="No executor found for this card")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching executor: {str(e)}")
