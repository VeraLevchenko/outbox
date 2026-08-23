import subprocess
import tempfile
import shutil
import os
from pathlib import Path
from typing import Optional


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


# Singleton instance
pdf_service = PdfService()
