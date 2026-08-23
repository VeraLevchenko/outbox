import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.api.auth import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])
CREDENTIALS_FILE = Path(__file__).parent.parent.parent / "user_credentials.json"
ADMIN_USERNAME = "levchenko"


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("username") != ADMIN_USERNAME:
        raise HTTPException(status_code=403, detail="Раздел доступен только администратору")
    return current_user


@router.get("/credentials")
async def get_credentials(_: dict = Depends(require_admin)):
    if not CREDENTIALS_FILE.exists():
        raise HTTPException(status_code=404, detail="Файл учётных записей не найден")
    return json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))


@router.get("/credentials/download")
async def download_credentials(_: dict = Depends(require_admin)):
    if not CREDENTIALS_FILE.exists():
        raise HTTPException(status_code=404, detail="Файл учётных записей не найден")
    return FileResponse(
        CREDENTIALS_FILE,
        media_type="application/json",
        filename="uchetnye_zapisi_outbox.json",
    )
