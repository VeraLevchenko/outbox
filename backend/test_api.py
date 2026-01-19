"""
Простой скрипт для тестирования API
"""
import asyncio
import httpx


async def test_api():
    """Тестирование основных endpoints"""
    base_url = "http://localhost:8000"

    async with httpx.AsyncClient() as client:
        print("=" * 50)
        print("Testing Outbox API")
        print("=" * 50)

        # Тест 1: Health check
        print("\n1. Testing health endpoint...")
        try:
            response = await client.get(f"{base_url}/health")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")
        except Exception as e:
            print(f"   Error: {e}")

        # Тест 2: Root endpoint
        print("\n2. Testing root endpoint...")
        try:
            response = await client.get(f"{base_url}/")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")
        except Exception as e:
            print(f"   Error: {e}")

        # Тест 3: Get cards for director
        print("\n3. Testing GET /api/kaiten/cards (director)...")
        try:
            response = await client.get(f"{base_url}/api/kaiten/cards?role=director")
            print(f"   Status: {response.status_code}")
            cards = response.json()
            print(f"   Found {len(cards)} cards")
            if cards:
                print(f"   First card: {cards[0].get('title')}")
        except Exception as e:
            print(f"   Error: {e}")

        # Тест 4: Get cards for head
        print("\n4. Testing GET /api/kaiten/cards (head)...")
        try:
            response = await client.get(f"{base_url}/api/kaiten/cards?role=head")
            print(f"   Status: {response.status_code}")
            cards = response.json()
            print(f"   Found {len(cards)} cards")
            if cards:
                print(f"   First card: {cards[0].get('title')}")
        except Exception as e:
            print(f"   Error: {e}")

        print("\n" + "=" * 50)
        print("Testing completed!")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_api())
