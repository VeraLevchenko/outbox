import os
import io
import httpx
from pathlib import Path
from datetime import date
from typing import Optional, Dict
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from app.core.config import settings


class DocxService:
    """Сервис для работы с DOCX документами"""

    def __init__(self):
        self.static_path = Path(__file__).parent.parent / "static"
        self.stamp_image_path = self.static_path / "stamp.png"

    async def download_docx_from_url(self, url: str) -> bytes:
        """
        Скачать DOCX файл по URL

        Args:
            url: URL файла

        Returns:
            Содержимое файла в виде байтов
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            return response.content

    def check_has_placeholders(self, docx_bytes: bytes) -> bool:
        """
        Проверить, есть ли в документе плейсхолдеры для заполнения

        Args:
            docx_bytes: Содержимое DOCX файла

        Returns:
            True если найдены плейсхолдеры, False если нет
        """
        import zipfile as _zipfile

        placeholders = ('{{outgoing_no}}', '{{outgoing_date}}', '{{stamp}}')

        # Первичная проверка — прямо по XML содержимому файла (надёжнее python-docx)
        try:
            with _zipfile.ZipFile(io.BytesIO(docx_bytes)) as z:
                with z.open('word/document.xml') as f:
                    xml_text = f.read().decode('utf-8', errors='ignore')
            if any(ph in xml_text for ph in placeholders):
                return True
        except Exception as e:
            print(f"Error checking placeholders via XML: {e}")

        # Запасная проверка через python-docx с защитой от ошибок парсинга
        try:
            doc = Document(io.BytesIO(docx_bytes))

            for paragraph in doc.paragraphs:
                try:
                    if any(ph in paragraph.text for ph in placeholders):
                        return True
                except Exception:
                    continue

            for table in doc.tables:
                try:
                    for row in table.rows:
                        try:
                            for cell in row.cells:
                                try:
                                    for paragraph in cell.paragraphs:
                                        try:
                                            if any(ph in paragraph.text for ph in placeholders):
                                                return True
                                        except Exception:
                                            continue
                                except Exception:
                                    continue
                        except Exception:
                            continue
                except Exception:
                    continue

        except Exception as e:
            print(f"Error checking placeholders via docx: {e}")

        return False

    def replace_placeholders(
        self,
        docx_bytes: bytes,
        outgoing_no: str,
        outgoing_date: str,
        certificate_data: Optional[Dict] = None
    ) -> bytes:
        """
        Заменить плейсхолдеры в DOCX документе

        Args:
            docx_bytes: Содержимое DOCX файла
            outgoing_no: Исходящий номер (например, "42-10")
            outgoing_date: Дата в формате ДД.ММ.ГГГГ (например, "20.01.2026")
            certificate_data: Данные сертификата для визуализации ЭЦП

        Returns:
            Измененный DOCX файл в виде байтов
        """
        # Загружаем документ из байтов
        doc = Document(io.BytesIO(docx_bytes))

        # Заменяем текстовые плейсхолдеры в параграфах
        for paragraph in doc.paragraphs:
            if '{{outgoing_no}}' in paragraph.text:
                paragraph.text = paragraph.text.replace('{{outgoing_no}}', outgoing_no)
            if '{{outgoing_date}}' in paragraph.text:
                paragraph.text = paragraph.text.replace('{{outgoing_date}}', outgoing_date)

            # Заменяем {{stamp}} на изображение визуализации ЭЦП
            if '{{stamp}}' in paragraph.text:
                # Очищаем текст параграфа
                paragraph.text = ''
                # Вставляем визуализацию ЭЦП
                self._insert_stamp_visualization(paragraph, certificate_data)

        # Заменяем плейсхолдеры в таблицах
        for table in doc.tables:
            try:
                for row in table.rows:
                    try:
                        for cell in row.cells:
                            try:
                                for paragraph in cell.paragraphs:
                                    try:
                                        if '{{outgoing_no}}' in paragraph.text:
                                            paragraph.text = paragraph.text.replace('{{outgoing_no}}', outgoing_no)
                                        if '{{outgoing_date}}' in paragraph.text:
                                            paragraph.text = paragraph.text.replace('{{outgoing_date}}', outgoing_date)
                                        if '{{stamp}}' in paragraph.text:
                                            paragraph.text = ''
                                            self._insert_stamp_visualization(paragraph, certificate_data)
                                    except Exception:
                                        continue
                            except Exception:
                                continue
                    except Exception:
                        continue
            except Exception:
                continue

        # Сохраняем измененный документ в байты
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        return output.read()

    def _insert_stamp_visualization(self, paragraph, certificate_data: Optional[Dict] = None):
        """
        Вставить визуализацию электронной подписи в параграф

        Args:
            paragraph: Параграф документа
            certificate_data: Данные сертификата
        """
        # Если есть готовое изображение штампа, используем его
        if self.stamp_image_path.exists():
            try:
                run = paragraph.add_run()
                run.add_picture(str(self.stamp_image_path), width=Inches(2.5))
                return
            except Exception as e:
                print(f"Error adding stamp image: {e}")

        # Если изображения нет, создаем текстовую визуализацию в рамке
        # Используем данные из certificate_data или mock данные

        USER_STAMP_DATA = {
            'gabidulina': {
                'serial': '6DADC5852C426780DD13A83271D7D582',
                'owner': 'Габидулина Рада Ришатовна',
                'valid_from': '02.12.2025',
                'valid_to': '25.02.2027',
            },
            'mezentseva': {
                'serial': 'F3E16AEEEF42503B17051E597BDF345EFB901DE1',
                'owner': 'Мезенцева Дарья Витальевна',
                'valid_from': '06.08.2025',
                'valid_to': '30.10.2026',
            },
            'default': {
                'serial': '5C6BE147FA657D807EF3A907DFB53553',
                'owner': 'Левченко Вера Сергеевна',
                'valid_from': '16.07.2025',
                'valid_to': '09.10.2026',
            }
        }
        username = certificate_data.get('username', 'default') if certificate_data else 'default'
        stamp = USER_STAMP_DATA.get(username, USER_STAMP_DATA['default'])
        cert_serial = certificate_data.get('serial', stamp['serial']) if certificate_data else stamp['serial']
        cert_owner = certificate_data.get('owner', stamp['owner']) if certificate_data else stamp['owner']
        cert_valid_from = certificate_data.get('valid_from', stamp['valid_from']) if certificate_data else stamp['valid_from']
        cert_valid_to = certificate_data.get('valid_to', stamp['valid_to']) if certificate_data else stamp['valid_to']

        # Добавляем текстовую визуализацию
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Заголовок
        run = paragraph.add_run('ДОКУМЕНТ ПОДПИСАН ЭЛЕКТРОННОЙ ПОДПИСЬЮ\n')
        run.bold = True
        run.font.size = Pt(10)

        # Данные сертификата
        run = paragraph.add_run(f'Сертификат {cert_serial}\n')
        run.font.size = Pt(8)

        run = paragraph.add_run(f'Владелец {cert_owner}\n')
        run.font.size = Pt(8)

        run = paragraph.add_run(f'Действителен с {cert_valid_from} по {cert_valid_to}')
        run.font.size = Pt(8)

    def format_date(self, date_obj: date) -> str:
        """
        Форматировать дату в формат ДД.ММ.ГГГГ

        Args:
            date_obj: Объект даты

        Returns:
            Строка с датой в формате ДД.ММ.ГГГГ
        """
        return date_obj.strftime('%d.%m.%Y')


# Singleton instance
docx_service = DocxService()
