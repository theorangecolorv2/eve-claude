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
    from eve.keyboard import key_down, key_up, press_key
    from eve.mouse import random_delay
    
    logger.info(f"Запускаю дронов: {hotkey_key}")
    
    # Разбираем хоткей
    keys = hotkey_key.split("+")
    
    if len(keys) == 2:
        # Комбинация типа shift+f
        modifier = keys[0].strip().lower()
        main_key = keys[1].strip().lower()
        
        # Зажимаем модификатор
        key_down(modifier)
        random_delay(0.05, 0.1)
        
        # Нажимаем основную клавишу
        press_key(main_key)
        random_delay(0.05, 0.1)
        
        # Отжимаем модификатор
        key_up(modifier)
        random_delay(0.1, 0.15)
    else:
        # Простая клавиша
        press_key(keys[0])
        random_delay(0.1, 0.15)


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
    from eve.keyboard import key_down, key_up, press_key
    from eve.mouse import random_delay
    
    logger.info(f"Возвращаю дронов: {hotkey_key}")
    
    # Разбираем хоткей
    keys = hotkey_key.split("+")
    
    if len(keys) == 2:
        # Комбинация типа shift+r
        modifier = keys[0].strip().lower()
        main_key = keys[1].strip().lower()
        
        # Зажимаем модификатор
        key_down(modifier)
        random_delay(0.05, 0.1)
        
        # Нажимаем основную клавишу
        press_key(main_key)
        random_delay(0.05, 0.1)
        
        # Отжимаем модификатор
        key_up(modifier)
        random_delay(0.1, 0.15)
    else:
        # Простая клавиша
        press_key(keys[0])
        random_delay(0.1, 0.15)
