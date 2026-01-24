from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from datetime import date, datetime
from pathlib import Path
from pydantic import BaseModel
import io
import uuid
import base64

from app.models.database import SessionLocal
from app.schemas.outbox_schemas import RegisterRequest, RegisterResponse
from app.services.kaiten_service import kaiten_service
from app.services.file_service import file_service
from app.services.docx_service import docx_service
from app.services.config_service import config_service
from app.services.pdf_service import pdf_service
from app.services.cryptopro_service import cryptopro_service
from app.api.auth import get_current_user
from app.api.journal import get_next_outgoing_number

router = APIRouter(prefix="/api/outbox", tags=["outbox"])

# Директория для временных зарегистрированных файлов
TEMP_FILES_DIR = Path(__file__).parent.parent.parent / "temp_files"
TEMP_FILES_DIR.mkdir(exist_ok=True)


def get_db():
    """Dependency для получения сессии БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/prepare-registration", response_model=RegisterResponse)
async def prepare_registration(
    request: RegisterRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Подготовить регистрацию документа:
    - Получить карточку и извлечь title (для поля "Кому")
    - Получить исполнителя из карточки Kaiten (для генерации номера)
    - Сгенерировать номер
    - Заменить плейсхолдеры в DOCX
    - Вернуть информацию для предпросмотра

    Args:
        request: Данные запроса (card_id)
        db: Сессия БД
        current_user: Текущий пользователь

    Returns:
        Данные регистрации с номером и датой
    """
    try:
        # 1. Получаем карточку для извлечения title
        card = await kaiten_service.get_card_by_id(request.card_id)
        if not card:
            raise HTTPException(status_code=404, detail=f"Card {request.card_id} not found")

        # Извлекаем title карточки - это поле "Кому"
        to_whom = card.get('title', '')

        # 2. Получаем исполнителя из карточки Kaiten (для генерации номера)
        executor_data = await kaiten_service.get_executor_from_card(request.card_id)

        if not executor_data:
            raise HTTPException(
                status_code=404,
                detail="Executor not found in card. Please ensure card has a member with type=2"
            )

        executor_id = executor_data.get('user_id')
        executor_name = executor_data.get('full_name')

        # 3. Генерируем следующий номер
        # Используем существующий endpoint get_next_outgoing_number
        from app.api.journal import get_next_outgoing_number as get_next_number_func
        from sqlalchemy import func
        from app.models.outbox_journal import OutboxJournal

        # Получаем правила нумерации для исполнителя
        numbering_rule = config_service.get_numbering_rule_for_executor(executor_id)

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

        # Фильтруем по исполнителю
        query = query.filter(OutboxJournal.executor == executor_name)

        # Получаем максимальный номер
        max_no = query.scalar()
        next_number = (max_no or (start_number - 1)) + 1

        # Форматируем номер согласно правилу (например, 42-10)
        formatted_number = number_format.format(
            number=next_number,
            executor_code=executor_code
        )

        # 4. Получаем текущую дату в формате ДД.ММ.ГГГГ
        today = date.today()
        outgoing_date = docx_service.format_date(today)

        # 5. Проверяем, что выбранный файл - DOCX
        if not request.selected_file_name.lower().endswith('.docx'):
            raise HTTPException(
                status_code=400,
                detail=f"Выбранный файл '{request.selected_file_name}' не является DOCX документом. Регистрировать можно только DOCX файлы с полями для заполнения."
            )

        # 6. Находим выбранный файл в карточке
        card_files = card.get('files', [])
        selected_file = None
        for file_info in card_files:
            if file_info.get('name') == request.selected_file_name:
                selected_file = file_info
                break

        if not selected_file:
            raise HTTPException(
                status_code=404,
                detail=f"Файл '{request.selected_file_name}' не найден в карточке"
            )

        # 8. Скачиваем DOCX (в mock режиме используем mock данные)
        if file_service.use_mock:
            # В mock режиме создаем простой DOCX с плейсхолдерами
            print(f"[Mock] Creating mock DOCX with placeholders for file: {request.selected_file_name}")
            docx_bytes = _create_mock_docx()
        else:
            # Скачиваем реальный файл из Kaiten
            docx_url = selected_file.get('url') or selected_file.get('path')
            if not docx_url:
                raise HTTPException(
                    status_code=404,
                    detail=f"URL файла '{request.selected_file_name}' не найден"
                )
            docx_bytes = await docx_service.download_docx_from_url(docx_url)

        # 9. Проверяем наличие плейсхолдеров
        has_placeholders = docx_service.check_has_placeholders(docx_bytes)
        if not has_placeholders:
            raise HTTPException(
                status_code=400,
                detail=f"Файл '{request.selected_file_name}' не содержит полей для заполнения ({{{{outgoing_no}}}}, {{{{outgoing_date}}}}, {{{{stamp}}}}). Регистрировать можно только шаблоны с полями."
            )

        # 10. Заменяем плейсхолдеры (пока без данных сертификата)
        modified_docx = docx_service.replace_placeholders(
            docx_bytes,
            formatted_number,
            outgoing_date,
            certificate_data=None  # Сначала создаем без подписи
        )

        # 11. Конвертируем DOCX в PDF
        print(f"[Outbox] Converting DOCX to PDF...")
        try:
            pdf_bytes = pdf_service.convert_docx_to_pdf(modified_docx)
            print(f"[Outbox] PDF created: {len(pdf_bytes)} bytes")
        except Exception as e:
            print(f"[Outbox] PDF conversion error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка конвертации в PDF: {str(e)}"
            )

        # 12. Подписываем PDF через КриптоПро
        print(f"[Outbox] Signing PDF with CryptoPro...")
        try:
            signature_bytes, cert_info = cryptopro_service.sign_pdf(pdf_bytes)
            print(f"[Outbox] PDF signed: {len(signature_bytes)} bytes signature")
        except Exception as e:
            print(f"[Outbox] Signing error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка подписания: {str(e)}"
            )

        # 13. Обновляем DOCX с данными сертификата (для визуализации штампа ЭЦП)
        modified_docx_with_stamp = docx_service.replace_placeholders(
            docx_bytes,
            formatted_number,
            outgoing_date,
            certificate_data=cert_info
        )

        # 14. Сохраняем файлы во временное хранилище
        file_id = str(uuid.uuid4())
        # Формируем имя файла: номер_дата_оригинальное_имя
        safe_number = formatted_number.replace('/', '_').replace('\\', '_').replace('-', '_')
        safe_date = outgoing_date.replace('.', '_')
        base_name = request.selected_file_name.rsplit('.', 1)[0]  # без расширения

        # Сохраняем DOCX с штампом
        docx_filename = f"{safe_number}_{safe_date}_{base_name}.docx"
        docx_file_path = TEMP_FILES_DIR / f"{file_id}_{docx_filename}"
        with open(docx_file_path, 'wb') as f:
            f.write(modified_docx_with_stamp)

        # Сохраняем PDF
        pdf_filename = f"{safe_number}_{safe_date}_{base_name}.pdf"
        pdf_file_path = TEMP_FILES_DIR / f"{file_id}_{pdf_filename}"
        with open(pdf_file_path, 'wb') as f:
            f.write(pdf_bytes)

        # Сохраняем подпись
        sig_filename = f"{safe_number}_{safe_date}_{base_name}.pdf.sig"
        sig_file_path = TEMP_FILES_DIR / f"{file_id}_{sig_filename}"
        with open(sig_file_path, 'wb') as f:
            f.write(signature_bytes)

        print(f"[Outbox] Files saved:")
        print(f"  - DOCX: {docx_file_path}")
        print(f"  - PDF: {pdf_file_path}")
        print(f"  - SIG: {sig_file_path}")

        # URL для скачивания подписанного PDF
        download_url = f"/api/outbox/download/{file_id}_{pdf_filename}"

        return RegisterResponse(
            outgoing_no=next_number,
            formatted_number=formatted_number,
            outgoing_date=outgoing_date,
            executor=executor_name,
            executor_id=executor_id,
            docx_preview_url=download_url,
            message=f"Документ зарегистрирован. Номер: {formatted_number} от {outgoing_date}"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error preparing registration: {e}")
        raise HTTPException(status_code=500, detail=f"Error preparing registration: {str(e)}")


def _create_mock_docx() -> bytes:
    """Создать mock DOCX файл с плейсхолдерами для тестирования"""
    from docx import Document

    doc = Document()
    doc.add_heading('Исходящее письмо', 0)

    doc.add_paragraph(f'Исх. № {{{{outgoing_no}}}} от {{{{outgoing_date}}}}')
    doc.add_paragraph('')
    doc.add_paragraph('Уважаемые коллеги,')
    doc.add_paragraph('')
    doc.add_paragraph('Направляем Вам информацию по запросу.')
    doc.add_paragraph('')
    doc.add_paragraph('С уважением,')
    doc.add_paragraph('{{stamp}}')

    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    return output.read()


class ClientSignatureUpload(BaseModel):
    """Схема для приёма подписи, созданной на клиенте"""
    file_id: str  # ID временного файла
    signature: str  # Base64 подпись
    thumbprint: str  # Отпечаток сертификата
    cn: str  # Common Name владельца сертификата


@router.post("/upload-client-signature")
async def upload_client_signature(
    data: ClientSignatureUpload,
    current_user: dict = Depends(get_current_user)
):
    """
    Принять подпись, созданную на клиенте (через браузер с КриптоПро)

    Args:
        data: Данные подписи
        current_user: Текущий пользователь

    Returns:
        Результат сохранения подписи
    """
    try:
        # Декодируем подпись из Base64
        try:
            sig_bytes = base64.b64decode(data.signature)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Неверный формат подписи Base64: {str(e)}"
            )

        # Проверяем, что файл существует
        # Ищем файлы с этим file_id
        matching_files = list(TEMP_FILES_DIR.glob(f"{data.file_id}_*.pdf"))
        if not matching_files:
            raise HTTPException(
                status_code=404,
                detail=f"PDF файл с ID {data.file_id} не найден"
            )

        pdf_file_path = matching_files[0]

        # Создаём .sig файл рядом с PDF
        sig_file_path = pdf_file_path.with_suffix('.pdf.sig')
        sig_file_path.write_bytes(sig_bytes)

        # Логируем информацию о подписи
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"""
=== Подпись получена от клиента ===
Время: {timestamp}
Владелец сертификата: {data.cn}
Отпечаток: {data.thumbprint}
PDF файл: {pdf_file_path.name}
Размер PDF: {pdf_file_path.stat().st_size} байт
Размер подписи: {len(sig_bytes)} байт
========================
"""
        print(log_entry)

        # Сохраняем в лог-файл
        log_path = TEMP_FILES_DIR / "signatures.log"
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
        except Exception as e:
            print(f"[Outbox] Warning: Could not write to log file: {e}")

        return {
            "success": True,
            "message": "Подпись успешно сохранена",
            "pdf_file": pdf_file_path.name,
            "sig_file": sig_file_path.name,
            "timestamp": timestamp,
            "certificate": {
                "cn": data.cn,
                "thumbprint": data.thumbprint
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[Outbox] Error uploading client signature: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка сохранения подписи: {str(e)}"
        )


@router.get("/download/{filename}")
async def download_file(filename: str):
    """
    Скачать файл из временного хранилища

    Args:
        filename: Имя файла для скачивания

    Returns:
        Файл для скачивания
    """
    # Защита от path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Неверное имя файла")

    file_path = TEMP_FILES_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")

    # Определяем MIME тип
    if filename.endswith('.pdf'):
        media_type = "application/pdf"
    elif filename.endswith('.sig'):
        media_type = "application/octet-stream"
    elif filename.endswith('.docx'):
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:
        media_type = "application/octet-stream"

    return FileResponse(
        file_path,
        media_type=media_type,
        filename=filename
    )


@router.get("/status/{file_id}")
async def get_file_status(file_id: str):
    """
    Получить статус файлов (PDF, DOCX, SIG) по file_id

    Args:
        file_id: ID файла

    Returns:
        Информация о существующих файлах
    """
    pdf_files = list(TEMP_FILES_DIR.glob(f"{file_id}_*.pdf"))
    docx_files = list(TEMP_FILES_DIR.glob(f"{file_id}_*.docx"))
    sig_files = list(TEMP_FILES_DIR.glob(f"{file_id}_*.pdf.sig"))

    result = {
        "file_id": file_id,
        "pdf_exists": len(pdf_files) > 0,
        "docx_exists": len(docx_files) > 0,
        "sig_exists": len(sig_files) > 0,
    }

    if pdf_files:
        pdf_path = pdf_files[0]
        result["pdf_file"] = pdf_path.name
        result["pdf_size"] = pdf_path.stat().st_size

    if docx_files:
        docx_path = docx_files[0]
        result["docx_file"] = docx_path.name
        result["docx_size"] = docx_path.stat().st_size

    if sig_files:
        sig_path = sig_files[0]
        result["sig_file"] = sig_path.name
        result["sig_size"] = sig_path.stat().st_size

    return result
