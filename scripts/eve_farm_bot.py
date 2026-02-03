"""
EVE Farm Bot - Полноценный бот для фарма аномалий.

Логика работы:
1. Зачищает все аномалии (убежище/укрытие) в текущей системе
2. Прыгает в следующую систему по маршруту
3. Повторяет

Использование:
    python scripts/eve_farm_bot.py

Файл: scripts/eve_farm_bot.py
"""

import sys
import os
import time
import logging
import threading
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eve import (
    # Window
    activate_window,
    # Navigation
    has_anomalies,
    find_anomaly,
    warp_to_anomaly,
    click_tab_pvp_foe,
    click_tab_jump,
    wait_for_targets,
    jump_to_next_system,
    farm_system,
    NavigationConfig,
    # Overview
    is_overview_empty,
    clear_anomaly,
    # Vision
    find_image,
    # Mouse
    click,
    random_delay,
    # Keyboard
    press_key,
)

# Telegram уведомления
from eve.telegram_notifier import notify_expedition, notify_error

# ============================================================================
# КОНФИГУРАЦИЯ БОТА
# ============================================================================

class BotConfig:
    """Настройки бота."""

    # Клавиша пушек
    GUNS_KEY = "2"

    # Клавиши модулей поддержки (активируются после варпа на первую аномалию)
    SUPPORT_MODULES_KEYS = ["4", "5", "6"]

    # Максимум систем для фарма (0 = бесконечно)
    MAX_SYSTEMS = 0

    # Пауза между системами (сек)
    PAUSE_BETWEEN_SYSTEMS = 3.0

    # Логировать статистику каждые N систем
    STATS_LOG_INTERVAL = 5


# ============================================================================
# ЛОГИРОВАНИЕ
# ============================================================================

def setup_logging():
    """Настройка логирования в файл и консоль."""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"farm_bot_{timestamp}.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    # Приглушить httpx/telegram логи (только WARNING и выше)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(f"Лог файл: {log_file}")
    return logger


# ============================================================================
# СТАТИСТИКА
# ============================================================================

class BotStats:
    """Статистика работы бота."""

    def __init__(self):
        self.start_time = time.time()
        self.systems_visited = 0
        self.anomalies_cleared = 0
        self.targets_killed = 0
        self.jumps_made = 0
        self.expeditions_found = 0

    def to_dict(self) -> dict:
        """
        Преобразовать статистику в словарь.

        Returns:
            Словарь со статистикой
        """
        elapsed = time.time() - self.start_time
        anomalies_per_hour = (self.anomalies_cleared / elapsed * 3600) if elapsed > 0 else 0
        expedition_rate = (self.expeditions_found / self.anomalies_cleared * 100) if self.anomalies_cleared > 0 else 0

        return {
            'elapsed': elapsed,
            'systems_visited': self.systems_visited,
            'anomalies_cleared': self.anomalies_cleared,
            'expeditions_found': self.expeditions_found,
            'jumps_made': self.jumps_made,
            'anomalies_per_hour': anomalies_per_hour,
            'expedition_rate': expedition_rate,
        }

    def save_to_file(self):
        """Сохранить статистику в файл для Telegram бота."""
        import json
        stats_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "bot_stats.json")

        # Создаем папку data если не существует
        os.makedirs(os.path.dirname(stats_file), exist_ok=True)

        try:
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.getLogger(__name__).error(f"Ошибка сохранения статистики: {e}")

    def log_stats(self, logger):
        """Вывести статистику в лог."""
        elapsed = time.time() - self.start_time
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)

        # Рассчитываем метрики
        anomalies_per_hour = (self.anomalies_cleared / elapsed * 3600) if elapsed > 0 else 0
        expedition_rate = (self.expeditions_found / self.anomalies_cleared * 100) if self.anomalies_cleared > 0 else 0

        logger.info("=" * 50)
        logger.info("СТАТИСТИКА БОТА")
        logger.info(f"  Время работы: {hours}ч {minutes}м {seconds}с")
        logger.info(f"  Систем посещено: {self.systems_visited}")
        logger.info(f"  Аномалий зачищено: {self.anomalies_cleared}")
        logger.info(f"  Экспедиций найдено: {self.expeditions_found}")
        logger.info(f"  Прыжков сделано: {self.jumps_made}")
        logger.info(f"  --- Метрики ---")
        logger.info(f"  Аномалий/час: {anomalies_per_hour:.1f}")
        logger.info(f"  Шанс экспедиции: {expedition_rate:.1f}%")
        logger.info("=" * 50)

        # Сохраняем в файл
        self.save_to_file()


# ============================================================================
# МОДУЛИ ПОДДЕРЖКИ
# ============================================================================

def activate_support_modules(logger) -> None:
    """
    Активировать модули поддержки (4, 5, 6).

    Вызывается сразу после клика на варп в первую аномалию (пока летим).
    """
    logger.info("Активирую модули поддержки...")

    for key in BotConfig.SUPPORT_MODULES_KEYS:
        press_key(key)
        logger.debug(f"  Нажал '{key}'")
        random_delay(0.15, 0.25)  # ~0.2 сек между нажатиями

    logger.info("Модули поддержки активированы")


# ============================================================================
# ОБРАБОТКА ЭКСПЕДИШЕНОВ
# ============================================================================

def check_and_close_expedition_popup(logger, stats: BotStats = None) -> bool:
    """
    Проверить и закрыть popup экспедиции.

    Новая логика: Ищем текст "Guristas Scout Outpost" + кнопку Close/Close2

    Args:
        logger: Логгер
        stats: Статистика бота (для подсчёта экспедиций)

    Returns:
        True если popup был найден и закрыт
    """
    assets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")

    # Шаблоны для поиска
    text_template = os.path.join(assets_path, "eve_expedition_text.png")  # "Guristas Scout Outpost"
    close_template = os.path.join(assets_path, "eve_expedition_close.png")  # Старая кнопка
    close2_template = os.path.join(assets_path, "eve_expedition_close2.png")  # Новая кнопка

    # 1. Ищем текст экспедиции
    text_result = find_image(text_template, confidence=0.85)
    if not text_result:
        return False  # Нет текста экспедиции

    # 2. Ищем кнопку Close (сначала старую, потом новую)
    close_result = find_image(close_template, confidence=0.8)

    if not close_result:
        # Попробуем close2
        close_result = find_image(close2_template, confidence=0.8)

    if not close_result:
        logger.warning("Найден текст экспедиции, но кнопка Close не найдена")
        return False

    # 3. ОБА найдены - это экспедиция!
    logger.info("=" * 30)
    logger.info("🎉 ЭКСПЕДИЦИЯ НАЙДЕНА!")
    logger.info("=" * 30)

    # Обновляем статистику
    if stats:
        stats.expeditions_found += 1
        logger.info(f"Всего экспедиций: {stats.expeditions_found}")

        # Уведомление в Telegram
        try:
            notify_expedition(stats.expeditions_found)
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления в Telegram: {e}")

    # Жмем Close
    random_delay(0.3, 0.5)
    logger.info("Закрываю popup экспедиции...")
    click(close_result[0], close_result[1])
    random_delay(0.5, 1.0)

    return True


# ============================================================================
# ЗАПУСК TELEGRAM БОТА
# ============================================================================

def start_telegram_bot_background():
    """
    Запустить Telegram бота в фоновом потоке.

    Бот будет обрабатывать команды /start, /stats и подписывать пользователей.
    """
    import asyncio
    logger = logging.getLogger(__name__)

    try:
        from telegram import Update
        from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
        from eve.telegram_notifier import BOT_TOKEN, add_user, load_users, format_stats

        # Проверка токена
        if not BOT_TOKEN:
            logger.error("TELEGRAM_BOT_TOKEN не найден в .env файле!")
            logger.info("Создай файл .env и добавь: TELEGRAM_BOT_TOKEN=your_token")
            logger.info("Фарм бот продолжит работу БЕЗ Telegram уведомлений")
            return

        logger.info("Запускаю Telegram бота в фоне...")

        # ВАЖНО: Создаем event loop для этого потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Обработчики команд (копия из telegram_bot.py)
        async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            chat_id = update.effective_chat.id
            username = update.effective_user.username or "Unknown"
            add_user(chat_id)

            # Загружаем статистику
            stats_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "bot_stats.json")
            stats = {}
            if os.path.exists(stats_file):
                import json
                with open(stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)

            if not stats:
                text = (
                    f"👋 <b>Привет, {username}!</b>\n\n"
                    f"📢 Ты подписан на уведомления:\n"
                    f"  • 🎉 Экспедиции\n"
                    f"  • ❌ Ошибки бота\n\n"
                    f"⏳ Фарм бот запускается..."
                )
            else:
                stats_text = format_stats(stats)
                text = (
                    f"👋 <b>Привет, {username}!</b>\n\n"
                    f"📢 Ты подписан на уведомления:\n"
                    f"  • 🎉 Экспедиции\n"
                    f"  • ❌ Ошибки бота\n\n"
                    f"{stats_text}"
                )

            await update.message.reply_text(text, parse_mode='HTML')

        async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            stats_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "bot_stats.json")
            stats = {}
            if os.path.exists(stats_file):
                import json
                with open(stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)

            if not stats:
                text = "⚠️ Фарм бот ещё не начал работу."
            else:
                text = format_stats(stats)

            await update.message.reply_text(text, parse_mode='HTML')

        async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            users = load_users()
            text = f"👥 Подписчиков: {len(users)}"
            await update.message.reply_text(text, parse_mode='HTML')

        async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            chat_id = update.effective_chat.id
            add_user(chat_id)
            text = "✅ Ты подписан на уведомления!\n\nИспользуй /start для просмотра статистики."
            await update.message.reply_text(text, parse_mode='HTML')

        # Создаем приложение
        app = Application.builder().token(BOT_TOKEN).build()

        # Регистрируем обработчики
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("stats", stats_command))
        app.add_handler(CommandHandler("users", users_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

        # Запускаем бота (run_polling создаст свой event loop)
        logger.info("Telegram бот запущен ✅")
        app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            close_loop=False  # Не закрывать loop при остановке
        )

    except ImportError as e:
        logger.error(f"Библиотека не найдена: {e}")
        logger.info("Установи: pip install python-telegram-bot python-dotenv")
        logger.info("Фарм бот продолжит работу БЕЗ Telegram уведомлений")
    except Exception as e:
        logger.error(f"Ошибка запуска Telegram бота: {e}")
        logger.info("Фарм бот продолжит работу БЕЗ Telegram уведомлений")


# ============================================================================
# ОСНОВНОЙ ЦИКЛ БОТА
# ============================================================================

def farm_current_system(logger, stats: BotStats) -> int:
    """
    Зачистить текущую систему.

    Returns:
        Количество зачищенных аномалий
    """
    logger.info("=" * 50)
    logger.info(f"СИСТЕМА #{stats.systems_visited + 1}")
    logger.info("=" * 50)

    # Проверяем popup экспедиции
    check_and_close_expedition_popup(logger, stats)

    # Сначала переключаемся на вкладку Jump чтобы увидеть аномалии
    click_tab_jump()
    random_delay(0.5, 1.0)

    # Проверяем есть ли аномалии
    if not has_anomalies():
        logger.info("Аномалий нет в системе")
        return 0

    # Фармим все аномалии
    cleared = 0
    support_modules_activated = False  # Флаг: модули активированы в этой системе

    while True:
        # Ищем аномалию
        anomaly = find_anomaly()
        if not anomaly:
            logger.info("Больше аномалий не найдено")
            break

        anomaly_type, coords = anomaly
        logger.info(f"Найдена аномалия: {anomaly_type} @ {coords}")

        # Варп в аномалию
        from eve.navigation import warp_to_ukrytie, warp_to_ubejishe

        if anomaly_type == "ukrytie":
            if not warp_to_ukrytie(coords):
                logger.warning("Не удалось варпнуть в укрытие, ищу заново...")
                continue  # Заново ищем аномалию (она могла исчезнуть)
        else:
            if not warp_to_ubejishe(coords):
                logger.warning("Не удалось варпнуть в убежище, ищу заново...")
                continue  # Заново ищем аномалию (она могла исчезнуть)

        # Переключаемся на PvP Foe
        logger.info("Переключаюсь на PvP Foe...")
        random_delay(1.0, 1.5)

        if not click_tab_pvp_foe():
            logger.error("Не удалось переключиться на PvP Foe")
            break

        # После клика на PvP Foe в ПЕРВУЮ аномалию - активируем модули поддержки
        if not support_modules_activated:
            random_delay(1.0, 1.5)  # Пауза после клика на вкладку
            activate_support_modules(logger)
            support_modules_activated = True

        # Ждём появления целей (до 45 сек - пока летим в варпе)
        # wait_for_targets уже ждёт 3-4 сек после появления целей
        if not wait_for_targets(timeout=45):
            logger.warning("Цели не появились за 60 сек - аномалия уже зачищена")
            # Считаем как зачищенную (пока летели, все умерли)
            cleared += 1
            # Переключаемся обратно на Jump
            click_tab_jump()
            random_delay(1.0, 2.0)
            continue

        # Зачищаем
        killed = clear_anomaly(guns_key=BotConfig.GUNS_KEY)
        logger.info(f"Аномалия зачищена, убито: {killed}")

        cleared += 1
        stats.anomalies_cleared += 1

        # Проверяем popup экспедиции после зачистки
        check_and_close_expedition_popup(logger, stats)

        # Ждём 5 секунд после зачистки перед поиском следующей
        logger.info("Пауза после зачистки...")
        random_delay(5.0, 6.0)

        # Переключаемся обратно на Jump чтобы искать следующую
        click_tab_jump()
        random_delay(2.0, 3.0)

    return cleared


def run_bot():
    """Главная функция бота."""
    logger = setup_logging()
    stats = BotStats()

    logger.info("=" * 50)
    logger.info("EVE FARM BOT ЗАПУЩЕН")
    logger.info(f"Клавиша пушек: {BotConfig.GUNS_KEY}")
    logger.info(f"Макс. систем: {BotConfig.MAX_SYSTEMS or 'бесконечно'}")
    logger.info("=" * 50)

    # Запускаем Telegram бота в фоновом потоке
    telegram_thread = threading.Thread(
        target=start_telegram_bot_background,
        daemon=True,
        name="TelegramBot"
    )
    telegram_thread.start()
    logger.info("Telegram бот запускается в фоне...")
    time.sleep(2)  # Даём время на запуск

    # Активация окна EVE
    logger.info("Активирую окно EVE...")
    if not activate_window("EVE"):
        logger.error("Окно EVE не найдено! Убедитесь что игра запущена.")
        return

    logger.info("Начинаю через 3 секунды...")
    time.sleep(3)

    try:
        while True:
            # Проверка лимита систем
            if BotConfig.MAX_SYSTEMS > 0 and stats.systems_visited >= BotConfig.MAX_SYSTEMS:
                logger.info(f"Достигнут лимит систем ({BotConfig.MAX_SYSTEMS})")
                break

            # Фармим текущую систему
            cleared = farm_current_system(logger, stats)
            stats.systems_visited += 1

            logger.info(f"Система #{stats.systems_visited} завершена: {cleared} аномалий")

            # Статистика
            if stats.systems_visited % BotConfig.STATS_LOG_INTERVAL == 0:
                stats.log_stats(logger)
            else:
                # Просто сохраняем в файл (без вывода в лог)
                stats.save_to_file()

            # Прыжок в следующую систему
            logger.info("Прыгаю в следующую систему...")

            if not jump_to_next_system():
                logger.error("Не удалось прыгнуть! Возможно маршрут закончился.")
                break

            stats.jumps_made += 1

            # Пауза между системами
            random_delay(
                BotConfig.PAUSE_BETWEEN_SYSTEMS - 0.5,
                BotConfig.PAUSE_BETWEEN_SYSTEMS + 0.5
            )

    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем (Ctrl+C)")

    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")

        # Уведомление в Telegram об ошибке
        try:
            error_msg = f"{type(e).__name__}: {str(e)}"
            notify_error(error_msg, send_screenshot=True)
        except Exception as telegram_err:
            logger.error(f"Ошибка отправки уведомления об ошибке: {telegram_err}")

    finally:
        # Итоговая статистика
        logger.info("")
        logger.info("БОТ ЗАВЕРШЁН")
        stats.log_stats(logger)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    run_bot()
