import base64
import hashlib
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel

from app.api.auth import get_current_user
from app.core.config import settings
from app.services.file_service import file_service
from app.services.kaiten_service import kaiten_service

router = APIRouter(prefix="/api/approval", tags=["approval"])


class ApprovalSignatureRequest(BaseModel):
    card_id: int
    file_name: str
    signature: str
    thumbprint: str
    cn: str


def _signature_name(file_name: str, digest: str) -> str:
    safe_name = Path(file_name).name
    return f"СОГЛАСОВАНО_{digest[:12]}_{safe_name}.sig"


async def _get_document(card_id: int, file_name: str, current_user: dict):
    if current_user.get("role") not in {"director", "head"}:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    if not file_name.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Для согласования выберите DOCX")

    card = await kaiten_service.get_card_by_id(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Карточка не найдена")
    if current_user.get("role") == "head" and card.get("column_id") != settings.KAITEN_COLUMN_HEAD_REVIEW_ID:
        raise HTTPException(status_code=409, detail="Карточка уже не находится на согласовании начальника отдела")
    if current_user.get("role") == "head" and not await kaiten_service.is_responsible(
        card_id, current_user["username"], card.get("members")
    ):
        raise HTTPException(status_code=403, detail="Карточка назначена другому начальнику отдела")
    document = next(
        (item for item in card.get("files", []) if not item.get("deleted") and item.get("name") == file_name),
        None,
    )
    if not document:
        raise HTTPException(status_code=404, detail="Выбранный DOCX не найден в карточке")
    url = document.get("url") or document.get("path")
    if not url:
        raise HTTPException(status_code=404, detail="У DOCX отсутствует ссылка для скачивания")
    content = await file_service.download_file(url)
    return card, document, content


@router.get("/document/{card_id}")
async def download_document(
    card_id: int,
    file_name: str = Query(...),
    current_user: dict = Depends(get_current_user),
):
    _, _, content = await _get_document(card_id, file_name, current_user)
    encoded_name = quote(Path(file_name).name)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"},
    )


@router.get("/status/{card_id}")
async def approval_status(
    card_id: int,
    file_name: str = Query(...),
    current_user: dict = Depends(get_current_user),
):
    card, _, content = await _get_document(card_id, file_name, current_user)
    digest = hashlib.sha256(content).hexdigest()
    expected_name = _signature_name(file_name, digest)
    files = [item for item in card.get("files", []) if not item.get("deleted")]
    signature = next((item for item in files if item.get("name") == expected_name), None)
    stale = any(
        (item.get("name") or "").startswith("СОГЛАСОВАНО_")
        and (item.get("name") or "").endswith(f"_{Path(file_name).name}.sig")
        for item in files
    )
    return {
        "signed": signature is not None,
        "stale": signature is None and stale,
        "signature_name": signature.get("name") if signature else None,
        "document_sha256": digest,
    }


@router.post("/sign")
async def sign_and_forward(
    data: ApprovalSignatureRequest,
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "head":
        raise HTTPException(status_code=403, detail="Согласовывать документ может только начальник отдела")

    card, _, content = await _get_document(data.card_id, data.file_name, current_user)
    digest = hashlib.sha256(content).hexdigest()
    signature_name = _signature_name(data.file_name, digest)
    existing = next(
        (item for item in card.get("files", []) if not item.get("deleted") and item.get("name") == signature_name),
        None,
    )

    if not existing:
        try:
            compact_signature = "".join(data.signature.split())
            signature_bytes = base64.b64decode(compact_signature, validate=True)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Некорректный формат электронной подписи") from exc
        if not signature_bytes:
            raise HTTPException(status_code=400, detail="Получена пустая электронная подпись")
        uploaded = await kaiten_service.upload_card_file(data.card_id, signature_name, signature_bytes)
        if not uploaded:
            raise HTTPException(status_code=502, detail="Не удалось загрузить подпись в Kaiten")

        comment = (
            f"Документ согласован электронной подписью. Файл: {data.file_name}. "
            f"Подписант: {data.cn}. Отпечаток: {data.thumbprint}. SHA-256: {digest}."
        )
        await kaiten_service.add_comment(data.card_id, comment)

    moved = await kaiten_service.move_card(
        data.card_id,
        "На подпись",
        f"Документ согласован начальником отдела {data.cn}",
    )
    if not moved:
        raise HTTPException(
            status_code=502,
            detail="Подпись загружена, но карточку не удалось переместить в колонку «На подпись»",
        )

    return {"status": "success", "signature_name": signature_name, "document_sha256": digest}

@router.get("/signature/{card_id}")
async def download_signature(
    card_id: int,
    file_name: str = Query(...),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "director":
        raise HTTPException(status_code=403, detail="Проверять согласующую подпись может только директор")
    if not file_name.startswith("СОГЛАСОВАНО_") or not file_name.endswith(".docx.sig"):
        raise HTTPException(status_code=400, detail="Недопустимое имя подписи")
    card = await kaiten_service.get_card_by_id(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Карточка не найдена")
    signature = next(
        (item for item in card.get("files", []) if not item.get("deleted") and item.get("name") == file_name),
        None,
    )
    if not signature:
        raise HTTPException(status_code=404, detail="Подпись не найдена")
    url = signature.get("url") or signature.get("path")
    if not url:
        raise HTTPException(status_code=404, detail="У подписи отсутствует ссылка для скачивания")
    content = await file_service.download_file(url)
    return Response(content=content, media_type="application/pkcs7-signature")
