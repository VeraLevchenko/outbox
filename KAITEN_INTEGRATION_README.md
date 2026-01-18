# Интеграция с Kaiten API - Инструкция

## Что было сделано

Реализована полная интеграция с Kaiten API на основе реальной структуры данных.

### Изменения в коде:

1. **Обновлена обработка properties** (`kaiten_service.py`):
   - Properties теперь обрабатываются как словарь (dict), а не список
   - Автоматическое извлечение даты из объекта `{date, time, tzOffset}`
   - Совместимость со старой структурой

2. **Обновлены mock данные**:
   - Соответствуют реальной структуре Kaiten API
   - Включают все необходимые поля

3. **Добавлены константы Kaiten** в `.env`:
   - Board ID, Lane ID
   - Column IDs (На подпись, Согласование, Готово)
   - Property IDs (incoming_no, incoming_date)

## Структура реальной карточки Kaiten

```json
{
  "id": 59837228,
  "title": "Тест 1",
  "column_id": 5592673,
  "board_id": 1612419,
  "lane_id": 1997087,
  "properties": {
    "id_228499": "1235",           // incoming_no - строка
    "id_228500": {                  // incoming_date - объект с датой
      "date": "2026-01-09",
      "time": null,
      "tzOffset": null
    }
  },
  "files": [
    {
      "id": 53643173,
      "url": "https://files.kaiten.ru/...",
      "name": "исх_КУМИ Сафоновой Н. В. список застройщиков МКД ввод 2026 и план ввода 2026 ПРИЛОЖЕНИЕ.docx",
      "size": 19332,
      "mime_type": null
    }
  ]
}
```

## Настройка .env файла

Ваш `.env` файл должен содержать:

```bash
# Kaiten API
KAITEN_API_URL=https://isogd2019.kaiten.ru/api/latest
KAITEN_API_TOKEN=ваш_токен_здесь
KAITEN_USE_MOCK=False

# Kaiten Board & Lane IDs
KAITEN_BOARD_ID=1612419
KAITEN_LANE_ID=1997087

# Kaiten Column IDs
KAITEN_COLUMN_TO_SIGN_ID=5592673
KAITEN_COLUMN_OUTBOX_ID=5592675
KAITEN_COLUMN_HEAD_REVIEW_ID=5592682

# Kaiten Properties
KAITEN_PROPERTY_INCOMING_NO=id_228499
KAITEN_PROPERTY_INCOMING_DATE=id_228500

# Для тестирования с реальным API установите:
DEBUG=False
```

## Проблема с API URL

Ранее возникала ошибка **405 Method Not Allowed** при запросе к `/api/v1/boards`.

### Возможные решения:

1. **Попробуйте другую версию API**:
   ```bash
   # В .env измените:
   KAITEN_API_URL=https://isogd2019.kaiten.ru/api/latest
   ```

2. **Запустите тест версий API**:
   ```bash
   cd /home/vera/outbox/backend
   python test_kaiten_api_version.py
   ```

   Скрипт автоматически протестирует:
   - `/api/latest`
   - `/api/v1`
   - `/api`

3. **Используйте прямой запрос карточек**:
   Эндпоинт `/cards` обычно работает надежнее, чем `/boards`

## Тестирование интеграции

### 1. Проверка подключения
```bash
cd /home/vera/outbox/backend

# Убедитесь что в .env:
# DEBUG=False (для реального API)
# KAITEN_USE_MOCK=False

python test_kaiten_connection.py
```

### 2. Запуск приложения
```bash
./run.sh
```

### 3. Тест через API
```bash
# Получить карточки для директора
curl "http://localhost:8000/api/kaiten/cards?role=director"

# Получить карточки для начальника отдела
curl "http://localhost:8000/api/kaiten/cards?role=head"

# Тест подключения
curl "http://localhost:8000/api/kaiten/debug/connection"
```

## Что извлекается из карточек

Приложение автоматически извлекает:

1. **incoming_no** (id_228499):
   - Номер входящего документа
   - Тип: строка (например, "1235")

2. **incoming_date** (id_228500):
   - Дата входящего документа
   - Извлекается поле `date` из объекта
   - Формат: "2026-01-09"

3. **Files**:
   - Полный список файлов с URL
   - Определение основного документа (начинается с "исх_")

## API Эндпоинты

### GET /api/kaiten/cards?role={director|head}
Получить карточки для роли:
- `director` → колонка "На подпись" (ID: 5592673)
- `head` → колонка "Согласование начальника отдела" (ID: 5592682)

Ответ:
```json
{
  "cards": [
    {
      "id": 59837228,
      "title": "Тест 1",
      "column_id": 5592673,
      "incoming_no": "1235",
      "incoming_date": "2026-01-09",
      "files": [...]
    }
  ],
  "total": 1
}
```

### POST /api/kaiten/cards/{card_id}/move
Переместить карточку:
```bash
curl -X POST "http://localhost:8000/api/kaiten/cards/59837228/move" \
  -H "Content-Type: application/json" \
  -d '{"target_column_id": 5592675, "comment": "Подписано"}'
```

### GET /api/kaiten/debug/connection
Проверить подключение к Kaiten API

## Отладка

Если карточки не появляются:

1. **Проверьте логи**:
   ```bash
   ./run.sh
   # Смотрите вывод в консоли
   ```

2. **Убедитесь в правильности ID**:
   - Board ID: 1612419
   - Lane ID: 1997087
   - Column ID (На подпись): 5592673

3. **Проверьте фильтрацию**:
   - Карточки должны быть именно в указанной колонке
   - Проверьте board_id и lane_id

4. **Включите DEBUG логи**:
   В `kaiten_service.py:188` установлен `logger.debug` для детальных логов

## Следующие шаги

После успешного подключения к Kaiten API:

1. ✅ Интеграция с Kaiten (ГОТОВО)
2. ⏭️ Генерация номеров исходящих документов
3. ⏭️ Заполнение DOCX шаблонов
4. ⏭️ Конвертация DOCX → PDF
5. ⏭️ Электронная подпись (CryptoPro)
6. ⏭️ Сохранение в `/mnt/doc/Исходящие/`
7. ⏭️ Перемещение карточек в Kaiten

---

**Важно**: После обновления кода на локальном компьютере (`git pull`), не забудьте:
1. Исправить `.env` файл (правильные названия переменных)
2. Установить `DEBUG=False` для работы с реальным API
3. Запустить тесты для проверки
