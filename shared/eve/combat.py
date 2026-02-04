"""
Eve Framework - Combat module

Модуль для боевых действий:
- Управление дронами (launch, engage, recall)

Для работы с Overview и локом целей используй eve.overview:
- lock_all_targets() - залочить цели
- kill_locked_targets() - убить залоченные
- lock_and_kill() - залочить и убить пачку
- clear_anomaly() - полная зачистка аномалии
"""

import logging
from shared.keyboard import hotkey, press_key

logger = logging.getLogger(__name__)


# ============================================================================
# УПРАВЛЕНИЕ ДРОНАМИ
# ============================================================================

def launch_drones(hotkey_key: str = "shift+f"):
    """
    Запустить дронов.

    Args:
        hotkey_key: Хоткей для запуска (по умолчанию Shift+F)
    """
    logger.info(f"Запускаю дронов: {hotkey_key}")
    keys = hotkey_key.split("+")
    hotkey(*keys)


def engage_drones(hotkey_key: str = "f"):
    """
    Дроны атакуют текущую цель.

    Args:
        hotkey_key: Хоткей для атаки
    """
    logger.info(f"Дроны атакуют: {hotkey_key}")
    if "+" in hotkey_key:
        keys = hotkey_key.split("+")
        hotkey(*keys)
    else:
        press_key(hotkey_key)


def recall_drones(hotkey_key: str = "shift+r"):
    """
    Вернуть дронов в отсек.

    Args:
        hotkey_key: Хоткей для возврата
    """
    logger.info(f"Возвращаю дронов: {hotkey_key}")
    keys = hotkey_key.split("+")
    hotkey(*keys)
