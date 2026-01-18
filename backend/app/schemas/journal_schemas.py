from pydantic import BaseModel
from datetime import date
from typing import Optional


class JournalEntryCreate(BaseModel):
    """Схема для создания записи в журнале"""
    outgoing_no: int
    outgoing_date: date
    to_whom: Optional[str] = None
    executor: Optional[str] = None
    folder_path: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "outgoing_no": 123,
                "outgoing_date": "2025-01-18",
                "to_whom": "Министерство финансов РФ",
                "executor": "Иванов И.П.",
                "folder_path": "/mnt/doc/Исходящие/2025/01/123"
            }
        }


class JournalEntryResponse(BaseModel):
    """Схема для ответа с записью журнала"""
    id: int
    outgoing_no: int
    outgoing_date: date
    to_whom: Optional[str] = None
    executor: Optional[str] = None
    folder_path: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "outgoing_no": 123,
                "outgoing_date": "2025-01-18",
                "to_whom": "Министерство финансов РФ",
                "executor": "Иванов И.П.",
                "folder_path": "/mnt/doc/Исходящие/2025/01/123",
                "created_at": "2025-01-18T10:30:00"
            }
        }


class JournalListResponse(BaseModel):
    """Схема для списка записей журнала"""
    entries: list[JournalEntryResponse]
    total: int

    class Config:
        json_schema_extra = {
            "example": {
                "entries": [
                    {
                        "id": 1,
                        "outgoing_no": 123,
                        "outgoing_date": "2025-01-18",
                        "to_whom": "Министерство финансов РФ",
                        "executor": "Иванов И.П.",
                        "folder_path": "/mnt/doc/Исходящие/2025/01/123",
                        "created_at": "2025-01-18T10:30:00"
                    }
                ],
                "total": 1
            }
        }
