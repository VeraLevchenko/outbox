import base64
import json
import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.api.auth import get_current_user
from app.api.outbox import (
    ClientSignatureUpload,
    SIGNING_JOBS_DIR,
    TEMP_FILES_DIR,
    _job_path,
    _process_client_signature,
    _read_job,
    _write_job,
)
from app.models.database import SessionLocal
from app.models.outbox_journal import OutboxJournal
from app.services.kaiten_service import kaiten_service

router = APIRouter(prefix="/api/outbox", tags=["outbox"])


async def run_signing_job(job_id: str):
    job = _read_job(job_id)
    if job.get("status") == "success":
        return
    job.update(status="processing", updated_at=datetime.now().isoformat())
    _write_job(job_id, job)
    db = SessionLocal()
    try:
        data = ClientSignatureUpload(**job["data"])
        existing = db.query(OutboxJournal).filter(
            OutboxJournal.formatted_number == data.formatted_number
        ).first()
        result = (
            {"journal_entry_id": existing.id, "folder_path": existing.folder_path}
            if existing
            else await _process_client_signature(data, db, job["user"])
        )
        moved = await kaiten_service.move_card(
            data.card_id,
            "Отправка",
            "Документ подписан и сохранён",
            data.formatted_number,
            datetime.strptime(data.outgoing_date, "%d.%m.%Y").strftime("%Y-%m-%d"),
        )
        if not moved:
            raise RuntimeError("Карточку не удалось переместить в колонку «Отправка»")
        job.update(status="success", result=result, updated_at=datetime.now().isoformat())
    except Exception as exc:
        db.rollback()
        job.update(status="error", error=str(exc), updated_at=datetime.now().isoformat())
    finally:
        db.close()
        _write_job(job_id, job)


@router.post("/upload-client-signature")
async def enqueue_client_signature(
    data: ClientSignatureUpload,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") not in {"director", "acting_chairman"}:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    try:
        compact_signature = "".join(data.signature.split())
        if not base64.b64decode(compact_signature, validate=True):
            raise ValueError
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Некорректная электронная подпись") from exc
    if not list(TEMP_FILES_DIR.glob(f"{data.file_id}_*.pdf")):
        raise HTTPException(status_code=404, detail="Подписываемый PDF не найден")

    job_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    _write_job(job_id, {
        "id": job_id,
        "status": "pending",
        "created_at": now,
        "updated_at": now,
        "data": data.dict(),
        "user": current_user,
    })
    background_tasks.add_task(run_signing_job, job_id)
    return {"accepted": True, "job_id": job_id, "status": "pending"}


@router.get("/signing-jobs/{job_id}")
async def signing_job_status(job_id: str, current_user: dict = Depends(get_current_user)):
    job = _read_job(job_id)
    data = job.get("data", {})
    return {
        "id": job_id,
        "status": job.get("status"),
        "formatted_number": data.get("formatted_number"),
        "error": job.get("error"),
        "result": job.get("result"),
        "updated_at": job.get("updated_at"),
    }


async def resume_pending_signing_jobs():
    for path in SIGNING_JOBS_DIR.glob("*.json"):
        try:
            job = json.loads(path.read_text(encoding="utf-8"))
            if job.get("status") in {"pending", "processing"}:
                await run_signing_job(job["id"])
        except Exception as exc:
            print(f"[Outbox] Failed to resume signing job {path.name}: {exc}")
