import logging
import json
import os
from datetime import datetime
from dotenv import load_dotenv  # pip install python-dotenv
import httpx
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
    PicklePersistence,
)

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Константы состояний ---
CHOOSING, TRAINER_MENU, CLIENT_MENU, TYPING_TIME, TYPING_CALORIES, TYPING_WEIGHT, \
PROFILE_MENU, TYPING_PROFILE_DATA, TYPING_LINK_CODE, \
TYPING_FULLNAME, TYPING_EMAIL, TYPING_DURATION, TYPING_SLOT_ID, TYPING_BOOKING = range(14)

# --- API URL ---
TRAINING_API_URL = "http://127.0.0.1:8000/api/trainer"
CLIENT_API_URL = "http://127.0.0.1:8000/api/client"

# --------------------------------------------------
# --- Функции взаимодействия с API (Асинхронные) ---
# --------------------------------------------------

async def register_user_api(role: str, tg_id: int, username: str) -> None:
    """Регистрирует пользователя через API."""
    api_url = CLIENT_API_URL if role == 'Клиент' else TRAINING_API_URL
    endpoint = f"{api_url}/register/" 
    payload = {'tg_id': tg_id, 'username': username or f"user_{tg_id}"}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(endpoint, json=payload)
            if response.status_code in (200, 201, 409): 
                logger.info(f"{role} API registration successful or already exists (Status {response.status_code}).")
            else:
                logger.error(f"Failed to register {role} {username}. Status code: {response.status_code}, Response: {response.text}")
    except httpx.TimeoutException:
        logger.error(f"API connection timeout during {role} registration")
    except Exception as e:
        logger.error(f"API connection error during {role} creation: {e}")


async def api_generate_link_code(tg_id: int) -> str | None:
    """Генерирует и возвращает код привязки через API."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{TRAINING_API_URL}/generate_code/", json={'tg_id': tg_id})
            if response.status_code == 200:
                return response.json().get('code')
            else:
                logger.error(f"Failed to generate code: {response.text}")
    except httpx.TimeoutException:
        logger.error(f"API timeout generating code")
    except Exception as e:
        logger.error(f"API error generating code: {e}")
    return None


async def api_update_profile(role: str, tg_id: int, fullname: str | None, email: str | None) -> bool:
    """Обновляет данные профиля через API."""
    api_url = CLIENT_API_URL if role == 'Клиент' else TRAINING_API_URL
    endpoint = f"{api_url}/update_profile/"
    payload = {'tg_id': tg_id, 'fullname': fullname, 'email': email}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.put(endpoint, json=payload)
            return response.status_code == 200
    except httpx.TimeoutException:
        logger.error(f"API timeout updating profile")
    except Exception as e:
        logger.error(f"API error updating profile: {e}")
    return False


async def api_link_client_to_trainer(client_tg_id: int, link_code: str) -> bool:
    """Привязывает клиента к тренеру по коду через API."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{CLIENT_API_URL}/link_trainer/", 
                json={'client_tg_id': client_tg_id, 'code': link_code}
            )
            return response.status_code == 200
    except httpx.TimeoutException:
        logger.error(f"API timeout linking client")
    except Exception as e:
        logger.error(f"API error linking client: {e}")
    return False


async def api_add_free_time(tg_id: int, start_time_iso: str, duration_minutes: int) -> bool:
    """Отправляет запрос в API Django на создание нового слота с продолжительностью."""
    endpoint = f"{TRAINING_API_URL}/add_free_time/"
    payload = {'tg_id': tg_id, 'start_time': start_time_iso, 'duration_minutes': duration_minutes} 
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(endpoint, json=payload)
            if response.status_code == 201:
                return True
            else:
                logger.error(f"Failed to add free time: {response.text}")
    except httpx.TimeoutException:
        logger.error(f"API timeout adding time")
    except Exception as e:
        logger.error(f"API connection error adding time: {e}")
    return False


async def api_get_trainer_clients(trainer_tg_id: int) -> list[dict] | None:
    """Получает список клиентов тренера из API Django."""
    endpoint_url = f"{TRAINING_API_URL}/my_clients/{trainer_tg_id}/" 
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(endpoint_url)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API error getting clients: Status code {response.status_code}, Response: {response.text}")
    except httpx.TimeoutException:
        logger.error(f"API timeout getting clients")
    except Exception as e:
        logger.error(f"API connection error during get clients list: {e}")
    return None


async def api_view_trainer_slots(tg_id: int) -> list | None:
    """Получает список слотов тренера из API."""
    endpoint = f"{TRAINING_API_URL}/view_slots/" 
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(endpoint, params={'tg_id': tg_id})
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to fetch slots: {response.text}")
    except httpx.TimeoutException:
        logger.error(f"API timeout fetching slots")
    except Exception as e:
        logger.error(f"API connection error fetching slots: {e}")
    return None


async def api_delete_slot(slot_id: int) -> bool:
    """Удаляет слот через API."""
    endpoint = f"{TRAINING_API_URL}/delete_slot/{slot_id}/"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.delete(endpoint)
            return response.status_code == 204
    except httpx.TimeoutException:
        logger.error(f"API timeout deleting slot")
    except Exception as e:
        logger.error(f"API connection error deleting slot: {e}")
    return False


async def api_log_weight(tg_id: int, weight: float) -> bool:
    """Отправляет данные о весе клиента через API."""
    endpoint = f"{CLIENT_API_URL}/log_weight/"
    payload = {'tg_id': tg_id, 'weight': weight}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(endpoint, json=payload)
            return response.status_code in (200, 201)
    except httpx.TimeoutException:
        logger.error(f"API timeout logging weight")
    except Exception as e:
        logger.error(f"API error logging weight: {e}")
    return False


async def api_log_calories(tg_id: int, calories: int) -> bool:
    """Отправляет данные о калориях клиента через API."""
    endpoint = f"{CLIENT_API_URL}/log_calories/"
    payload = {'tg_id': tg_id, 'calories': calories}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(endpoint, json=payload)
            return response.status_code in (200, 201)
    except httpx.TimeoutException:
        logger.error(f"API timeout logging calories")
    except Exception as e:
        logger.error(f"API error logging calories: {e}")
    return False


async def api_get_available_slots(client_tg_id: int) -> list | None:
    """Получает доступные слоты тренера клиента."""
    endpoint = f"{CLIENT_API_URL}/available_slots/"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(endpoint, params={'tg_id': client_tg_id})
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to fetch available slots: {response.text}")
    except httpx.TimeoutException:
        logger.error(f"API timeout fetching available slots")
    except Exception as e:
        logger.error(f"API error fetching available slots: {e}")
    return None


async def api_book_slot(client_tg_id: int, slot_id: int) -> bool:
    """Бронирует слот для клиента через API."""
    endpoint = f"{CLIENT_API_URL}/book_slot/"
    payload = {'client_tg_id': client_tg_id, 'slot_id': slot_id}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(endpoint, json=payload)
            return response.status_code in (200, 201)
    except httpx.TimeoutException:
        logger.error(f"API timeout booking slot")
    except Exception as e:
        logger.error(f"API error booking slot: {e}")
    return False


# --------------------------------------------------
# --- Функции отображения меню ---
# --------------------------------------------------

def get_trainer_keyboard():
    reply_keyboard = [
        ['Посмотреть свободное время', 'Добавить свободное время'],
        ['Удалить свободное время', 'Посмотреть информацию о клиентах'],
        ['Профиль', '/cancel']
    ]
    return ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=False)


def get_client_keyboard():
    reply_keyboard = [
        ['Записаться на тренировку', 'Внести данные о весе'],
        ['Внести данные о калориях'],
        ['Профиль', '/cancel']
    ]
    return ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=False)


def get_profile_keyboard(role: str):
    buttons = []
    if role == 'Тренер':
        buttons.append(['Получить код привязки'])
        buttons.append(['Изменить данные профиля'])
    elif role == 'Клиент':
        buttons.append(['Ввести код привязки тренера'])
        buttons.append(['Изменить данные профиля'])
    
    buttons.append(['Назад в основное меню'])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)


SKIP_KEYBOARD = ReplyKeyboardMarkup([['Пропустить']], resize_keyboard=True, one_time_keyboard=True)


# --------------------------------------------------
# --- Обработчики команд и состояний ---
# --------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик команды /start."""
    if 'role' in context.user_data:
        role = context.user_data['role']
        if role == 'Тренер':
            await update.message.reply_text(
                "С возвращением! Продолжаем как Тренер.", 
                reply_markup=get_trainer_keyboard()
            )
            return TRAINER_MENU
        elif role == 'Клиент':
            await update.message.reply_text(
                "С возвращением! Продолжаем как Клиент.", 
                reply_markup=get_client_keyboard()
            )
            return CLIENT_MENU
    
    reply_keyboard = [['Тренер', 'Клиент']]
    await update.message.reply_text(
        "Привет! Ты тренер или клиент?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, resize_keyboard=True
        ),
    )
    return CHOOSING


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help."""
    await update.message.reply_text("Используйте /start для начала общения с ботом.")


async def choose_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик выбора роли пользователя."""
    user_choice = update.message.text
    user_id = update.effective_user.id
    username = update.message.from_user.username
    
    context.user_data['role'] = user_choice 
    
    if user_choice == 'Тренер':
        await register_user_api(role='Тренер', tg_id=user_id, username=username) 
        await update.message.reply_text(
            "Вы выбрали роль Тренер. Добро пожаловать!",
            reply_markup=get_trainer_keyboard(),
        )
        return TRAINER_MENU
    elif user_choice == 'Клиент':
        await register_user_api(role='Клиент', tg_id=user_id, username=username) 
        await update.message.reply_text(
            "Вы выбрали роль Клиент. Добро пожаловать!",
            reply_markup=get_client_keyboard(),
        )
        return CLIENT_MENU
    else:
        await update.message.reply_text(
            "Пожалуйста, выберите корректную роль, используя кнопки."
        )
        if 'role' in context.user_data: 
            del context.user_data['role']
        return CHOOSING


# --- Функции меню Тренера ---

async def trainer_add_time_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запрос времени начала слота."""
    await update.message.reply_text(
        "Введите **время начала** свободного слота в формате ДД.ММ ЧЧ:ММ (например, 25.12 15:30):",
        parse_mode='Markdown'
    )
    return TYPING_TIME


async def trainer_receive_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка введенного времени начала слота."""
    time_input_str = update.message.text.strip()
    
    try:
        current_year = datetime.now().year 
        dt_object = datetime.strptime(f"{time_input_str} {current_year}", "%d.%m %H:%M %Y")
        
        # Проверка, что время в будущем
        if dt_object < datetime.now():
            await update.message.reply_text(
                "⚠️ Время должно быть в будущем. Попробуйте еще раз:"
            )
            return TYPING_TIME
        
        start_time_iso = dt_object.isoformat() 
        context.user_data['temp_start_time_iso'] = start_time_iso
        context.user_data['display_time_str'] = time_input_str 
        
        await update.message.reply_text(
            "Теперь введите **продолжительность** слота в минутах (например, 60 или 90):",
            parse_mode='Markdown'
        )
        return TYPING_DURATION
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат ввода даты/времени. Используйте ДД.ММ ЧЧ:ММ. Попробуйте еще раз:"
        )
        return TYPING_TIME


async def trainer_receive_duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка продолжительности слота."""
    duration_str = update.message.text.strip()
    user_id = update.effective_user.id
    
    try:
        duration_minutes = int(duration_str)
        if duration_minutes <= 0 or duration_minutes > 480:  # Максимум 8 часов
            raise ValueError("Продолжительность должна быть от 1 до 480 минут")
    except ValueError as e:
        await update.message.reply_text(
            f"❌ Неверный формат продолжительности. Введите целое число от 1 до 480 минут. Попробуйте еще раз:"
        )
        return TYPING_DURATION
    
    start_time_iso = context.user_data.get('temp_start_time_iso')
    display_time_str = context.user_data.get('display_time_str')
    
    if await api_add_free_time(user_id, start_time_iso, duration_minutes): 
        await update.message.reply_text(
            f"✅ Слот {display_time_str} ({duration_minutes} мин) успешно добавлен.",
            reply_markup=get_trainer_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ Не удалось добавить слот через API (возможно, ошибка сервера или время занято).",
            reply_markup=get_trainer_keyboard()
        )
    
    # Очистка временных данных
    context.user_data.pop('temp_start_time_iso', None)
    context.user_data.pop('display_time_str', None)
    
    return TRAINER_MENU


async def trainer_view_clients(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Просмотр списка клиентов тренера."""
    user_id = update.effective_user.id
    clients = await api_get_trainer_clients(user_id)
    
    if clients:
        response_text = "👥 **Ваши клиенты:**\n\n"
        for client in clients.get('clients', []):
          fullname = client.get('fullname', 'Не указано')
          username = client.get('username')
          email = client.get('email', 'Не указан')
          last_weight = client.get('last_weight') or 'Нет данных'
          last_calories = client.get('last_calories') or 'Нет данных'
          last_date = client.get('last_date') or '—'

          response_text += f"**{fullname}** (@{username})\n"
          response_text += f"Email: {email}\n"
          response_text += f"Последний вес: {last_weight} кг\n"
          response_text += f"Последние калории: {last_calories}\n"
          response_text += f"Дата: {last_date}\n"
          response_text += "—" * 20 + "\n"      
        
        await update.message.reply_text(response_text, parse_mode='Markdown')
    else:
        await update.message.reply_text(
            "У вас пока нет привязанных клиентов или произошла ошибка API."
        )
    
    return TRAINER_MENU


async def trainer_view_slots(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает кнопку 'Посмотреть свободное время'."""
    user_id = update.effective_user.id
    slots = await api_view_trainer_slots(user_id)
    
    if slots:
        message_text = "📅 **Ваши текущие слоты:**\n\n"
        for slot in slots:
            status = "🔴 Занят" if slot.get('is_booked', False) else "🟢 Свободен"
            
            try:
                dt_object = datetime.fromisoformat(slot['start_time'])
                time_str = dt_object.strftime('%d.%m %H:%M')
            except (ValueError, KeyError):
                time_str = slot.get('start_time', 'N/A')
            
            duration = slot.get('duration_minutes', 'N/A')
            message_text += f"ID: `{slot['id']}` | {time_str} ({duration} мин.) | {status}\n"
        
        await update.message.reply_text(message_text, parse_mode='Markdown')
    else:
        await update.message.reply_text("У вас пока нет добавленных свободных слотов.")
    
    return TRAINER_MENU 


async def trainer_delete_slot_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запрашивает ID слота для удаления."""
    await update.message.reply_text(
        "Введите ID слота, который хотите удалить:\n\n"
        "Используйте команду 'Посмотреть свободное время' чтобы увидеть ID слотов."
    )
    return TYPING_SLOT_ID 


async def trainer_receive_slot_id_to_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает ввод ID слота и вызывает API удаления."""
    slot_id_str = update.message.text.strip()
    
    try:
        slot_id = int(slot_id_str)
        if slot_id <= 0:
            raise ValueError("ID должен быть положительным")
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат ID. Введите целое положительное число:"
        )
        return TYPING_SLOT_ID
    
    if await api_delete_slot(slot_id):
        await update.message.reply_text(
            f"✅ Слот с ID {slot_id} успешно удален.",
            reply_markup=get_trainer_keyboard()
        )
    else:
        await update.message.reply_text(
            f"❌ Не удалось удалить слот ID {slot_id} (возможно, он не существует, уже занят или ошибка API).",
            reply_markup=get_trainer_keyboard()
        )
    
    return TRAINER_MENU


# --- Функции меню Клиента ---

async def client_log_weight_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запрос веса клиента."""
    await update.message.reply_text("Введите ваш текущий вес в кг (например, 75.3):")
    return TYPING_WEIGHT


async def client_receive_weight(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка введенного веса."""
    weight_str = update.message.text.strip().replace(',', '.')
    user_id = update.effective_user.id
    
    try:
        weight = float(weight_str)
        if weight <= 0 or weight > 500:
            raise ValueError("Вес должен быть в разумных пределах")
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат веса. Введите число (например, 75.3):"
        )
        return TYPING_WEIGHT
    
    if await api_log_weight(user_id, weight):
        await update.message.reply_text(
            f"✅ Ваш вес {weight} кг записан.",
            reply_markup=get_client_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ Не удалось записать вес через API.",
            reply_markup=get_client_keyboard()
        )
    
    return CLIENT_MENU


async def client_log_calories_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запрос количества калорий."""
    await update.message.reply_text("Введите количество потребленных калорий за сегодня:")
    return TYPING_CALORIES


async def client_receive_calories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка введенного количества калорий."""
    calories_str = update.message.text.strip()
    user_id = update.effective_user.id
    
    try:
        calories = int(calories_str)
        if calories <= 0 or calories > 20000:
            raise ValueError("Калории должны быть в разумных пределах")
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат. Введите целое число калорий (например, 2000):"
        )
        return TYPING_CALORIES
    
    if await api_log_calories(user_id, calories):
        await update.message.reply_text(
            f"✅ {calories} калорий записано.",
            reply_markup=get_client_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ Не удалось записать калории через API.",
            reply_markup=get_client_keyboard()
        )
    
    return CLIENT_MENU


async def client_book_training(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает доступные слоты для записи."""
    user_id = update.effective_user.id
    slots = await api_get_available_slots(user_id)
    
    if slots is None:
        await update.message.reply_text(
            "❌ Не удалось загрузить доступные слоты. Возможно, вы еще не привязаны к тренеру.\n\n"
            "Перейдите в Профиль → Ввести код привязки тренера",
            reply_markup=get_client_keyboard()
        )
        return CLIENT_MENU
    
    if not slots:
        await update.message.reply_text(
            "К сожалению, у вашего тренера нет свободных слотов.",
            reply_markup=get_client_keyboard()
        )
        return CLIENT_MENU
    
    message_text = "📅 **Доступные слоты для записи:**\n\n"
    for slot in slots:
        try:
            dt_object = datetime.fromisoformat(slot['start_time'])
            time_str = dt_object.strftime('%d.%m %H:%M')
        except (ValueError, KeyError):
            time_str = slot.get('start_time', 'N/A')
        
        duration = slot.get('duration_minutes', 'N/A')
        message_text += f"ID: `{slot['id']}` | {time_str} ({duration} мин.)\n"
    
    message_text += "\n\nВведите ID слота, на который хотите записаться:"
    
    await update.message.reply_text(message_text, parse_mode='Markdown')
    return TYPING_BOOKING


async def client_receive_booking_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает ID слота для бронирования."""
    slot_id_str = update.message.text.strip()
    user_id = update.effective_user.id
    
    try:
        slot_id = int(slot_id_str)
        if slot_id <= 0:
            raise ValueError("ID должен быть положительным")
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат ID. Введите целое положительное число:"
        )
        return TYPING_BOOKING
    
    if await api_book_slot(user_id, slot_id):
        await update.message.reply_text(
            f"✅ Вы успешно записались на тренировку (слот ID: {slot_id})!",
            reply_markup=get_client_keyboard()
        )
    else:
        await update.message.reply_text(
            f"❌ Не удалось записаться на слот ID {slot_id} (возможно, он уже занят или не существует).",
            reply_markup=get_client_keyboard()
        )
    
    return CLIENT_MENU


# --- Функции профиля ---

async def profile_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отображает меню профиля."""
    role = context.user_data.get('role')
    await update.message.reply_text(
        f"⚙️ **Меню профиля ({role})**",
        reply_markup=get_profile_keyboard(role),
        parse_mode='Markdown'
    )
    return PROFILE_MENU


async def handle_profile_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик кнопок в меню профиля."""
    text = update.message.text
    user_id = update.effective_user.id
    role = context.user_data.get('role')
    
    if text == 'Назад в основное меню':
        if role == 'Тренер':
            await update.message.reply_text(
                "Возвращаемся в главное меню.", 
                reply_markup=get_trainer_keyboard()
            )
            return TRAINER_MENU
        else:
            await update.message.reply_text(
                "Возвращаемся в главное меню.", 
                reply_markup=get_client_keyboard()
            )
            return CLIENT_MENU
    
    elif text == 'Получить код привязки' and role == 'Тренер':
        code = await api_generate_link_code(user_id)
        if code:
            await update.message.reply_text(
                f"🔑 Ваш код привязки: `{code}`\n\nОтправьте его клиенту для привязки.", 
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ Не удалось сгенерировать код. Ошибка API.")
        return PROFILE_MENU
    
    elif text == 'Ввести код привязки тренера' and role == 'Клиент':
        await update.message.reply_text(
            "Пожалуйста, введите код привязки, полученный от вашего тренера:"
        )
        return TYPING_LINK_CODE
    
    elif text == 'Изменить данные профиля':
        await update.message.reply_text(
            "Введите ваше ФИО или нажмите 'Пропустить':",
            reply_markup=SKIP_KEYBOARD
        )
        context.user_data['temp_fullname'] = None
        context.user_data['temp_email'] = None
        return TYPING_FULLNAME
    
    else:
        await update.message.reply_text("Неизвестная команда в меню профиля.")
        return PROFILE_MENU


async def receive_fullname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка ввода ФИО."""
    fullname_input = update.message.text
    
    if fullname_input != 'Пропустить':
        context.user_data['temp_fullname'] = fullname_input.strip()
    
    await update.message.reply_text(
        "Теперь введите ваш Email или нажмите 'Пропустить':",
        reply_markup=SKIP_KEYBOARD
    )
    return TYPING_EMAIL


async def receive_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка ввода Email."""
    email_input = update.message.text
    
    if email_input != 'Пропустить':
        # Простая валидация email
        if '@' not in email_input or '.' not in email_input:
            await update.message.reply_text(
                "⚠️ Некорректный формат email. Попробуйте еще раз или нажмите 'Пропустить':",
                reply_markup=SKIP_KEYBOARD
            )
            return TYPING_EMAIL
        context.user_data['temp_email'] = email_input.strip()
    
    fullname = context.user_data.get('temp_fullname')
    email = context.user_data.get('temp_email')
    role = context.user_data.get('role')
    user_id = update.effective_user.id
    
    if await api_update_profile(role, user_id, fullname, email):
        msg = "✅ Данные профиля обновлены."
        if fullname: 
            msg += f"\nФИО: {fullname}"
        if email: 
            msg += f"\nEmail: {email}"
        await update.message.reply_text(msg, reply_markup=get_profile_keyboard(role))
    else:
        await update.message.reply_text(
            "❌ Не удалось обновить данные через API.", 
            reply_markup=get_profile_keyboard(role)
        )
    
    # Очистка временных данных
    context.user_data.pop('temp_fullname', None)
    context.user_data.pop('temp_email', None)
    
    return PROFILE_MENU


async def receive_link_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка кода привязки от клиента."""
    link_code = update.message.text.strip().upper()
    client_id = update.effective_user.id
    
    if len(link_code) < 4:
        await update.message.reply_text(
            "❌ Код привязки слишком короткий. Попробуйте еще раз:"
        )
        return TYPING_LINK_CODE
    
    if await api_link_client_to_trainer(client_id, link_code):
        await update.message.reply_text(
            "✅ Вы успешно привязаны к тренеру!",
            reply_markup=get_profile_keyboard('Клиент')
        )
    else:
        await update.message.reply_text(
            "❌ Неверный код привязки или ошибка API. Попробуйте еще раз:",
        )
        return TYPING_LINK_CODE
    
    return PROFILE_MENU


# --------------------------------------------------
# --- Общий обработчик текста для навигации ---
# --------------------------------------------------

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Главный роутер текстовых команд."""
    text = update.message.text
    
    # Глобальная кнопка "Профиль"
    if text == 'Профиль':
        return await profile_menu(update, context)
    
    user_role = context.user_data.get('role') 
    
    if user_role == 'Тренер':
        if text == 'Добавить свободное время':
            return await trainer_add_time_prompt(update, context)
        elif text == 'Посмотреть информацию о клиентах':
            return await trainer_view_clients(update, context)
        elif text == 'Удалить свободное время':
            return await trainer_delete_slot_prompt(update, context)
        elif text == 'Посмотреть свободное время':
            return await trainer_view_slots(update, context)
        else:
            await update.message.reply_text("Неизвестная команда в меню тренера.")
            return TRAINER_MENU
    
    elif user_role == 'Клиент':
        if text == 'Внести данные о весе':
            return await client_log_weight_prompt(update, context)
        elif text == 'Внести данные о калориях':
            return await client_log_calories_prompt(update, context)
        elif text == 'Записаться на тренировку':
            return await client_book_training(update, context)
        else:
            await update.message.reply_text("Неизвестная команда в меню клиента.")
            return CLIENT_MENU
    
    return await start(update, context)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена текущего диалога."""
    await update.message.reply_text(
        "Операция отменена. Используйте /start для начала.", 
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    context.chat_data.clear()
    
    return ConversationHandler.END


# --------------------------------------------------
# --- Главная функция ---
# --------------------------------------------------

def main() -> None:
    """Запуск бота."""
    persistence = PicklePersistence(filepath="bot_data.pkl") 
    
    # Получение токена из переменных окружения
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
        logger.info("Please create .env file with: TELEGRAM_BOT_TOKEN=your_token_here")
        return
    
    application = ApplicationBuilder() \
        .token(bot_token) \
        .persistence(persistence) \
        .build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_role)],
            TRAINER_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)],
            CLIENT_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)],
            PROFILE_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_profile_buttons)],
            TYPING_FULLNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_fullname)], 
            TYPING_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_email)],     
            TYPING_LINK_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link_code)],
            TYPING_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, trainer_receive_time)],
            TYPING_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, trainer_receive_duration)],
            TYPING_SLOT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, trainer_receive_slot_id_to_delete)],
            TYPING_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, client_receive_weight)],
            TYPING_CALORIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, client_receive_calories)],
            TYPING_BOOKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, client_receive_booking_id)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        persistent=True, 
        name='main_conversation'
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('help', help_command))
    
    logger.info("Bot is polling with persistence enabled...")
    application.run_polling(poll_interval=2.0)


if __name__ == '__main__':
    main()

