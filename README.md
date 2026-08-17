# TaskManager Bot

**@taskmezerokharu_bot** — Telegram-бот для управления задачами команды.

> Попробуйте бота прямо сейчас: откройте Telegram, найдите **@taskmezerokharu_bot** и нажмите `/start`.

## Возможности

- Добавление задач с названием, описанием и плановым сроком
- Список всех задач с иконками статусов и приоритетов
- Статусы: Не начата / В работе / На проверке / Доработка / Выполнена
- Приоритеты: Высокий / Средний / Низкий
- Делегирование исполнителю по @username или ID
- Установка и изменение планового срока
- Комментарии к задачам для заказчика
- Экспорт в CSV-файл
- Персистентное хранение в SQLite (данные не теряются при перезапуске)
- Множественные пользователи — вся команда работает через одного бота

## Быстрый старт (свои токен и бот)

### 1. Клонирование

```bash
git clone https://github.com/Kharusaki/VPb06.-Telegram--.git
cd VPb06.-Telegram--
```

### 2. Виртуальное окружение

```bash
python -m venv venv
```

**Windows:**
```bash
venv\Scripts\activate
```

**macOS / Linux:**
```bash
source venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Создание бота в Telegram

1. Откройте Telegram, найдите **@BotFather**
2. Отправьте `/newbot`
3. Задайте имя бота (например: `My Task Manager`)
4. Задайте username (должен заканчиваться на `bot`)
5. Скопируйте полученный токен

### 5. Настройка токена

```bash
cp .env.example .env
```

Откройте `.env` и вставьте свой токен:

```env
BOT_TOKEN=ваш_токен_от_BotFather
```

### 6. Запуск

```bash
python main.py
```

Откройте Telegram, найдите своего бота и отправьте `/start`.

## Тестовые данные

В папке `test_data/` находится готовая база `tasks.db` с примерами задач.

### Как подключить тестовую базу

**Windows:**
```bash
copy test_data\tasks.db tasks.db
python main.py
```

**macOS / Linux:**
```bash
cp test_data/tasks.db tasks.db
python main.py
```

Бот загрузит тестовые задачи — можно сразу смотреть список (`/list`), комментировать, менять статусы.

### Как сбросить базу

Удалите файл `tasks.db` в корне проекта — бот создаст новую пустую базу при следующем запуске.

## Команды бота

### Основные

| Команда | Описание |
|---------|----------|
| `/start` | Приветствие и подсказка |
| `/help` | Подробная справка |
| `/add` | Добавить задачу (название -> описание -> срок) |
| `/list` | Показать все задачи |
| `/list_csv` | Скачать CSV-файл |
| `/select_task` | Выбрать задачу для редактирования |
| `/cancel` | Отменить текущее действие |

### Редактирование выбранной задачи

После `/select_task` и выбора задачи:

| Команда | Описание |
|---------|----------|
| `/edit_name` | Изменить название |
| `/add_description` | Добавить описание |
| `/set_duedate` | Установить срок (ДД.ММ.ГГГГ) |
| `/set_incharge` | Назначить исполнителя |
| `/set_priority` | Установить приоритет |
| `/edit_status` | Изменить статус |
| `/comment` | Оставить комментарий |
| `/view_comments` | Посмотреть комментарии |
| `/set_done` | Закрыть задачу |
| `/delete_task` | Удалить задачу |

### Поток работы

```
/add               -> создать задачу
/select_task       -> выбрать задачу из списка
/edit_name, ...    -> редактировать
/comment           -> оставить комментарий
/set_done          -> закрыть задачу
```

## Структура проекта

```
.
├── main.py                    # Точка входа
├── bot/
│   ├── config.py              # Конфигурация
│   ├── db/
│   │   └── database.py        # SQLite CRUD
│   ├── handlers/
│   │   ├── start.py           # /start, /help, /cancel
│   │   ├── tasks.py           # /add, /list, /list_csv
│   │   ├── commands.py        # /select_task, /comment, /edit_name, ...
│   │   ├── edit.py            # Inline-кнопки
│   │   └── delete.py          # Удаление
│   ├── keyboards/
│   │   └── inline.py          # Inline-клавиатуры
│   ├── states/
│   │   └── states.py          # FSM
│   └── utils/
│       ├── csv_export.py      # Экспорт CSV
│       └── fmt.py             # Форматирование дат
├── assets/
│   └── welcome.png            # Приветственная картинка
├── test_data/
│   └── tasks.db               # Тестовая база с примерами
├── requirements.txt
├── .env.example
└── .gitignore
```

## Технологии

- Python 3.12+
- aiogram 3.x
- SQLite3
- python-dotenv

## Лицензия

MIT
