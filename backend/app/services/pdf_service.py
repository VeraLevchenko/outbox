import subprocess
import tempfile
import os
from pathlib import Path
from typing import Optional


class PdfService:
    """Сервис для конвертации DOCX в PDF"""

    def __init__(self):
        self.libreoffice_path = self._find_libreoffice()

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
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)

            # Сохраняем DOCX во временный файл
            docx_file = temp_dir_path / "document.docx"
            with open(docx_file, 'wb') as f:
                f.write(docx_bytes)

            # Конвертируем в PDF используя LibreOffice headless
            try:
                result = subprocess.run(
                    [
                        self.libreoffice_path,
                        '--headless',
                        '--convert-to', 'pdf',
                        '--outdir', str(temp_dir_path),
                        str(docx_file)
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode != 0:
                    raise RuntimeError(f"LibreOffice conversion failed: {result.stderr}")

                # Читаем созданный PDF
                pdf_file = temp_dir_path / "document.pdf"
                if not pdf_file.exists():
                    raise RuntimeError("PDF file was not created")

                with open(pdf_file, 'rb') as f:
                    pdf_bytes = f.read()

                print(f"[PdfService] Successfully converted DOCX to PDF ({len(pdf_bytes)} bytes)")
                return pdf_bytes

            except subprocess.TimeoutExpired:
                raise RuntimeError("PDF conversion timeout")
            except Exception as e:
                raise RuntimeError(f"PDF conversion error: {str(e)}")


# Singleton instance
pdf_service = PdfService()
