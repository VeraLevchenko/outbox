import os
from typing import List, Dict, Optional
from pathlib import Path
from app.core.config import settings


class FileService:
    """Сервис для работы с файлами входящих и исходящих документов"""

    def __init__(self):
        self.incoming_path = Path(settings.INCOMING_FILES_PATH)
        self.outgoing_path = Path(settings.OUTGOING_FILES_PATH)
        self.use_mock = settings.DEBUG

    def _get_mock_incoming_files(self, incoming_no: str) -> List[Dict]:
        """Генерировать mock-данные для входящих файлов"""
        return [
            {
                "name": f"входящее_письмо_{incoming_no}.pdf",
                "path": f"/mnt/doc/Входящие/{incoming_no}/входящее_письмо_{incoming_no}.pdf",
                "size": 245680,
                "type": "application/pdf",
                "is_main": True
            },
            {
                "name": "приложение_1_схема.pdf",
                "path": f"/mnt/doc/Входящие/{incoming_no}/приложение_1_схема.pdf",
                "size": 1024000,
                "type": "application/pdf",
                "is_main": False
            },
            {
                "name": "приложение_2_расчеты.xlsx",
                "path": f"/mnt/doc/Входящие/{incoming_no}/приложение_2_расчеты.xlsx",
                "size": 45120,
                "type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "is_main": False
            }
        ]

    def _get_mock_outgoing_files(self, card_id: int) -> Dict:
        """Генерировать mock-данные для исходящих файлов"""
        # Данные зависят от card_id
        if card_id == 1001:
            return {
                "main_docx": {
                    "name": "исх_письмо_минфин.docx",
                    "path": "/kaiten/files/исх_письмо_минфин.docx",
                    "size": 89600,
                    "type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "is_main": True
                },
                "attachments": [
                    {
                        "name": "приложение_1.pdf",
                        "path": "/kaiten/files/приложение_1.pdf",
                        "size": 456000,
                        "type": "application/pdf",
                        "is_main": False
                    }
                ]
            }
        elif card_id == 1002:
            return {
                "main_docx": {
                    "name": "исх_договор.docx",
                    "path": "/kaiten/files/исх_договор.docx",
                    "size": 125440,
                    "type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "is_main": True
                },
                "attachments": []
            }
        else:
            return {
                "main_docx": {
                    "name": "исх_отчет.docx",
                    "path": "/kaiten/files/исх_отчет.docx",
                    "size": 67890,
                    "type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "is_main": True
                },
                "attachments": []
            }

    def get_incoming_files(self, incoming_no: str) -> List[Dict]:
        """
        Получить список входящих файлов

        Args:
            incoming_no: Номер входящего документа

        Returns:
            Список файлов с метаданными
        """
        if self.use_mock:
            print(f"[Mock] Returning mock incoming files for {incoming_no}")
            return self._get_mock_incoming_files(incoming_no)

        # Реальная логика работы с файловой системой
        folder_path = self.incoming_path / incoming_no
        if not folder_path.exists():
            return []

        files = []
        for file_path in folder_path.iterdir():
            if file_path.is_file():
                files.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "size": file_path.stat().st_size,
                    "type": self._get_mime_type(file_path.suffix),
                    "is_main": False  # Определяется логикой приложения
                })

        return files

    def get_outgoing_files(self, card_id: int, card_files: List[Dict]) -> Dict:
        """
        Получить исходящие файлы из карточки Kaiten

        Args:
            card_id: ID карточки
            card_files: Список файлов из карточки Kaiten

        Returns:
            Словарь с главным DOCX и приложениями
        """
        if self.use_mock:
            print(f"[Mock] Returning mock outgoing files for card {card_id}")
            return self._get_mock_outgoing_files(card_id)

        # Реальная логика работы с файлами Kaiten
        main_docx = None
        attachments = []

        for file_info in card_files:
            file_name = file_info.get("name", "")

            # Главный DOCX начинается с "исх_"
            if file_name.startswith("исх_") and file_name.endswith(".docx"):
                main_docx = {
                    "name": file_name,
                    "path": file_info.get("url", ""),
                    "size": file_info.get("size", 0),
                    "type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "is_main": True
                }
            else:
                attachments.append({
                    "name": file_name,
                    "path": file_info.get("url", ""),
                    "size": file_info.get("size", 0),
                    "type": self._get_mime_type(Path(file_name).suffix),
                    "is_main": False
                })

        return {
            "main_docx": main_docx,
            "attachments": attachments
        }

    def get_google_viewer_url(self, file_url: str) -> str:
        """
        Получить URL для просмотра файла через Google Viewer

        Args:
            file_url: URL файла

        Returns:
            URL для Google Viewer
        """
        # Google Docs Viewer URL
        return f"https://docs.google.com/viewer?url={file_url}&embedded=true"

    def _get_mime_type(self, extension: str) -> str:
        """Определить MIME тип по расширению файла"""
        mime_types = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xls": "application/vnd.ms-excel",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
        }
        return mime_types.get(extension.lower(), "application/octet-stream")


# Singleton instance
file_service = FileService()
