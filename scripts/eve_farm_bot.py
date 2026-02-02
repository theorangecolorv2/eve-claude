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
)

# ============================================================================
# КОНФИГУРАЦИЯ БОТА
# ============================================================================

class BotConfig:
    """Настройки бота."""

    # Клавиша пушек
    GUNS_KEY = "2"

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

    def log_stats(self, logger):
        """Вывести статистику в лог."""
        elapsed = time.time() - self.start_time
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)

        logger.info("=" * 50)
        logger.info("СТАТИСТИКА БОТА")
        logger.info(f"  Время работы: {hours}ч {minutes}м")
        logger.info(f"  Систем посещено: {self.systems_visited}")
        logger.info(f"  Аномалий зачищено: {self.anomalies_cleared}")
        logger.info(f"  Прыжков сделано: {self.jumps_made}")
        logger.info("=" * 50)


# ============================================================================
# ОБРАБОТКА ЭКСПЕДИШЕНОВ
# ============================================================================

def check_and_close_expedition_popup(logger) -> bool:
    """
    Проверить и закрыть popup экспедиции.

    Returns:
        True если popup был найден и закрыт
    """
    assets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
    template = os.path.join(assets_path, "eve_expedition_popup.png")

    result = find_image(template, confidence=0.8)
    if result:
        logger.info("Обнаружен popup экспедиции, закрываю...")
        # Кликаем на popup чтобы закрыть (или можно искать кнопку закрытия)
        click(result[0], result[1])
        random_delay(0.5, 1.0)
        return True

    return False


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
    check_and_close_expedition_popup(logger)

    # Сначала переключаемся на вкладку Jump чтобы увидеть аномалии
    click_tab_jump()
    random_delay(0.5, 1.0)

    # Проверяем есть ли аномалии
    if not has_anomalies():
        logger.info("Аномалий нет в системе")
        return 0

    # Фармим все аномалии
    cleared = 0

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
                logger.error("Не удалось варпнуть в укрытие")
                break
        else:
            if not warp_to_ubejishe(coords):
                logger.error("Не удалось варпнуть в убежище")
                break

        # Ждём прибытия (60 сек варпа + 5 сек загрузки)
        logger.info("Жду прибытия в аномалию...")
        random_delay(25.0, 30.0)  # Примерное время варпа

        # Переключаемся на PvP Foe
        if not click_tab_pvp_foe():
            logger.error("Не удалось переключиться на PvP Foe")
            break

        random_delay(1.0, 2.0)

        # Ждём появления целей
        if not wait_for_targets(timeout=120):
            logger.warning("Цели не появились - аномалия пустая?")
            # Всё равно считаем как зачищенную
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
        check_and_close_expedition_popup(logger)

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
