from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import date
from sqlalchemy import func
from sqlalchemy.orm import Session
import os
import shutil
from app.models.database import SessionLocal
from app.models.outbox_journal import OutboxJournal
from app.schemas.journal_schemas import (
    JournalEntryCreate,
    JournalEntryUpdate,
    JournalEntryResponse,
    JournalListResponse
)
from app.services.excel_service import excel_service
from app.services.config_service import config_service
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
                formatted_number=entry.formatted_number,
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
        # Проверяем, что числовая часть номера не занята
        existing_no = db.query(OutboxJournal).filter(
            OutboxJournal.outgoing_no == entry.outgoing_no
        ).first()

        if existing_no:
            raise HTTPException(
                status_code=400,
                detail=f"Числовая часть номера {entry.outgoing_no} уже занята"
            )

        # Проверяем, что форматированный номер не занят
        existing_formatted = db.query(OutboxJournal).filter(
            OutboxJournal.formatted_number == entry.formatted_number
        ).first()

        if existing_formatted:
            raise HTTPException(
                status_code=400,
                detail=f"Номер {entry.formatted_number} уже существует"
            )

        # Создаем новую запись
        new_entry = OutboxJournal(
            outgoing_no=entry.outgoing_no,
            formatted_number=entry.formatted_number,
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
            formatted_number=new_entry.formatted_number,
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


@router.put("/entries/{entry_id}", response_model=JournalEntryResponse)
async def update_journal_entry(
    entry_id: int,
    entry_update: JournalEntryUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Обновить запись в журнале

    Args:
        entry_id: ID записи
        entry_update: Данные для обновления
        db: Сессия БД
        current_user: Текущий пользователь

    Returns:
        Обновленная запись
    """
    try:
        # Ищем запись
        entry = db.query(OutboxJournal).filter(OutboxJournal.id == entry_id).first()

        if not entry:
            raise HTTPException(status_code=404, detail=f"Journal entry {entry_id} not found")

        # Проверяем уникальность formatted_number, если он изменяется
        if entry_update.formatted_number is not None and entry_update.formatted_number != entry.formatted_number:
            existing = db.query(OutboxJournal).filter(
                OutboxJournal.formatted_number == entry_update.formatted_number,
                OutboxJournal.id != entry_id
            ).first()

            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Formatted number {entry_update.formatted_number} already exists"
                )

        # Обновляем поля
        if entry_update.formatted_number is not None:
            entry.formatted_number = entry_update.formatted_number
            # Извлекаем числовую часть из formatted_number (например, "4-01" -> 4)
            try:
                numeric_part = entry_update.formatted_number.split('-')[0]
                entry.outgoing_no = int(numeric_part)
            except (ValueError, IndexError):
                # Если не удалось извлечь, оставляем как есть
                pass
        elif entry_update.outgoing_no is not None:
            # Если обновляется только outgoing_no без formatted_number
            entry.outgoing_no = entry_update.outgoing_no
        if entry_update.outgoing_date is not None:
            entry.outgoing_date = entry_update.outgoing_date
        if entry_update.to_whom is not None:
            entry.to_whom = entry_update.to_whom
        if entry_update.executor is not None:
            entry.executor = entry_update.executor
        if entry_update.folder_path is not None:
            entry.folder_path = entry_update.folder_path

        db.commit()
        db.refresh(entry)

        return JournalEntryResponse(
            id=entry.id,
            outgoing_no=entry.outgoing_no,
            formatted_number=entry.formatted_number,
            outgoing_date=entry.outgoing_date,
            to_whom=entry.to_whom,
            executor=entry.executor,
            folder_path=entry.folder_path,
            created_at=entry.created_at.isoformat() if entry.created_at else ""
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating journal entry: {str(e)}")


@router.delete("/entries/{entry_id}")
async def delete_journal_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Удалить запись из журнала и папку с файлами

    Args:
        entry_id: ID записи
        db: Сессия БД
        current_user: Текущий пользователь

    Returns:
        Сообщение об успешном удалении
    """
    try:
        # Ищем запись
        entry = db.query(OutboxJournal).filter(OutboxJournal.id == entry_id).first()

        if not entry:
            raise HTTPException(status_code=404, detail=f"Journal entry {entry_id} not found")

        # Удаляем папку с файлами, если она существует
        if entry.folder_path and os.path.exists(entry.folder_path):
            try:
                shutil.rmtree(entry.folder_path)
            except Exception as e:
                # Логируем ошибку, но продолжаем удаление записи из БД
                print(f"Warning: Failed to delete folder {entry.folder_path}: {str(e)}")

        # Удаляем запись из БД
        db.delete(entry)
        db.commit()

        return {"message": f"Journal entry {entry_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting journal entry: {str(e)}")


@router.get("/next-number")
async def get_next_outgoing_number(
    executor_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Получить следующий доступный исходящий номер

    Args:
        executor_id: ID исполнителя из Kaiten (опционально)
        db: Сессия БД
        current_user: Текущий пользователь

    Returns:
        Следующий доступный номер с форматированием согласно правилам
    """
    try:
        # Получаем правила нумерации для исполнителя
        numbering_rule = config_service.get_numbering_rule_for_executor(executor_id) if executor_id else config_service.get_numbering_rules().get('default', {})

        # Извлекаем параметры из правила
        executor_code = numbering_rule.get('executor_code', '00')
        number_format = numbering_rule.get('format', '{number}-{executor_code}')
        start_number = numbering_rule.get('start_number', 1)
        reset_yearly = numbering_rule.get('reset_yearly', False)

        # Определяем фильтр для поиска максимального номера
        query = db.query(func.max(OutboxJournal.outgoing_no))

        # Если нумерация сбрасывается ежегодно, фильтруем по текущему году
        if reset_yearly:
            current_year = date.today().year
            query = query.filter(
                func.extract('year', OutboxJournal.outgoing_date) == current_year
            )

        # Сквозная нумерация независимо от исполнителя - НЕ фильтруем по executor

        # Получаем максимальный номер
        max_no = query.scalar()
        next_number = (max_no or (start_number - 1)) + 1

        # Форматируем номер согласно правилу (например, 42-10)
        formatted_number = number_format.format(
            number=next_number,
            executor_code=executor_code
        )

        return {
            "next_number": next_number,
            "formatted_number": formatted_number,
            "executor_code": executor_code,
            "executor_id": executor_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting next number: {str(e)}")


@router.post("/reload-config")
async def reload_configuration(
    current_user: dict = Depends(get_current_user)
):
    """
    Перезагрузить конфигурационные файлы (executors.json, numbering_rules.json)
    без перезапуска сервера

    Args:
        current_user: Текущий пользователь

    Returns:
        Сообщение об успешной перезагрузке
    """
    try:
        config_service.reload_configs()
        return {
            "message": "Configuration reloaded successfully",
            "executors_count": len(config_service.get_executors()),
            "numbering_rules_count": len(config_service.get_numbering_rules())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reloading configuration: {str(e)}")


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
