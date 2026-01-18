from pydantic import BaseModel
from typing import List, Optional


class FileInfo(BaseModel):
    """Информация о файле"""
    name: str
    path: str
    size: int
    type: str
    is_main: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "name": "document.pdf",
                "path": "/path/to/document.pdf",
                "size": 1024000,
                "type": "application/pdf",
                "is_main": True
            }
        }


class IncomingFilesResponse(BaseModel):
    """Ответ со списком входящих файлов"""
    incoming_no: str
    files: List[FileInfo]
    total_files: int

    class Config:
        json_schema_extra = {
            "example": {
                "incoming_no": "12345",
                "files": [
                    {
                        "name": "входящее_письмо.pdf",
                        "path": "/mnt/doc/Входящие/12345/входящее_письмо.pdf",
                        "size": 245680,
                        "type": "application/pdf",
                        "is_main": True
                    }
                ],
                "total_files": 1
            }
        }


class OutgoingFilesResponse(BaseModel):
    """Ответ с исходящими файлами"""
    card_id: int
    main_docx: Optional[FileInfo] = None
    attachments: List[FileInfo] = []
    total_files: int

    class Config:
        json_schema_extra = {
            "example": {
                "card_id": 1001,
                "main_docx": {
                    "name": "исх_письмо.docx",
                    "path": "/kaiten/files/исх_письмо.docx",
                    "size": 89600,
                    "type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "is_main": True
                },
                "attachments": [],
                "total_files": 1
            }
        }


class GoogleViewerRequest(BaseModel):
    """Запрос на получение URL для Google Viewer"""
    file_url: str

    class Config:
        json_schema_extra = {
            "example": {
                "file_url": "https://example.com/document.pdf"
            }
        }


class GoogleViewerResponse(BaseModel):
    """Ответ с URL для Google Viewer"""
    viewer_url: str
    original_url: str

    class Config:
        json_schema_extra = {
            "example": {
                "viewer_url": "https://docs.google.com/viewer?url=https://example.com/document.pdf&embedded=true",
                "original_url": "https://example.com/document.pdf"
            }
        }
