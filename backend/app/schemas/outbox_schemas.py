from pydantic import BaseModel
from typing import Optional
from datetime import date


class RegisterRequest(BaseModel):
    """Запрос на регистрацию документа"""
    card_id: int
    to_whom: str  # Кому адресовано письмо


class RegisterResponse(BaseModel):
    """Ответ на запрос регистрации"""
    outgoing_no: int
    formatted_number: str  # Например, "42-10"
    outgoing_date: str  # Формат ДД.ММ.ГГГГ
    executor: str
    executor_id: int
    docx_preview_url: Optional[str] = None
    message: str
