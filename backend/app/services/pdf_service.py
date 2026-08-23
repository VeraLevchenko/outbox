import io
import subprocess
import tempfile
import shutil
import os
from pathlib import Path
from typing import Optional
import pymupdf


class PdfService:
    """Сервис для конвертации DOCX в PDF"""

    def __init__(self):
        self.libreoffice_path = self._find_libreoffice()
        if self.libreoffice_path:
            print(f"[PdfService] LibreOffice found at: {self.libreoffice_path}")
        else:
            print("[PdfService] WARNING: LibreOffice not found!")

    def _find_libreoffice(self) -> Optional[str]:
        """Найти путь к LibreOffice"""
        # Возможные пути к LibreOffice
        possible_paths = [
            '/usr/bin/libreoffice',
            '/usr/bin/soffice',
            '/Applications/LibreOffice.app/Contents/MacOS/soffice',  # macOS
            'C:\\Program Files\\LibreOffice\\program\\soffice.exe',  # Windows
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # Попробуем найти через which
        try:
            result = subprocess.run(['which', 'libreoffice'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass

        return None

    def convert_docx_to_pdf(self, docx_bytes: bytes) -> bytes:
        """
        Конвертировать DOCX в PDF используя LibreOffice

        Args:
            docx_bytes: Содержимое DOCX файла

        Returns:
            Содержимое PDF файла

        Raises:
            RuntimeError: Если LibreOffice не установлен или конвертация не удалась
        """
        if not self.libreoffice_path:
            raise RuntimeError(
                "LibreOffice не установлен. "
                "Установите LibreOffice: apt-get install -y libreoffice-writer libreoffice-common"
            )

        # Создаем временную директорию для файлов
        temp_dir = tempfile.mkdtemp(prefix='libreoffice_')
        try:
            temp_dir_path = Path(temp_dir)

            # Сохраняем DOCX во временный файл
            docx_file = temp_dir_path / "document.docx"
            with open(docx_file, 'wb') as f:
                f.write(docx_bytes)

            # Конвертируем в PDF используя LibreOffice headless
            print(f"[PdfService] Starting conversion with: {self.libreoffice_path}")
            print(f"[PdfService] Input DOCX size: {len(docx_bytes)} bytes")
            print(f"[PdfService] Temp directory: {temp_dir_path}")

            # Создаем директорию для профиля LibreOffice
            profile_dir = temp_dir_path / ".libreoffice_profile"
            profile_dir.mkdir(exist_ok=True)

            # Окружение для работы в headless режиме БЕЗ Java
            env = os.environ.copy()
            env.update({
                'SAL_USE_VCLPLUGIN': 'svp',  # Headless plugin
            })
            # Удаляем все Java-related переменные
            for key in list(env.keys()):
                if 'JAVA' in key.upper():
                    del env[key]

            result = subprocess.run(
                [
                    self.libreoffice_path,
                    '--headless',
                    '--invisible',
                    '--nocrashreport',
                    '--nodefault',
                    '--nofirststartwizard',
                    '--nolockcheck',
                    '--nologo',
                    '--norestore',
                    '-env:UserInstallation=file://' + str(profile_dir.absolute()),  # Используем отдельный профиль
                    '--convert-to', 'pdf',
                    '--outdir', str(temp_dir_path),
                    str(docx_file)
                ],
                capture_output=True,
                text=True,
                timeout=120,
                env=env
            )

            print(f"[PdfService] LibreOffice exit code: {result.returncode}")
            if result.stdout:
                print(f"[PdfService] LibreOffice stdout: {result.stdout}")
            if result.stderr:
                print(f"[PdfService] LibreOffice stderr: {result.stderr}")

            if result.returncode != 0:
                raise RuntimeError(f"LibreOffice conversion failed: {result.stderr}")

            # Читаем созданный PDF
            pdf_file = temp_dir_path / "document.pdf"
            if not pdf_file.exists():
                # Пытаемся найти PDF файл с другим именем
                pdf_files = list(temp_dir_path.glob("*.pdf"))
                if pdf_files:
                    pdf_file = pdf_files[0]
                    print(f"[PdfService] Found PDF: {pdf_file.name}")
                else:
                    raise RuntimeError(f"PDF file was not created. Files in temp dir: {list(temp_dir_path.glob('*'))}")

            with open(pdf_file, 'rb') as f:
                pdf_bytes = f.read()

            print(f"[PdfService] Successfully converted DOCX to PDF ({len(pdf_bytes)} bytes)")
            return pdf_bytes

        except subprocess.TimeoutExpired:
            print(f"[PdfService] ERROR: Conversion timeout after 120 seconds")
            raise RuntimeError("PDF conversion timeout after 120 seconds")
        except Exception as e:
            print(f"[PdfService] ERROR: {type(e).__name__}: {str(e)}")
            raise RuntimeError(f"PDF conversion error: {str(e)}")
        finally:
            # Очищаем временную директорию
            try:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                print(f"[PdfService] Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                print(f"[PdfService] Warning: Failed to clean up temp directory: {e}")


    def fill_pdf_placeholders(self, pdf_bytes: bytes, outgoing_no: str, outgoing_date: str, username: str = "default") -> bytes:
        """Заменить текстовые маркеры в готовом PDF и добавить визуальную отметку ЭП."""
        stamp_data = {
            "gabidulina": ("6DADC5852C426780DD13A83271D7D582", "Габидулина Рада Ришатовна", "02.12.2025", "25.02.2027"),
            "mezentseva": ("F3E16AEEEF42503B17051E597BDF345EFB901DE1", "Мезенцева Дарья Витальевна", "06.08.2025", "30.10.2026"),
            "default": ("5C6BE147FA657D807EF3A907DFB53553", "Левченко Вера Сергеевна", "16.07.2025", "09.10.2026"),
        }
        serial, owner, valid_from, valid_to = stamp_data.get(username, stamp_data["default"])
        values = {"{{outgoing_no}}": outgoing_no, "{{outgoing_date}}": outgoing_date}
        document = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        found = {}

        for marker in (*values.keys(), "{{stamp}}"):
            matches = []
            for page_number, page in enumerate(document):
                matches.extend((page_number, rect) for rect in page.search_for(marker))
            if len(matches) == 0 or len(matches) > 1:
                document.close()
                raise ValueError(f"Маркер {marker} должен встречаться в PDF ровно один раз; найдено: {len(matches)}")
            found[marker] = matches[0]

        for marker, (page_number, rect) in found.items():
            page = document[page_number]
            page.add_redact_annot(rect + (-1, -1, 1, 1), fill=(1, 1, 1))
        for page in document:
            page.apply_redactions()

        font_file = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        for marker, value in values.items():
            page_number, rect = found[marker]
            page = document[page_number]
            page.insert_font(fontname="OutboxFont", fontfile=font_file)
            page.insert_text((rect.x0, rect.y1 - 1), value, fontname="OutboxFont", fontsize=9, color=(0, 0, 0))

        page_number, marker_rect = found["{{stamp}}"]
        page = document[page_number]
        page.insert_font(fontname="OutboxFont", fontfile=font_file)
        stamp_rect = pymupdf.Rect(
            max(36, marker_rect.x0 - 95),
            max(36, marker_rect.y0 - 5),
            min(page.rect.width - 36, marker_rect.x1 + 100),
            min(page.rect.height - 36, marker_rect.y0 + 72),
        )
        page.draw_rect(stamp_rect, color=(0.1, 0.35, 0.65), width=0.8, overlay=True)
        stamp_text = (
            "ДОКУМЕНТ ПОДПИСАН ЭЛЕКТРОННОЙ ПОДПИСЬЮ\n"
            f"Сертификат {serial}\n"
            f"Владелец {owner}\n"
            f"Действителен с {valid_from} по {valid_to}"
        )
        result = page.insert_textbox(
            stamp_rect + (4, 4, -4, -4), stamp_text,
            fontname="OutboxFont", fontsize=6.5, color=(0.1, 0.25, 0.5),
            align=pymupdf.TEXT_ALIGN_CENTER, overlay=True,
        )
        if result < 0:
            document.close()
            raise ValueError("Отметка электронной подписи не помещается в зарезервированную область")

        output = io.BytesIO()
        document.save(output, garbage=4, deflate=True)
        document.close()
        return output.getvalue()


# Singleton instance
pdf_service = PdfService()
