"""
Тесты навигации.

Использование:
    python scripts/test_navigation.py
"""

import sys
import os
import time
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eve import (
    activate_window,
    has_anomalies,
    has_anomaly_ubejishe,
    has_anomaly_ukrytie,
    find_anomaly,
    warp_to_anomaly,
    click_tab_jump,
    click_tab_pvp_foe,
    click_yellow_gate,
    click_jump_button,
    wait_jump_complete,
    wait_for_targets,
    jump_to_next_system,
    farm_anomaly,
    farm_system,
)

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def test_check_anomalies():
    """Проверить наличие аномалий (безопасно)."""
    logger.info("=== Тест: проверка аномалий ===")

    has_ubejishe = has_anomaly_ubejishe()
    has_ukrytie = has_anomaly_ukrytie()

    logger.info(f"Убежище: {'ЕСТЬ' if has_ubejishe else 'нет'}")
    logger.info(f"Укрытие: {'ЕСТЬ' if has_ukrytie else 'нет'}")
    logger.info(f"Любая аномалия: {'ЕСТЬ' if has_anomalies() else 'нет'}")

    result = find_anomaly()
    if result:
        anomaly_type, coords = result
        logger.info(f"Первая аномалия: {anomaly_type} @ {coords}")

    return has_ubejishe or has_ukrytie


def test_warp_to_anomaly():
    """Варп в аномалию."""
    logger.info("=== Тест: варп в аномалию ===")
    result = warp_to_anomaly()
    logger.info(f"Результат: {'OK' if result else 'FAIL'}")
    return result


def test_click_tab_pvp_foe():
    """Кликнуть на вкладку PvP Foe."""
    logger.info("=== Тест: вкладка PvP Foe ===")
    result = click_tab_pvp_foe()
    logger.info(f"Результат: {'OK' if result else 'FAIL'}")
    return result


def test_farm_anomaly():
    """Зачистить одну аномалию."""
    logger.info("=== Тест: зачистка аномалии ===")
    result = farm_anomaly(guns_key="2")
    logger.info(f"Результат: {'OK' if result else 'FAIL'}")
    return result


def test_farm_system():
    """Зачистить все аномалии в системе."""
    logger.info("=== Тест: фарм системы ===")
    cleared = farm_system(guns_key="2")
    logger.info(f"Зачищено аномалий: {cleared}")
    return cleared


def test_full_jump():
    """Полный прыжок в следующую систему."""
    logger.info("=== Тест: полный прыжок ===")
    result = jump_to_next_system()
    logger.info(f"Результат: {'OK' if result else 'FAIL'}")
    return result


def main():
    logger.info("Активирую окно EVE...")
    if not activate_window("EVE"):
        logger.error("Окно EVE не найдено!")
        return

    logger.info("Переключаюсь на EVE через 2 секунды...")
    time.sleep(2)

    # === ВЫБЕРИ ТЕСТ ===

    # 1. Проверка аномалий (безопасно)
    test_check_anomalies()

    # 2. Варп в аномалию
    # test_warp_to_anomaly()

    # 3. Переключение на вкладку PvP Foe
    # test_click_tab_pvp_foe()

    # 4. Зачистка одной аномалии (варп + бой)
    # test_farm_anomaly()

    # 5. Зачистка всех аномалий в системе
    # test_farm_system()

    # 6. Прыжок в следующую систему
    # test_full_jump()


if __name__ == "__main__":
    main()
