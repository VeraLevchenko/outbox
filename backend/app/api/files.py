from fastapi import APIRouter, HTTPException
from typing import List
from app.services.file_service import file_service
from app.services.kaiten_service import kaiten_service
from app.schemas.file_schemas import (
    IncomingFilesResponse,
    OutgoingFilesResponse,
    GoogleViewerRequest,
    GoogleViewerResponse,
    FileInfo
)

router = APIRouter(prefix="/api/files", tags=["files"])


@router.get("/incoming/{card_id}", response_model=IncomingFilesResponse)
async def get_incoming_files(card_id: int):
    """
    Получить входящие файлы для карточки

    Args:
        card_id: ID карточки Kaiten

    Returns:
        Список входящих файлов с метаданными
    """
    try:
        # Получить карточку из Kaiten чтобы узнать incoming_no
        # Для упрощения используем mock-данные
        if card_id == 1001:
            incoming_no = "12345"
        elif card_id == 1002:
            incoming_no = "12346"
        elif card_id == 2001:
            incoming_no = "12347"
        else:
            raise HTTPException(status_code=404, detail=f"Card {card_id} not found")

        # Получить файлы
        files = file_service.get_incoming_files(incoming_no)

        return IncomingFilesResponse(
            incoming_no=incoming_no,
            files=files,
            total_files=len(files)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching incoming files: {str(e)}")


@router.get("/outgoing/{card_id}", response_model=OutgoingFilesResponse)
async def get_outgoing_files(card_id: int):
    """
    Получить исходящие файлы для карточки

    Args:
        card_id: ID карточки Kaiten

    Returns:
        Главный DOCX файл и приложения
    """
    try:
        # Получить файлы карточки из Kaiten
        # Для mock-данных используем заглушки
        card_files = []
        if card_id == 1001:
            card_files = [
                {"name": "исх_письмо_минфин.docx", "url": "http://example.com/file1.docx"},
                {"name": "приложение_1.pdf", "url": "http://example.com/file2.pdf"}
            ]
        elif card_id == 1002:
            card_files = [
                {"name": "исх_договор.docx", "url": "http://example.com/file3.docx"}
            ]
        elif card_id == 2001:
            card_files = [
                {"name": "исх_отчет.docx", "url": "http://example.com/file4.docx"}
            ]

        # Получить структурированные файлы
        files_data = file_service.get_outgoing_files(card_id, card_files)

        total = 0
        if files_data["main_docx"]:
            total += 1
        total += len(files_data["attachments"])

        return OutgoingFilesResponse(
            card_id=card_id,
            main_docx=files_data["main_docx"],
            attachments=files_data["attachments"],
            total_files=total
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching outgoing files: {str(e)}")


@router.post("/viewer", response_model=GoogleViewerResponse)
async def get_google_viewer_url(request: GoogleViewerRequest):
    """
    Получить URL для просмотра файла через Google Viewer

    Args:
        request: Запрос с URL файла

    Returns:
        URL для Google Viewer
    """
    try:
        viewer_url = file_service.get_google_viewer_url(request.file_url)

        return GoogleViewerResponse(
            viewer_url=viewer_url,
            original_url=request.file_url
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating viewer URL: {str(e)}")


@router.get("/card/{card_id}/all")
async def get_all_files_for_card(card_id: int):
    """
    Получить ВСЕ файлы для карточки (входящие + исходящие)

    Args:
        card_id: ID карточки Kaiten

    Returns:
        Объединенный список всех файлов
    """
    try:
        # Получить входящие файлы
        incoming_response = await get_incoming_files(card_id)

        # Получить исходящие файлы
        outgoing_response = await get_outgoing_files(card_id)

        # Объединить
        all_files = {
            "card_id": card_id,
            "incoming": {
                "incoming_no": incoming_response.incoming_no,
                "files": incoming_response.files,
                "count": incoming_response.total_files
            },
            "outgoing": {
                "main_docx": outgoing_response.main_docx,
                "attachments": outgoing_response.attachments,
                "count": outgoing_response.total_files
            },
            "total_files": incoming_response.total_files + outgoing_response.total_files
        }

        return all_files
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching all files: {str(e)}")
