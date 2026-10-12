"""Письма из папки проектов, доступные без подключения к Kaiten."""

import base64
import binascii
import hashlib
import io
import json
import mimetypes
import re
import shutil
import uuid
import zipfile
from datetime import date, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from docx import Document

from app.api.auth import get_current_user
from app.api.outbox import TEMP_FILES_DIR, get_db
from app.core.config import settings
from app.models.outbox_journal import OutboxJournal
from app.services.docx_service import docx_service
from app.services.pdf_service import pdf_service

router = APIRouter(prefix="/api/server-projects", tags=["server-projects"])
NUMBER_PATTERN = re.compile(r"^[0-9]+-[0-9]+$")


class PrepareRequest(BaseModel):
    folder: str
    selected_file_name: str
    to_whom: str
    executor: str
    content: str = ""
    skip_head_approval: bool = False


class SignRequest(BaseModel):
    file_id: uuid.UUID
    signature: str
    thumbprint: str = ""
    cn: str = ""


def _require_director(user: dict) -> None:
    if user.get("role") not in {"director", "acting_chairman"}:
        raise HTTPException(status_code=403, detail="Подписывать исходящие письма может только руководитель")


def _source_root() -> Path:
    configured = settings.PROJECTS_OUTGOING_FILES_PATH
    return Path(configured) if configured else Path(settings.OUTGOING_FILES_PATH).parent / "Проекты_исходящие"


def _project(folder: str) -> Path:
    if not NUMBER_PATTERN.fullmatch(folder):
        raise HTTPException(status_code=400, detail="Имя папки должно быть исходящим номером вида 2331-10")
    path = _source_root() / folder
    if path.is_symlink() or not path.is_dir():
        raise HTTPException(status_code=404, detail="Папка проекта не найдена")
    return path


def _files(project: Path) -> list[Path]:
    try:
        children = sorted(project.iterdir(), key=lambda item: item.name.lower())
        if any(item.is_symlink() for item in children):
            raise HTTPException(status_code=400, detail="В папке проекта есть недопустимая ссылка на файл")
        if any(not item.is_file() for item in children):
            raise HTTPException(status_code=400, detail="В папке проекта допускаются только файлы")
        return children
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Не удалось прочитать папку проекта: {exc}") from exc


def _file(project: Path, filename: str) -> Path:
    if not filename or filename in {".", ".."} or Path(filename).name != filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Недопустимое имя файла")
    path = project / filename
    if path.is_symlink() or not path.is_file():
        raise HTTPException(status_code=404, detail="Файл проекта не найден")
    return path


def _check_duplicate(db: Session, number: str) -> None:
    if db.query(OutboxJournal.id).filter(OutboxJournal.formatted_number == number).first():
        raise HTTPException(status_code=409, detail=f"Исходящий номер {number} уже есть в журнале")


def _has_number_placeholder(content: bytes) -> bool:
    try:
        document = Document(io.BytesIO(content))
        if any("{{outgoing_no}}" in paragraph.text for paragraph in document.paragraphs):
            return True
        return any(
            "{{outgoing_no}}" in paragraph.text
            for table in document.tables for row in table.rows
            for cell in row.cells for paragraph in cell.paragraphs
        )
    except Exception:
        return False


@router.get("")
def list_projects(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    _require_director(user)
    root = _source_root()
    if not root.is_dir():
        raise HTTPException(status_code=503, detail=f"Папка проектов недоступна: {root}")
    try:
        registered = {row[0] for row in db.query(OutboxJournal.formatted_number).all()}
        folders = sorted(root.iterdir(), key=lambda item: item.name.lower())
        return [
            {"name": item.name, "error": None if NUMBER_PATTERN.fullmatch(item.name) else "Имя папки должно иметь вид 2331-10"}
            for item in folders
            if item.is_dir() and not item.is_symlink()
            and not item.name.lower().endswith(" подписано")
            and item.name not in registered
        ]
    except OSError as exc:
        raise HTTPException(status_code=503, detail=f"Не удалось прочитать папку проектов: {exc}") from exc


@router.get("/{folder}/files")
def list_files(folder: str, user: dict = Depends(get_current_user)):
    _require_director(user)
    project = _project(folder)
    return [
        {"name": path.name, "size": path.stat().st_size, "is_docx": path.suffix.lower() == ".docx"}
        for path in _files(project)
    ]


@router.get("/{folder}/files/{filename}")
def get_file(folder: str, filename: str, user: dict = Depends(get_current_user)):
    _require_director(user)
    path = _file(_project(folder), filename)
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return FileResponse(path, media_type=media_type, filename=path.name)


@router.get("/{folder}/preview/{filename}")
def preview_docx(folder: str, filename: str, user: dict = Depends(get_current_user)):
    _require_director(user)
    path = _file(_project(folder), filename)
    if path.suffix.lower() != ".docx":
        raise HTTPException(status_code=400, detail="Предпросмотр доступен только для DOCX")
    try:
        return Response(pdf_service.convert_docx_to_pdf(path.read_bytes()), media_type="application/pdf")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Не удалось открыть Word документ: {exc}") from exc


@router.get("/{folder}/approval/{filename}")
def approval_status(folder: str, filename: str, user: dict = Depends(get_current_user)):
    _require_director(user)
    project = _project(folder)
    source = _file(project, filename)
    if source.suffix.lower() != ".docx":
        raise HTTPException(status_code=400, detail="Для проверки согласования выберите DOCX")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    expected = f"СОГЛАСОВАНО_{digest[:12]}_{source.name}.sig"
    names = {path.name for path in _files(project)}
    stale = any(name.startswith("СОГЛАСОВАНО_") and name.endswith(f"_{source.name}.sig") for name in names)
    return {"signed": expected in names, "stale": expected not in names and stale, "signature_name": expected if expected in names else None}


@router.post("/prepare")
def prepare_project(
    request: PrepareRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    _require_director(user)
    project = _project(request.folder)
    _check_duplicate(db, request.folder)
    to_whom = request.to_whom.strip()
    executor = request.executor.strip()
    if not to_whom or not executor:
        raise HTTPException(status_code=400, detail="Укажите адресата и исполнителя")
    source = _file(project, request.selected_file_name)
    if source.suffix.lower() != ".docx":
        raise HTTPException(status_code=400, detail="Для подписи выберите DOCX")
    source_bytes = source.read_bytes()
    if not docx_service.check_has_placeholders(source_bytes) or not _has_number_placeholder(source_bytes):
        raise HTTPException(status_code=400, detail="В DOCX нет поля {{outgoing_no}} для исходящего номера")
    approval_name = f"СОГЛАСОВАНО_{hashlib.sha256(source_bytes).hexdigest()[:12]}_{source.name}.sig"
    has_approval = any(path.name == approval_name for path in _files(project))
    if not has_approval and not request.skip_head_approval:
        raise HTTPException(status_code=400, detail="Для этой версии DOCX нет подписи согласования")

    outgoing_date = docx_service.format_date(date.today())
    try:
        prepared_docx = docx_service.replace_placeholders(
            source_bytes, request.folder, outgoing_date,
            certificate_data={"username": user.get("username", "default")},
        )
        pdf_bytes = pdf_service.convert_docx_to_pdf(prepared_docx)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Не удалось подготовить документ: {exc}") from exc

    file_id = str(uuid.uuid4())
    stem = f"{request.folder.replace('-', '_')}_{outgoing_date.replace('.', '_')}"
    pdf_filename = f"{file_id}_{stem}.pdf"
    docx_filename = f"{file_id}_{stem}.docx"
    metadata = {
        "folder": request.folder,
        "source_name": source.name,
        "source_hash": hashlib.sha256(source_bytes).hexdigest(),
        "to_whom": to_whom,
        "executor": executor,
        "content": request.content.strip()[:500],
        "approval_name": approval_name if has_approval and not request.skip_head_approval else None,
        "outgoing_date": outgoing_date,
        "pdf_filename": pdf_filename,
        "docx_filename": docx_filename,
        "username": user.get("username"),
    }
    TEMP_FILES_DIR.mkdir(parents=True, exist_ok=True)
    (TEMP_FILES_DIR / pdf_filename).write_bytes(pdf_bytes)
    (TEMP_FILES_DIR / docx_filename).write_bytes(prepared_docx)
    (TEMP_FILES_DIR / f"{file_id}.server.json").write_text(json.dumps(metadata, ensure_ascii=False), encoding="utf-8")
    return {
        "file_id": file_id,
        "outgoing_no": int(request.folder.split("-", 1)[0]),
        "formatted_number": request.folder,
        "outgoing_date": outgoing_date,
        "executor": executor,
        "docx_preview_url": f"/api/outbox/download/{pdf_filename}",
    }


@router.post("/sign")
def sign_project(
    request: SignRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    _require_director(user)
    file_id = str(request.file_id)
    metadata_path = TEMP_FILES_DIR / f"{file_id}.server.json"
    if not metadata_path.is_file():
        raise HTTPException(status_code=404, detail="Подготовленный документ не найден")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata["username"] != user.get("username"):
        raise HTTPException(status_code=403, detail="Документ подготовлен другим пользователем")
    project = _project(metadata["folder"])
    _check_duplicate(db, metadata["folder"])
    source = _file(project, metadata["source_name"])
    if hashlib.sha256(source.read_bytes()).hexdigest() != metadata["source_hash"]:
        raise HTTPException(status_code=409, detail="DOCX изменился после подготовки. Подготовьте его повторно")
    try:
        signature = base64.b64decode("".join(request.signature.split()), validate=True)
        if not signature:
            raise ValueError("empty signature")
    except (ValueError, binascii.Error) as exc:
        raise HTTPException(status_code=400, detail="Некорректная электронная подпись") from exc

    pdf_path = TEMP_FILES_DIR / metadata["pdf_filename"]
    docx_path = TEMP_FILES_DIR / metadata["docx_filename"]
    if not pdf_path.is_file() or not docx_path.is_file():
        raise HTTPException(status_code=404, detail="Подготовленные PDF и Word не найдены")
    pdf_bytes = pdf_path.read_bytes()
    docx_bytes = docx_path.read_bytes()
    attachments = [
        (path.name, path.read_bytes()) for path in _files(project)
        if path.name != source.name
        and (not (path.name.startswith("СОГЛАСОВАНО_") and path.name.endswith(".docx.sig"))
             or path.name == metadata.get("approval_name"))
    ]
    pdf_name = metadata["pdf_filename"].replace(f"{file_id}_", "", 1)
    docx_name = metadata["docx_filename"].replace(f"{file_id}_", "", 1)
    output_names = {pdf_name, docx_name, f"{pdf_name}.sig"}
    if any(name in output_names for name, _ in attachments):
        raise HTTPException(status_code=409, detail="Имя приложения совпадает с именем подписанного документа")
    archive = None
    if attachments:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for name, content in attachments:
                zip_file.writestr(name, content)
        archive = buffer.getvalue()

    output_root = Path(settings.OUTGOING_FILES_PATH)
    output_root.mkdir(parents=True, exist_ok=True)
    output_folder = output_root / metadata["folder"]
    if output_folder.exists():
        raise HTTPException(status_code=409, detail=f"Папка исходящего номера {metadata['folder']} уже существует")
    staging = output_root / f".{metadata['folder']}.{file_id}.pending"
    staging.mkdir(exist_ok=False)
    published = False
    try:
        (staging / pdf_name).write_bytes(pdf_bytes)
        (staging / docx_name).write_bytes(docx_bytes)
        (staging / f"{pdf_name}.sig").write_bytes(signature)
        for name, content in attachments:
            (staging / name).write_bytes(content)
        staging.rename(output_folder)
        published = True
        number = metadata["folder"]
        journal_entry = OutboxJournal(
            outgoing_no=int(number.split("-", 1)[0]),
            formatted_number=number,
            outgoing_date=datetime.strptime(metadata["outgoing_date"], "%d.%m.%Y").date(),
            to_whom=metadata["to_whom"],
            executor=metadata["executor"],
            content=metadata["content"] or None,
            kaiten_card_url=None,
            file_blob=pdf_bytes,
            sig_blob=signature,
            attachments_blob=archive,
            folder_path=str(output_folder),
        )
        db.add(journal_entry)
        db.commit()
    except Exception as exc:
        db.rollback()
        shutil.rmtree(output_folder if published else staging, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Не удалось сохранить подпись и журнал: {exc}") from exc

    signed_path = project.with_name(f"{project.name} подписано")
    warning = None
    try:
        if signed_path.exists():
            raise FileExistsError(f"Папка {signed_path.name} уже существует")
        project.rename(signed_path)
    except OSError as exc:
        warning = f"Документ подписан и записан в журнал, но папку проекта не удалось переименовать: {exc}"
    try:
        metadata_path.unlink(missing_ok=True)
    except OSError:
        pass
    return {"success": True, "formatted_number": metadata["folder"], "warning": warning}
