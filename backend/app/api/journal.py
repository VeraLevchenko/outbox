from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import date
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.database import SessionLocal
from app.models.outbox_journal import OutboxJournal
from app.schemas.journal_schemas import (
    JournalEntryCreate,
    JournalEntryResponse,
    JournalListResponse
)
from app.services.excel_service import excel_service
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/journal", tags=["journal"])


def get_db():
    """Dependency для получения сессии БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/entries", response_model=JournalListResponse)
async def get_journal_entries(
    skip: int = 0,
    limit: int = 100,
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Получить записи журнала

    Args:
        skip: Количество записей для пропуска (пагинация)
        limit: Максимальное количество записей
        year: Фильтр по году
        month: Фильтр по месяцу
        db: Сессия БД
        current_user: Текущий пользователь

    Returns:
        Список записей журнала
    """
    try:
        query = db.query(OutboxJournal)

        # Фильтры
        if year:
            query = query.filter(
                func.extract('year', OutboxJournal.outgoing_date) == year
            )
        if month:
            query = query.filter(
                func.extract('month', OutboxJournal.outgoing_date) == month
            )

        # Общее количество
        total = query.count()

        # Получаем записи
        entries = query.order_by(
            OutboxJournal.outgoing_date.desc()
        ).offset(skip).limit(limit).all()

        # Форматируем ответ
        entries_data = [
            JournalEntryResponse(
                id=entry.id,
                outgoing_no=entry.outgoing_no,
                outgoing_date=entry.outgoing_date,
                to_whom=entry.to_whom,
                executor=entry.executor,
                folder_path=entry.folder_path,
                created_at=entry.created_at.isoformat() if entry.created_at else ""
            )
            for entry in entries
        ]

        return JournalListResponse(entries=entries_data, total=total)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching journal entries: {str(e)}")


@router.post("/entries", response_model=JournalEntryResponse, status_code=201)
async def create_journal_entry(
    entry: JournalEntryCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Создать новую запись в журнале

    Args:
        entry: Данные записи
        db: Сессия БД
        current_user: Текущий пользователь

    Returns:
        Созданная запись
    """
    try:
        # Проверяем, что номер не занят
        existing = db.query(OutboxJournal).filter(
            OutboxJournal.outgoing_no == entry.outgoing_no
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Outgoing number {entry.outgoing_no} already exists"
            )

        # Создаем новую запись
        new_entry = OutboxJournal(
            outgoing_no=entry.outgoing_no,
            outgoing_date=entry.outgoing_date,
            to_whom=entry.to_whom,
            executor=entry.executor,
            folder_path=entry.folder_path
        )

        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)

        return JournalEntryResponse(
            id=new_entry.id,
            outgoing_no=new_entry.outgoing_no,
            outgoing_date=new_entry.outgoing_date,
            to_whom=new_entry.to_whom,
            executor=new_entry.executor,
            folder_path=new_entry.folder_path,
            created_at=new_entry.created_at.isoformat() if new_entry.created_at else ""
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating journal entry: {str(e)}")


@router.get("/next-number")
async def get_next_outgoing_number(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Получить следующий доступный исходящий номер

    Args:
        db: Сессия БД
        current_user: Текущий пользователь

    Returns:
        Следующий доступный номер
    """
    try:
        # Получаем максимальный номер
        max_no = db.query(func.max(OutboxJournal.outgoing_no)).scalar()

        next_no = (max_no or 0) + 1

        return {"next_number": next_no}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting next number: {str(e)}")


@router.get("/export/xlsx")
async def export_journal_to_xlsx(
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Экспортировать журнал в формат XLSX

    Args:
        year: Фильтр по году
        month: Фильтр по месяцу
        db: Сессия БД
        current_user: Текущий пользователь

    Returns:
        XLSX файл
    """
    try:
        query = db.query(OutboxJournal)

        # Фильтры
        if year:
            query = query.filter(
                func.extract('year', OutboxJournal.outgoing_date) == year
            )
        if month:
            query = query.filter(
                func.extract('month', OutboxJournal.outgoing_date) == month
            )

        # Получаем записи
        entries = query.order_by(OutboxJournal.outgoing_date.desc()).all()

        # Генерируем Excel файл
        excel_buffer = excel_service.generate_journal_xlsx(entries)

        # Формируем имя файла
        filename = "journal"
        if year:
            filename += f"_{year}"
        if month:
            filename += f"_{month:02d}"
        filename += ".xlsx"

        # Возвращаем файл
        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting journal: {str(e)}")
