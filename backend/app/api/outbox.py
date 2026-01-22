from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import date
import io

from app.models.database import SessionLocal
from app.schemas.outbox_schemas import RegisterRequest, RegisterResponse
from app.services.kaiten_service import kaiten_service
from app.services.file_service import file_service
from app.services.docx_service import docx_service
from app.services.config_service import config_service
from app.api.auth import get_current_user
from app.api.journal import get_next_outgoing_number

router = APIRouter(prefix="/api/outbox", tags=["outbox"])


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
    - Получить исполнителя из карточки Kaiten
    - Сгенерировать номер
    - Заменить плейсхолдеры в DOCX
    - Вернуть информацию для предпросмотра

    Args:
        request: Данные запроса (card_id, to_whom)
        db: Сессия БД
        current_user: Текущий пользователь

    Returns:
        Данные регистрации с номером и датой
    """
    try:
        # 1. Получаем исполнителя из карточки Kaiten
        executor_data = await kaiten_service.get_executor_from_card(request.card_id)

        if not executor_data:
            raise HTTPException(
                status_code=404,
                detail="Executor not found in card. Please ensure card has a member with type=2"
            )

        executor_id = executor_data.get('user_id')
        executor_name = executor_data.get('full_name')

        # 2. Генерируем следующий номер
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

        # 3. Получаем текущую дату в формате ДД.ММ.ГГГГ
        today = date.today()
        outgoing_date = docx_service.format_date(today)

        # 4. Получаем главный DOCX файл из карточки
        card = await kaiten_service.get_card_by_id(request.card_id)
        if not card:
            raise HTTPException(status_code=404, detail=f"Card {request.card_id} not found")

        card_files = card.get('files', [])
        files_data = file_service.get_outgoing_files(request.card_id, card_files)
        main_docx = files_data.get('main_docx')

        if not main_docx:
            raise HTTPException(
                status_code=404,
                detail="Main DOCX file not found. File name must start with 'исх_'"
            )

        # 5. Скачиваем DOCX (в mock режиме используем mock данные)
        if file_service.use_mock:
            # В mock режиме создаем простой DOCX с плейсхолдерами
            print(f"[Mock] Creating mock DOCX with placeholders")
            docx_bytes = _create_mock_docx()
        else:
            # Скачиваем реальный файл из Kaiten
            docx_url = main_docx.get('path')
            docx_bytes = await docx_service.download_docx_from_url(docx_url)

        # 6. Заменяем плейсхолдеры
        modified_docx = docx_service.replace_placeholders(
            docx_bytes,
            formatted_number,
            outgoing_date,
            certificate_data=None  # TODO: получить данные сертификата из CryptoPro
        )

        # TODO: Сохранить modified_docx во временное хранилище для последующего использования
        # Пока возвращаем только информацию

        return RegisterResponse(
            outgoing_no=next_number,
            formatted_number=formatted_number,
            outgoing_date=outgoing_date,
            executor=executor_name,
            executor_id=executor_id,
            docx_preview_url=None,  # TODO: добавить URL для предпросмотра
            message=f"Документ готов к регистрации. Номер: {formatted_number} от {outgoing_date}"
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
