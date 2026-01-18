# Outbox Backend

Backend приложение для работы с исходящей корреспонденцией.

## Технологии

- **Python 3.10+**
- **FastAPI** - веб-фреймворк
- **PostgreSQL** - база данных
- **SQLAlchemy** - ORM
- **httpx** - HTTP клиент для Kaiten API

## Установка и запуск

### 1. Установить зависимости

```bash
pip install -r requirements.txt
```

### 2. Настроить переменные окружения

Скопировать `.env.example` в `.env` в корне проекта и заполнить:

```bash
cp ../.env.example ../.env
```

Отредактировать `.env` файл:
- `KAITEN_API_URL` - URL вашего Kaiten API
- `KAITEN_API_TOKEN` - токен для доступа к Kaiten API
- `SECRET_KEY` - секретный ключ для JWT

### 3. Запустить PostgreSQL

```bash
cd ..
docker-compose up -d
```

### 4. Инициализировать базу данных

```bash
python init_db.py
```

### 5. Запустить приложение

```bash
./run.sh
# или
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API будет доступен по адресу: http://localhost:8000

Документация API (Swagger): http://localhost:8000/docs

## Структура

```
backend/
├── app/
│   ├── api/              # API endpoints
│   │   └── kaiten.py     # Endpoints для работы с Kaiten
│   ├── core/             # Конфигурация
│   │   └── config.py     # Настройки приложения
│   ├── models/           # Модели БД
│   │   ├── database.py   # Подключение к БД
│   │   ├── user.py       # Модель пользователя
│   │   └── outbox_journal.py  # Модель журнала
│   ├── services/         # Бизнес-логика
│   │   └── kaiten_service.py  # Сервис для Kaiten API
│   └── main.py           # Основное приложение
├── init_db.py            # Скрипт инициализации БД
├── requirements.txt      # Python зависимости
└── run.sh               # Скрипт запуска
```

## API Endpoints

### Kaiten

- `GET /api/kaiten/cards?role=director` - Получить карточки для роли
- `POST /api/kaiten/cards/{card_id}/move` - Переместить карточку

### Служебные

- `GET /` - Информация о приложении
- `GET /health` - Проверка состояния
