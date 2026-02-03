"""
Eve Framework - Telegram notifications module

Отправка уведомлений в Telegram:
- Уведомления о экспедициях
- Уведомления об ошибках + скриншот
- Статистика бота
"""

import os
import json
import logging
import asyncio
from typing import List, Optional
from datetime import datetime
import mss
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)

# Загрузка токена из .env файла
try:
    from dotenv import load_dotenv
    load_dotenv()
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    if not BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN не найден в .env файле")
        BOT_TOKEN = None
except ImportError:
    logger.warning("python-dotenv не установлен, используйте: pip install python-dotenv")
    BOT_TOKEN = None

# Файл для хранения chat_id пользователей
USERS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "telegram_users.json")


# ============================================================================
# УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ
# ============================================================================

def _ensure_data_dir():
    """Создать папку data если не существует."""
    data_dir = os.path.dirname(USERS_FILE)
    os.makedirs(data_dir, exist_ok=True)


def load_users() -> List[int]:
    """
    Загрузить список chat_id пользователей.

    Returns:
        Список chat_id
    """
    _ensure_data_dir()

    if not os.path.exists(USERS_FILE):
        return []

    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('users', [])
    except Exception as e:
        logger.error(f"Ошибка загрузки пользователей: {e}")
        return []


def save_users(users: List[int]) -> None:
    """
    Сохранить список chat_id пользователей.

    Args:
        users: Список chat_id
    """
    _ensure_data_dir()

    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump({'users': users}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения пользователей: {e}")


def add_user(chat_id: int) -> None:
    """
    Добавить пользователя в список.

    Args:
        chat_id: ID чата пользователя
    """
    users = load_users()

    if chat_id not in users:
        users.append(chat_id)
        save_users(users)
        logger.info(f"Добавлен пользователь: {chat_id}")


# ============================================================================
# СКРИНШОТЫ
# ============================================================================

def take_screenshot() -> Optional[BytesIO]:
    """
    Сделать скриншот экрана.

    Returns:
        BytesIO с изображением или None при ошибке
    """
    try:
        with mss.mss() as sct:
            # Снимок всего экрана (первый монитор)
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)

            # Конвертируем в PIL Image
            img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')

            # Сохраняем в BytesIO
            bio = BytesIO()
            bio.name = 'screenshot.png'
            img.save(bio, 'PNG')
            bio.seek(0)

            return bio
    except Exception as e:
        logger.error(f"Ошибка создания скриншота: {e}")
        return None


# ============================================================================
# ОТПРАВКА СООБЩЕНИЙ
# ============================================================================

async def _send_message_async(chat_id: int, text: str) -> bool:
    """
    Отправить текстовое сообщение (async).

    Args:
        chat_id: ID чата
        text: Текст сообщения

    Returns:
        True если успешно
    """
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не установлен")
        return False

    try:
        from telegram import Bot

        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения в {chat_id}: {e}")
        return False


async def _send_photo_async(chat_id: int, photo: BytesIO, caption: str = None) -> bool:
    """
    Отправить фото (async).

    Args:
        chat_id: ID чата
        photo: BytesIO с изображением
        caption: Подпись к фото

    Returns:
        True если успешно
    """
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не установлен")
        return False

    try:
        from telegram import Bot

        bot = Bot(token=BOT_TOKEN)
        await bot.send_photo(chat_id=chat_id, photo=photo, caption=caption, parse_mode='HTML')
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки фото в {chat_id}: {e}")
        return False


def send_message(chat_id: int, text: str) -> bool:
    """
    Отправить текстовое сообщение (sync wrapper).

    Args:
        chat_id: ID чата
        text: Текст сообщения

    Returns:
        True если успешно
    """
    try:
        return asyncio.run(_send_message_async(chat_id, text))
    except Exception as e:
        logger.error(f"Ошибка в send_message: {e}")
        return False


def send_photo(chat_id: int, photo: BytesIO, caption: str = None) -> bool:
    """
    Отправить фото (sync wrapper).

    Args:
        chat_id: ID чата
        photo: BytesIO с изображением
        caption: Подпись к фото

    Returns:
        True если успешно
    """
    try:
        return asyncio.run(_send_photo_async(chat_id, photo, caption))
    except Exception as e:
        logger.error(f"Ошибка в send_photo: {e}")
        return False


# ============================================================================
# УВЕДОМЛЕНИЯ ВСЕМ ПОЛЬЗОВАТЕЛЯМ
# ============================================================================

def notify_all_users(text: str) -> int:
    """
    Отправить уведомление всем пользователям.

    Args:
        text: Текст сообщения

    Returns:
        Количество успешно отправленных сообщений
    """
    users = load_users()

    if not users:
        logger.info("Нет пользователей для уведомления")
        return 0

    success_count = 0

    for chat_id in users:
        if send_message(chat_id, text):
            success_count += 1

    logger.info(f"Отправлено уведомлений: {success_count}/{len(users)}")
    return success_count


def notify_expedition(expedition_count: int) -> None:
    """
    Уведомить всех пользователей о выпадении экспедиции.

    Args:
        expedition_count: Общее количество экспедиций
    """
    timestamp = datetime.now().strftime("%H:%M:%S")

    text = (
        f"🎉 <b>ЭКСПЕДИЦИЯ!</b>\n\n"
        f"⏰ Время: {timestamp}\n"
        f"📦 Всего найдено: {expedition_count}"
    )

    notify_all_users(text)
    logger.info("Отправлены уведомления об экспедиции")


def notify_error(error_message: str, send_screenshot: bool = True) -> None:
    """
    Уведомить всех пользователей об ошибке.

    Args:
        error_message: Текст ошибки
        send_screenshot: Отправлять ли скриншот
    """
    users = load_users()

    if not users:
        logger.info("Нет пользователей для уведомления об ошибке")
        return

    timestamp = datetime.now().strftime("%H:%M:%S")

    text = (
        f"❌ <b>ОШИБКА БОТА</b>\n\n"
        f"⏰ Время: {timestamp}\n\n"
        f"<code>{error_message}</code>"
    )

    # Отправляем текст
    for chat_id in users:
        send_message(chat_id, text)

    # Отправляем скриншот
    if send_screenshot:
        screenshot = take_screenshot()
        if screenshot:
            for chat_id in users:
                screenshot.seek(0)  # Сброс позиции для каждой отправки
                send_photo(chat_id, screenshot, caption="Скриншот в момент ошибки")

    logger.info("Отправлены уведомления об ошибке")


def format_stats(stats_dict: dict) -> str:
    """
    Форматировать статистику бота для отправки.

    Args:
        stats_dict: Словарь со статистикой

    Returns:
        Форматированный текст
    """
    elapsed = stats_dict.get('elapsed', 0)
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = int(elapsed % 60)

    anomalies_per_hour = stats_dict.get('anomalies_per_hour', 0)
    expedition_rate = stats_dict.get('expedition_rate', 0)

    text = (
        f"📊 <b>СТАТИСТИКА БОТА</b>\n\n"
        f"⏱ Время работы: {hours}ч {minutes}м {seconds}с\n"
        f"🌟 Систем посещено: {stats_dict.get('systems_visited', 0)}\n"
        f"💥 Аномалий зачищено: {stats_dict.get('anomalies_cleared', 0)}\n"
        f"🎉 Экспедиций найдено: {stats_dict.get('expeditions_found', 0)}\n"
        f"🚀 Прыжков сделано: {stats_dict.get('jumps_made', 0)}\n\n"
        f"<b>Метрики:</b>\n"
        f"📈 Аномалий/час: {anomalies_per_hour:.1f}\n"
        f"🎲 Шанс экспедиции: {expedition_rate:.1f}%"
    )

    return text


def send_stats_to_user(chat_id: int, stats_dict: dict) -> bool:
    """
    Отправить статистику конкретному пользователю.

    Args:
        chat_id: ID чата пользователя
        stats_dict: Словарь со статистикой

    Returns:
        True если успешно
    """
    text = format_stats(stats_dict)
    return send_message(chat_id, text)
