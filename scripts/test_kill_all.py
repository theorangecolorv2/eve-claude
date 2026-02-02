"""
Тесты боевых функций.

Использование:
    python scripts/test_kill_all.py
"""

import sys
import os
import time
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eve import (
    activate_window,
    count_targets,
    lock_all_targets,
    kill_locked_targets,
    lock_and_kill,
    clear_anomaly,
    has_locked_targets,
)

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def test_count_only():
    """Только подсчёт целей (безопасно)."""
    logger.info("=== Тест: подсчёт целей ===")
    count = count_targets()
    logger.info(f"Найдено целей: {count}")
    return count


def test_lock_only():
    """Только лок целей (без стрельбы)."""
    logger.info("=== Тест: лок целей ===")
    locked = lock_all_targets()
    logger.info(f"Залочено целей: {locked}")
    return locked


def test_has_locked():
    """Проверка наличия залоченных целей."""
    logger.info("=== Тест: проверка лока ===")
    has_lock = has_locked_targets()
    logger.info(f"Есть залоченные: {has_lock}")
    return has_lock


def test_lock_and_kill():
    """Лок + убийство одной пачки."""
    logger.info("=== Тест: lock_and_kill ===")
    killed = lock_and_kill(guns_key="2", check_interval=1.0, kill_timeout=60.0)
    logger.info(f"Убито: {killed}")
    return killed


def test_clear_anomaly():
    """Полная зачистка аномалии."""
    logger.info("=== Тест: clear_anomaly ===")
    killed = clear_anomaly(guns_key="2", check_interval=1.0, kill_timeout=60.0, max_waves=10)
    logger.info(f"Всего убито: {killed}")
    return killed


def main():
    logger.info("Активирую окно EVE...")
    if not activate_window("EVE"):
        logger.error("Окно EVE не найдено!")
        return

    logger.info("Переключаюсь на EVE через 2 секунды...")
    time.sleep(2)

    # === ВЫБЕРИ ТЕСТ ===

    # 1. Только подсчёт (безопасно)
    # test_count_only()

    # 2. Только лок (Ctrl+Click, без стрельбы)
    # test_lock_only()

    # 3. Проверка есть ли залоченные цели
    # test_has_locked()

    # 4. Лок + убийство одной пачки (до 5 целей)
    # test_lock_and_kill()

    # 5. Полная зачистка аномалии (все волны)
    test_clear_anomaly()


if __name__ == "__main__":
    main()
