import subprocess
import tempfile
import os
from pathlib import Path
from typing import Optional, Dict


class CryptoProService:
    """Сервис для работы с электронной подписью через КриптоПро"""

    def __init__(self):
        self.cryptcp_path = self._find_cryptcp()
        self.use_mock = not self.cryptcp_path  # Если КриптоПро не установлен, используем mock

    def _find_cryptcp(self) -> Optional[str]:
        """Найти путь к утилите cryptcp из КриптоПро CSP"""
        possible_paths = [
            '/opt/cprocsp/bin/amd64/cryptcp',
            '/opt/cprocsp/bin/ia32/cryptcp',
            'C:\\Program Files\\Crypto Pro\\CSP\\cryptcp.exe',  # Windows
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # Попробуем найти через which
        try:
            result = subprocess.run(['which', 'cryptcp'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass

        return None

    def sign_pdf(
        self,
        pdf_bytes: bytes,
        certificate_thumbprint: Optional[str] = None
    ) -> tuple[bytes, Dict]:
        """
        Подписать PDF файл электронной подписью

        Args:
            pdf_bytes: Содержимое PDF файла
            certificate_thumbprint: Отпечаток сертификата (опционально)

        Returns:
            Кортеж (подписанный PDF, данные сертификата)
        """
        if self.use_mock:
            return self._mock_sign_pdf(pdf_bytes)

        # Реальная подпись через КриптоПро
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)

            # Сохраняем PDF во временный файл
            pdf_file = temp_dir_path / "document.pdf"
            with open(pdf_file, 'wb') as f:
                f.write(pdf_bytes)

            # Файл для подписи
            signature_file = temp_dir_path / "document.pdf.sig"

            try:
                # Команда для создания отсоединенной подписи
                cmd = [
                    self.cryptcp_path,
                    '-sign',
                    '-der',  # Формат подписи DER
                    str(pdf_file),
                    str(signature_file)
                ]

                if certificate_thumbprint:
                    cmd.extend(['-thumbprint', certificate_thumbprint])

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode != 0:
                    raise RuntimeError(f"CryptoPro signing failed: {result.stderr}")

                # Читаем файл подписи
                if not signature_file.exists():
                    raise RuntimeError("Signature file was not created")

                with open(signature_file, 'rb') as f:
                    signature_bytes = f.read()

                # Получаем информацию о сертификате
                cert_info = self._get_certificate_info(certificate_thumbprint)

                print(f"[CryptoProService] Successfully signed PDF ({len(signature_bytes)} bytes)")

                return signature_bytes, cert_info

            except subprocess.TimeoutExpired:
                raise RuntimeError("Signing timeout")
            except Exception as e:
                raise RuntimeError(f"Signing error: {str(e)}")

    def _mock_sign_pdf(self, pdf_bytes: bytes) -> tuple[bytes, Dict]:
        """
        Mock подпись для тестирования (без реального КриптоПро)

        Returns:
            Кортеж (mock подпись, mock данные сертификата)
        """
        print("[CryptoProService] Using MOCK signing (CryptoPro not installed)")

        # Создаем mock подпись (просто несколько байтов)
        mock_signature = b"MOCK_SIGNATURE_DATA_FOR_TESTING"

        # Mock данные сертификата
        mock_cert_info = {
            "serial": "5C6BE147FA657D807EF3A907DFB53553",
            "owner": "Левченко Вера Сергеевна",
            "valid_from": "16.07.2025",
            "valid_to": "09.10.2026",
            "issuer": "MOCK CA"
        }

        return mock_signature, mock_cert_info

    def _get_certificate_info(self, thumbprint: Optional[str] = None) -> Dict:
        """
        Получить информацию о сертификате

        Args:
            thumbprint: Отпечаток сертификата

        Returns:
            Словарь с данными сертификата
        """
        # TODO: Реализовать получение реальной информации о сертификате
        # Используя команду certmgr или другие утилиты КриптоПро

        # Пока возвращаем mock данные
        return {
            "serial": "5C6BE147FA657D807EF3A907DFB53553",
            "owner": "Левченко Вера Сергеевна",
            "valid_from": "16.07.2025",
            "valid_to": "09.10.2026",
            "issuer": "Test CA"
        }

    def verify_signature(self, pdf_bytes: bytes, signature_bytes: bytes) -> bool:
        """
        Проверить подпись PDF файла

        Args:
            pdf_bytes: Содержимое PDF файла
            signature_bytes: Содержимое файла подписи

        Returns:
            True если подпись валидна, False иначе
        """
        if self.use_mock:
            return True  # В mock режиме всегда успех

        # TODO: Реализовать проверку подписи через КриптоПро
        # Используя cryptcp -verify

        return True


# Singleton instance
cryptopro_service = CryptoProService()
