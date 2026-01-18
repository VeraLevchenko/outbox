# Инструкция по настройке пользователей

## Проблема

При попытке логина получаете ошибку `401 Unauthorized`, потому что пользователи из `passwords.txt` не загружены в базу данных PostgreSQL.

## Решение

Запустите обновленный скрипт `create_users.py`, который автоматически прочитает пользователей из `passwords.txt` и создаст их в БД.

## Шаги для исправления

### 1. Убедитесь, что БД PostgreSQL запущена

```bash
# Проверьте, что PostgreSQL запущен
pg_isready

# Если не запущен, запустите его
sudo systemctl start postgresql  # для Linux
# или
brew services start postgresql   # для macOS
```

### 2. Перейдите в директорию backend

```bash
cd /home/vera/outbox/backend
```

### 3. Убедитесь, что файл `.env` настроен

Проверьте, что в `.env` правильно указан `DATABASE_URL`:

```bash
cat .env | grep DATABASE_URL
```

Должно быть:
```
DATABASE_URL=postgresql://outbox_user:outbox_password@localhost:5432/outbox_db
```

### 4. Запустите скрипт создания пользователей

```bash
python create_users.py
```

Скрипт автоматически:
- Найдет файл `passwords.txt` (или использует `passwords.txt.example`)
- Прочитает пользователей из файла
- Создаст их в базе данных с хешированными паролями

### 5. Результат

Вы должны увидеть:

```
[Info] Используется /home/vera/outbox/backend/passwords.txt
======================================================================
Создание пользователей в базе данных:
======================================================================
✓ Левченко В.С.         | levchenko    | director   | levchenko123
✓ Габидулина Р.Р.       | gabidulina   | head       | gabidulina123
✓ Горская Т.К.          | gorskaya     | head       | gorskaya123
======================================================================
✓ Все пользователи (3) успешно созданы в БД!
======================================================================
```

### 6. Проверьте логин

Теперь попробуйте войти:

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"levchenko","password":"levchenko123"}'
```

Должны получить access_token в ответе.

## Что изменилось в скрипте

Обновленный `create_users.py` теперь:
- ✅ Автоматически читает пользователей из `passwords.txt`
- ✅ Ищет файл в нескольких возможных местах
- ✅ Использует `passwords.txt.example` как резервный вариант
- ✅ Создает пользователей напрямую в PostgreSQL
- ✅ Поддерживает пересоздание пользователей

## Troubleshooting

### Ошибка: "Connection refused"
БД не запущена. Запустите PostgreSQL:
```bash
sudo systemctl start postgresql
```

### Ошибка: "passwords.txt not found"
Создайте файл:
```bash
cp passwords.txt.example passwords.txt
# Отредактируйте пароли при необходимости
nano passwords.txt
```

### Ошибка: "Database does not exist"
Создайте базу данных:
```bash
python init_db.py
```

### Хочу пересоздать пользователей
Просто запустите скрипт снова:
```bash
python create_users.py
```
Введите `yes` когда скрипт спросит о пересоздании.

## Структура passwords.txt

Формат файла:
```
username:password:role:full_name
```

Пример:
```
levchenko:levchenko123:director:Левченко В.С.
gabidulina:gabidulina123:head:Габидулина Р.Р.
gorskaya:gorskaya123:head:Горская Т.К.
```

**Роли:**
- `director` - Руководитель (доступ к колонке "На подпись")
- `head` - Начальник отдела (доступ к колонке "Проект готов. Согласование начальника отдела")
