"""
EVE Abyss Farmer Bot - Бот для фарма абиссов.

Возможности:
- Автоматический вход в абисс
- Зачистка комнат
- Сбор лута
- Выход из абисса

Использование:
    python bots/abyss_farmer/main.py

Версия: 0.2.0
"""

import sys
import os
import logging
import time
from datetime import datetime

# Добавляем корневую папку проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.window import activate_window
from core.sanderling.service import SanderlingService
from bots.abyss_farmer.enter import enter_abyss
from bots.abyss_farmer.room import room
from config import FILAMENT_NAMES


def setup_logging():
    """Настройка логирования."""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"abyss_bot_{timestamp}.log")

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


def run_bot():
    """Главная функция бота."""
    logger = setup_logging()

    logger.info("=" * 50)
    logger.info("EVE ABYSS FARMER BOT v0.2.0")
    logger.info("=" * 50)

    # Активация окна EVE
    logger.info("Активирую окно EVE...")
    if not activate_window("EVE"):
        logger.error("Окно EVE не найдено! Убедитесь что игра запущена.")
        return

    # Запуск Sanderling
    logger.info("Запускаю Sanderling...")
    sanderling = SanderlingService()
    if not sanderling.start():
        logger.error("Не удалось запустить Sanderling")
        return

    try:
        # Прогрев Sanderling
        logger.info("Жду 3 секунды для прогрева Sanderling...")
        time.sleep(3)

        # Основной цикл бота
        run_count = 0
        max_runs = 10  # Максимум 10 забегов

        while run_count < max_runs:
            run_count += 1
            logger.info(f"")
            logger.info(f"{'=' * 50}")
            logger.info(f"ЗАБЕГ #{run_count}/{max_runs}")
            logger.info(f"{'=' * 50}")

            # 1. Вход в абисс
            logger.info("Этап 1: Вход в абисс...")
            if not enter_abyss(sanderling, filament_name=FILAMENT_NAMES['CALM_EXOTIC']):
                logger.error("Не удалось войти в абисс, останавливаю бота")
                break

            logger.info("Успешно вошли в абисс!")
            time.sleep(5)  # Ждем загрузки

            # 2. Прохождение комнат (пока только одна)
            logger.info("Этап 2: Прохождение комнаты...")
            if not room(sanderling, timeout=300.0):
                logger.error("Не удалось пройти комнату, останавливаю бота")
                break

            logger.info("Комната пройдена!")

            # TODO: Добавить выход из абисса
            logger.info("TODO: Выход из абисса (пока не реализовано)")
            logger.info(f"Забег #{run_count} завершен!")

            # Пауза между забегами
            if run_count < max_runs:
                logger.info("Пауза 10 секунд перед следующим забегом...")
                time.sleep(10)

        logger.info("")
        logger.info(f"{'=' * 50}")
        logger.info(f"БОТ ЗАВЕРШИЛ РАБОТУ")
        logger.info(f"Всего забегов: {run_count}")
        logger.info(f"{'=' * 50}")

    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")

    finally:
        logger.info("Останавливаю Sanderling...")
        sanderling.stop()


if __name__ == "__main__":
    run_bot()
