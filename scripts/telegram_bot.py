"""
EVE Telegram Bot - Обработчик команд

Команды:
- /start - Получить статистику бота
- Любое сообщение - Подписаться на уведомления

Использование:
    python scripts/telegram_bot.py

Файл: scripts/telegram_bot.py
"""

import sys
import os
import logging
import asyncio
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from shared.eve.telegram_notifier import (
    BOT_TOKEN,
    add_user,
    load_users,
    format_stats,
)

# Проверка токена
if not BOT_TOKEN:
    print("=" * 50)
    print("ОШИБКА: TELEGRAM_BOT_TOKEN не найден!")
    print("=" * 50)
    print()
    print("Создай файл .env в корне проекта:")
    print("  cp .env.example .env")
    print()
    print("И добавь токен бота:")
    print("  TELEGRAM_BOT_TOKEN=your_token_here")
    print()
    print("=" * 50)
    import sys
    sys.exit(1)

# ============================================================================
# ЛОГИРОВАНИЕ
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# ХРАНЕНИЕ СТАТИСТИКИ
# ============================================================================

# Глобальная переменная для хранения последней статистики
# Обновляется из eve_farm_bot.py через файл
STATS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "bot_stats.json")


def load_bot_stats() -> dict:
    """
    Загрузить последнюю статистику бота.

    Returns:
        Словарь со статистикой или пустой словарь
    """
    if not os.path.exists(STATS_FILE):
        return {}

    try:
        import json
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки статистики: {e}")
        return {}


# ============================================================================
# ОБРАБОТЧИКИ КОМАНД
# ============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /start.

    Добавляет пользователя в список и отправляет статистику.
    """
    chat_id = update.effective_chat.id
    username = update.effective_user.username or "Unknown"

    logger.info(f"Команда /start от {username} (chat_id: {chat_id})")

    # Добавляем пользователя в список
    add_user(chat_id)

    # Загружаем статистику
    stats = load_bot_stats()

    if not stats:
        # Статистики нет - бот не запущен
        text = (
            f"👋 <b>Привет, {username}!</b>\n\n"
            f"Бот для EVE Online запущен.\n\n"
            f"📢 Ты подписан на уведомления:\n"
            f"  • 🎉 Экспедиции\n"
            f"  • ❌ Ошибки бота\n\n"
            f"⚠️ Фарм бот сейчас не работает.\n"
            f"Запусти его командой:\n"
            f"<code>python scripts/eve_farm_bot.py</code>"
        )
    else:
        # Есть статистика - отправляем
        stats_text = format_stats(stats)

        text = (
            f"👋 <b>Привет, {username}!</b>\n\n"
            f"Бот для EVE Online запущен.\n\n"
            f"📢 Ты подписан на уведомления:\n"
            f"  • 🎉 Экспедиции\n"
            f"  • ❌ Ошибки бота\n\n"
            f"{stats_text}"
        )

    await update.message.reply_text(text, parse_mode='HTML')


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /stats - показать статистику.
    """
    chat_id = update.effective_chat.id

    logger.info(f"Команда /stats от chat_id: {chat_id}")

    # Загружаем статистику
    stats = load_bot_stats()

    if not stats:
        text = "⚠️ Фарм бот сейчас не работает."
    else:
        text = format_stats(stats)

    await update.message.reply_text(text, parse_mode='HTML')


async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /users - показать количество подписчиков.
    """
    chat_id = update.effective_chat.id

    logger.info(f"Команда /users от chat_id: {chat_id}")

    users = load_users()

    text = f"👥 Подписчиков: {len(users)}"

    await update.message.reply_text(text, parse_mode='HTML')


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик любых сообщений (не команд).

    Добавляет пользователя в список подписчиков.
    """
    chat_id = update.effective_chat.id
    username = update.effective_user.username or "Unknown"
    message_text = update.message.text

    logger.info(f"Сообщение от {username} (chat_id: {chat_id}): {message_text}")

    # Добавляем пользователя
    add_user(chat_id)

    text = (
        f"✅ Ты подписан на уведомления!\n\n"
        f"Используй /start для просмотра статистики."
    )

    await update.message.reply_text(text, parse_mode='HTML')


# ============================================================================
# ЗАПУСК БОТА
# ============================================================================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок."""
    logger.error(f"Ошибка в боте: {context.error}")


def main():
    """Главная функция - запуск бота."""
    logger.info("=" * 50)
    logger.info("EVE TELEGRAM BOT ЗАПУЩЕН")
    logger.info(f"Токен: {BOT_TOKEN[:20]}...")
    logger.info("=" * 50)

    # Создаем приложение
    app = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("users", users_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # Обработчик ошибок
    app.add_error_handler(error_handler)

    # Запускаем бота
    logger.info("Бот готов к работе. Нажми Ctrl+C для остановки.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
