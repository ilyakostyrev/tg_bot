# tg_bot

Telegram-бот для управления тренировками между тренерами и клиентами.

## О проекте

**tg_bot** — это Telegram-бот, который помогает тренерам и клиентам взаимодействовать в сфере фитнеса/персональных тренировок.

### Основные возможности

**Для Тренеров:**
- Добавление/просмотр/удаление свободного времени для тренировок
- Просмотр списка привязанных клиентов
- Генерация кода привязки для клиентов
- Управление профилем

**Для Клиентов:**
- Просмотр доступных слотов тренера
- Запись на тренировку
- Ведение дневника веса и потреблённых калорий
- Привязка к тренеру по коду

**Общее:**
- Регистрация как "Тренер" или "Клиент"
- Удобное меню с клавиатурой
- Интеграция с Django REST API (`tg_bot_api`)
- Сохранение состояний через PicklePersistence
- Асинхронная работа с API

## Структура проекта
tg_bot/
├── tg_bot/                 # Основной Telegram-бот
│   ├── bot.py              # Главная логика бота
│   ├── .env                # Переменные окружения (BOT_TOKEN и др.)
│   └── bot_data.pkl        # Сохранённые данные состояний
│
└── tg_bot_api/             # Django REST API backend
├── main/               # Django проект
├── bd_client/          # Приложение для клиентов
└── bd_trainer/         # Приложение для тренеров
text## Технологии

- **Telegram Bot**: `python-telegram-bot` (v20+)
- **Backend API**: Django + Django REST Framework
- **База данных**: SQLite / PostgreSQL (настраивается в API)
- **HTTP-запросы**: `httpx` (async)
- **Переменные окружения**: `python-dotenv`

## Как запустить

### 1. Telegram-бот

```bash
cd tg_bot/tg_bot

# Установка зависимостей
pip install python-telegram-bot python-dotenv httpx

# Настройте .env файл (BOT_TOKEN)
cp .env.example .env

# Запуск бота
python bot.py
2. Django API (tg_bot_api)
Bashcd tg_bot/tg_bot_api/main

pip install django djangorestframework

python manage.py migrate
python manage.py runserver
Бот по умолчанию обращается к API по адресу http://127.0.0.1:8000.
Команды бота

/start — начало работы / выбор роли
/help — справка
/cancel — отмена текущего действия

Будущие улучшения

Деплой на сервер (Heroku / VPS)
Уведомления о предстоящих тренировках
Статистика прогресса клиента
Webhook вместо polling
