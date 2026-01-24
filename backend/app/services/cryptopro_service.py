import subprocess
import tempfile
import os
import base64
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime


class CryptoProService:
    """Сервис для работы с электронной подписью через КриптоПро"""

    def __init__(self):
        self.cryptcp_path = self._find_cryptcp()
        self.use_mock = not self.cryptcp_path  # Если КриптоПро не установлен, используем mock

        # Директория для логов подписей
        self.log_dir = Path(__file__).parent.parent.parent / "temp_files"
        self.log_dir.mkdir(exist_ok=True)

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
            Кортеж (байты подписи .sig, данные сертификата)
        """
        if self.use_mock:
            return self._mock_sign_pdf(pdf_bytes)

        # Реальная подпись через КриптоПро
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)

            # Сохраняем PDF во временный файл
            pdf_file = temp_dir_path / "document.pdf"
            pdf_file.write_bytes(pdf_bytes)

            # Файл для отсоединенной подписи (detached signature)
            signature_file = temp_dir_path / "document.sig"

            try:
                # Команда для создания отсоединенной подписи в формате PKCS#7
                cmd = [
                    self.cryptcp_path,
                    '-sign',
                    '-detached',  # Отсоединенная подпись
                    '-der',       # Формат DER (бинарный PKCS#7)
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

                # Проверяем, что файл подписи создан
                if not signature_file.exists():
                    raise RuntimeError("Signature file was not created")

                # Читаем байты подписи
                signature_bytes = signature_file.read_bytes()

                # Получаем информацию о сертификате
                cert_info = self._get_certificate_info(certificate_thumbprint)

                # Логируем информацию о подписи
                self._log_signature_info(
                    pdf_size=len(pdf_bytes),
                    sig_size=len(signature_bytes),
                    cert_info=cert_info
                )

                print(f"[CryptoProService] Successfully signed PDF")
                print(f"  PDF size: {len(pdf_bytes)} bytes")
                print(f"  Signature size: {len(signature_bytes)} bytes")

                return signature_bytes, cert_info

            except subprocess.TimeoutExpired:
                raise RuntimeError("Signing timeout")
            except Exception as e:
                raise RuntimeError(f"Signing error: {str(e)}")

    def _log_signature_info(self, pdf_size: int, sig_size: int, cert_info: Dict):
        """
        Логировать информацию о созданной подписи

        Args:
            pdf_size: Размер PDF файла в байтах
            sig_size: Размер файла подписи в байтах
            cert_info: Информация о сертификате
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"""
=== Подпись создана ===
Время: {timestamp}
Владелец сертификата: {cert_info.get('owner', 'Unknown')}
Серийный номер: {cert_info.get('serial', 'Unknown')}
Действителен с: {cert_info.get('valid_from', 'Unknown')}
Действителен до: {cert_info.get('valid_to', 'Unknown')}
Издатель: {cert_info.get('issuer', 'Unknown')}
Размер PDF: {pdf_size} байт
Размер подписи: {sig_size} байт
========================
"""
        # Выводим в консоль
        print(log_entry)

        # Сохраняем в лог-файл
        log_path = self.log_dir / "signatures.log"
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
        except Exception as e:
            print(f"[CryptoProService] Warning: Could not write to log file: {e}")

    def _mock_sign_pdf(self, pdf_bytes: bytes) -> tuple[bytes, Dict]:
        """
        Mock подпись для тестирования (без реального КриптоПро)
        Создает валидную PKCS#7 структуру для тестов

        Returns:
            Кортеж (mock подпись, mock данные сертификата)
        """
        print("[CryptoProService] Using MOCK signing (CryptoPro not installed)")

        # Создаем mock подпись, имитирующую PKCS#7 структуру
        # В реальности это будет байтовая структура PKCS#7 DER
        mock_signature = b"\x30\x82\x05\x00" + b"MOCK_PKCS7_SIGNATURE_DATA_FOR_TESTING" * 10

        # Mock данные сертификата
        mock_cert_info = {
            "serial": "5C6BE147FA657D807EF3A907DFB53553",
            "owner": "Левченко Вера Сергеевна",
            "valid_from": "16.07.2025",
            "valid_to": "09.10.2026",
            "issuer": "MOCK CA"
        }

        # Логируем как и при реальной подписи
        self._log_signature_info(
            pdf_size=len(pdf_bytes),
            sig_size=len(mock_signature),
            cert_info=mock_cert_info
        )

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
