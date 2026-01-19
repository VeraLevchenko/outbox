# Инструкция по тестированию Outbox

## Вариант 1: Быстрый тест (без сервера)

Этот вариант проверяет работу mock-данных и основной логики без запуска полного сервера.

```bash
# 1. Склонировать репозиторий
git clone https://github.com/VeraLevchenko/outbox.git
cd outbox
git checkout claude/setup-dev-environment-IYuJy

# 2. Установить Python зависимости
pip install -r backend/requirements.txt

# 3. Запустить быстрый тест (из корня проекта outbox)
python3 test_quick.py
```

**Важно:** Запускайте `test_quick.py` из корня проекта `outbox/`, не из папки `backend/`.

```

**Что тестируется:**
- ✓ Mock-данные для роли director (2 карточки)
- ✓ Mock-данные для роли head (1 карточка)
- ✓ Сервис работы с Kaiten API

---

## Вариант 2: Полное тестирование (с сервером и БД)

### Требования:
- Python 3.10+
- Docker и Docker Compose
- Git

### Пошаговая инструкция:

#### Шаг 1: Клонирование репозитория

```bash
git clone https://github.com/VeraLevchenko/outbox.git
cd outbox
git checkout claude/setup-dev-environment-IYuJy
```

#### Шаг 2: Создание файла окружения

Файл `.env` уже создан в репозитории, но вы можете его отредактировать:

```bash
# Просмотреть текущие настройки
cat .env

# Отредактировать (опционально)
nano .env  # или любой текстовый редактор
```

**Важные переменные:**
- `KAITEN_API_URL` - URL вашего Kaiten API (пока используется mock)
- `KAITEN_API_TOKEN` - токен для Kaiten (пока используется mock)
- `DEBUG=True` - включает mock-данные
- `KAITEN_POLL_INTERVAL=5` - интервал polling в секундах

#### Шаг 3: Запуск PostgreSQL

```bash
# Запустить PostgreSQL в Docker
docker-compose up -d

# Проверить что контейнер запустился
docker-compose ps
```

Вы должны увидеть:
```
NAME                IMAGE                COMMAND                  SERVICE      CREATED         STATUS         PORTS
outbox_postgres     postgres:15-alpine   "docker-entrypoint.s…"   postgres     X seconds ago   Up X seconds   0.0.0.0:5432->5432/tcp
```

#### Шаг 4: Установка Python зависимостей

```bash
cd backend

# Рекомендуется использовать виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt
```

#### Шаг 5: Инициализация базы данных

```bash
python init_db.py
```

Вы должны увидеть:
```
Creating database tables...
Database tables created successfully!
```

#### Шаг 6: Запуск приложения

```bash
# Вариант A: Через скрипт
./run.sh

# Вариант B: Напрямую через uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

При успешном запуске вы увидите:
```
[Startup] Starting background polling tasks...
[Startup] Background tasks started
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### Шаг 7: Тестирование API

**В новом терминале:**

```bash
cd backend
python test_api.py
```

Или вручную через curl:

```bash
# Health check
curl http://localhost:8000/health

# Информация о приложении
curl http://localhost:8000/

# Получить карточки для director
curl "http://localhost:8000/api/kaiten/cards?role=director"

# Получить карточки для head
curl "http://localhost:8000/api/kaiten/cards?role=head"
```

#### Шаг 8: Swagger документация

Откройте в браузере:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Здесь вы можете интерактивно тестировать все API endpoints.

---

## Вариант 3: Тестирование через браузер

После запуска сервера (Шаг 6), откройте в браузере:

### 1. Swagger UI: http://localhost:8000/docs

Попробуйте:
- **GET /api/kaiten/cards** - выберите role: "director" или "head"
- Нажмите "Try it out" → "Execute"
- Увидите JSON с карточками

### 2. Прямые запросы в браузере:

- http://localhost:8000/ - информация о приложении
- http://localhost:8000/health - проверка статуса
- http://localhost:8000/api/kaiten/cards?role=director - карточки director
- http://localhost:8000/api/kaiten/cards?role=head - карточки head

---

## Ожидаемые результаты

### Для director (колонка "На подпись"):
```json
[
  {
    "id": 1001,
    "title": "Письмо в Минфин о налоговых льготах",
    "files": [
      {"name": "исх_письмо_минфин.docx", ...},
      {"name": "приложение_1.pdf", ...}
    ],
    "properties": {"id_228499": "12345"}
  },
  {
    "id": 1002,
    "title": "Договор на поставку оборудования",
    "files": [
      {"name": "исх_договор.docx", ...}
    ],
    "properties": {"id_228499": "12346"}
  }
]
```

### Для head:
```json
[
  {
    "id": 2001,
    "title": "Отчет о проделанной работе",
    "files": [
      {"name": "исх_отчет.docx", ...}
    ],
    "properties": {"id_228499": "12347"}
  }
]
```

---

## Фоновый polling

При запуске приложения автоматически запускаются 2 фоновые задачи:

1. **Polling колонки "На подпись"** (для director) - каждые 5 сек
2. **Polling колонки для head** - каждые 5 сек

В логах вы увидите:
```
[Polling] Found 2 cards in 'На подпись'
[Polling] Found 1 cards in 'Проект готов. Согласование начальника отдела'
```

---

## Остановка приложения

```bash
# Остановить uvicorn
Ctrl+C

# Остановить PostgreSQL
docker-compose down

# Удалить данные PostgreSQL (опционально)
docker-compose down -v
```

---

## Переключение на реальный Kaiten API

Когда будете готовы использовать настоящий Kaiten API:

1. Отредактируйте `.env`:
   ```bash
   KAITEN_API_URL=https://ваша-компания.kaiten.ru/api/v1
   KAITEN_API_TOKEN=ваш_настоящий_токен
   DEBUG=False  # Отключит mock-данные
   ```

2. Перезапустите приложение

---

## Troubleshooting

### Ошибка: "Port 5432 already in use"
PostgreSQL уже запущен на вашем компьютере. Либо остановите его, либо измените порт в `docker-compose.yml`.

### Ошибка: "Database connection failed"
Проверьте что PostgreSQL запущен:
```bash
docker-compose ps
```

### Ошибка: "Field required" при запуске
Убедитесь что файл `.env` существует в корне проекта.

### Mock-данные не работают
Проверьте что `DEBUG=True` в `.env` файле.

---

## Дополнительные команды

```bash
# Посмотреть логи PostgreSQL
docker-compose logs -f postgres

# Подключиться к PostgreSQL
docker exec -it outbox_postgres psql -U outbox_user -d outbox_db

# Проверить созданные таблицы
docker exec -it outbox_postgres psql -U outbox_user -d outbox_db -c "\dt"

# Посмотреть структуру таблицы
docker exec -it outbox_postgres psql -U outbox_user -d outbox_db -c "\d users"
docker exec -it outbox_postgres psql -U outbox_user -d outbox_db -c "\d outbox_journal"
```
