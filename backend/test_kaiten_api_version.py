#!/usr/bin/env python3
"""
Скрипт для определения правильной версии Kaiten API

Использование:
    python test_kaiten_api_version.py
"""

import asyncio
import httpx
import os
import sys

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

KAITEN_DOMAIN = os.getenv("KAITEN_API_URL", "").split("/api")[0]
KAITEN_TOKEN = os.getenv("KAITEN_API_TOKEN", "")

print("=" * 70)
print("ТЕСТИРОВАНИЕ ВЕРСИЙ KAITEN API")
print("=" * 70)
print()

if not KAITEN_DOMAIN or not KAITEN_TOKEN:
    print("❌ Не найдены KAITEN_API_URL или KAITEN_API_TOKEN в .env файле")
    sys.exit(1)

print(f"Домен: {KAITEN_DOMAIN}")
print(f"Токен: {'*' * 20}{KAITEN_TOKEN[-4:] if len(KAITEN_TOKEN) > 4 else '****'}")
print()

# Версии API для тестирования
api_versions = [
    "/api/latest",
    "/api/v1",
    "/api",
]

# Эндпоинты для тестирования
test_endpoints = [
    "/boards",
    "/cards",
    "/spaces",
    "/current-user"
]

headers = {
    "Authorization": f"Bearer {KAITEN_TOKEN}",
    "Content-Type": "application/json"
}


async def test_endpoint(client: httpx.AsyncClient, url: str, method: str = "GET"):
    """Тестирует эндпоинт"""
    try:
        if method == "GET":
            response = await client.get(url, headers=headers, timeout=10.0)
        else:
            response = await client.request(method, url, headers=headers, timeout=10.0)

        return response.status_code, response.text[:200] if response.text else ""
    except httpx.TimeoutException:
        return None, "Timeout"
    except httpx.ConnectError:
        return None, "Connection Error"
    except Exception as e:
        return None, str(e)


async def main():
    async with httpx.AsyncClient() as client:
        print("Тестирование версий API и эндпоинтов:")
        print("-" * 70)
        print()

        working_endpoints = []

        for api_version in api_versions:
            print(f"Тестирование {api_version}:")

            for endpoint in test_endpoints:
                url = f"{KAITEN_DOMAIN}{api_version}{endpoint}"
                status, response = await test_endpoint(client, url)

                status_symbol = "✓" if status == 200 else "✗"
                status_text = f"{status}" if status else "ERROR"

                print(f"  {status_symbol} GET {endpoint}: {status_text}")

                if status == 200:
                    working_endpoints.append((api_version, endpoint, url))
                elif status == 405:
                    print(f"      (405 Method Not Allowed - возможно нужен другой метод)")
                elif status == 401:
                    print(f"      (401 Unauthorized - проверьте токен)")
                elif status == 403:
                    print(f"      (403 Forbidden - недостаточно прав)")

            print()

        print("=" * 70)
        print("РЕЗУЛЬТАТЫ:")
        print("=" * 70)
        print()

        if working_endpoints:
            print("✓ Найдены работающие эндпоинты:")
            print()
            for api_ver, endpoint, full_url in working_endpoints:
                print(f"  {api_ver}{endpoint}")
                print(f"    Полный URL: {full_url}")
            print()
            print("Рекомендация для .env:")
            best_api = working_endpoints[0][0]
            print(f"  KAITEN_API_URL={KAITEN_DOMAIN}{best_api}")
        else:
            print("❌ Не найдено ни одного работающего эндпоинта")
            print()
            print("Возможные причины:")
            print("  - Неправильный токен")
            print("  - Недостаточно прав у токена")
            print("  - Неправильный домен")
            print("  - API Kaiten временно недоступен")

        print()

        # Дополнительный тест: попробуем получить текущего пользователя
        print("Дополнительный тест: GET /current-user")
        for api_version in api_versions:
            url = f"{KAITEN_DOMAIN}{api_version}/current-user"
            status, response = await test_endpoint(client, url)
            if status == 200:
                print(f"  ✓ {api_version}/current-user работает!")
                print(f"    Response preview: {response[:100]}...")
                break

        print()
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
