"""
Eve Framework - Modules management

Управление модулями корабля (активация средних слотов).
"""

import logging
from typing import Optional, List
from eve.keyboard import press_key
from eve.mouse import random_delay

logger = logging.getLogger(__name__)


def ensure_mid_slots_active(
    left_key: str = "2",
    right_key: str = "3",
    sanderling_service=None
) -> bool:
    """
    Убедиться что оба активных модуля в средних слотах включены.
    
    Логика:
    - Модуль слева (меньший X) = left_key (по умолчанию "2")
    - Модуль справа (больший X) = right_key (по умолчанию "3")
    - Нажатие клавиши ПЕРЕКЛЮЧАЕТ модуль (toggle)
    - Включаем только те модули, которые неактивны
    
    Args:
        left_key: Хоткей для левого модуля (по умолчанию "2")
        right_key: Хоткей для правого модуля (по умолчанию "3")
        sanderling_service: Инстанс SanderlingService (опционально)
        
    Returns:
        True если оба модуля активны или были успешно активированы
        
    Example:
        >>> from core.sanderling.service import SanderlingService
        >>> sanderling = SanderlingService()
        >>> sanderling.start()
        >>> ensure_mid_slots_active(sanderling_service=sanderling)
        True
    """
    # Если Sanderling не передан, активируем вслепую
    if not sanderling_service:
        logger.warning("Sanderling service не передан, активирую модули вслепую")
        _activate_module(left_key)
        random_delay(0.1, 0.2)
        _activate_module(right_key)
        return True
    
    # Получить состояние корабля
    state = sanderling_service.get_state()
    
    if not state or not state.ship or not state.ship.modules:
        logger.warning("Нет данных о модулях, активирую вслепую")
        _activate_module(left_key)
        random_delay(0.1, 0.2)
        _activate_module(right_key)
        return True
    
    # Найти активные модули в средних слотах (пассивные не имеют center)
    mid_modules = [m for m in state.ship.modules 
                   if m.slot_type == 'mid' and m.center is not None]
    
    if len(mid_modules) < 2:
        logger.warning(f"Найдено только {len(mid_modules)} активных модулей в средних слотах")
        # Активируем оба на всякий случай
        _activate_module(left_key)
        random_delay(0.1, 0.2)
        _activate_module(right_key)
        return True
    
    # Сортировать по X-координате (слева направо)
    mid_modules.sort(key=lambda m: m.center[0])
    
    # Взять два первых (самые левые)
    left_module = mid_modules[0]
    right_module = mid_modules[1]
    
    logger.debug(f"Левый модуль ({left_module.slot_name}): {'активен' if left_module.is_active else 'неактивен'}")
    logger.debug(f"Правый модуль ({right_module.slot_name}): {'активен' if right_module.is_active else 'неактивен'}")
    
    # Проверить какие модули нужно включить
    need_activate_left = not left_module.is_active
    need_activate_right = not right_module.is_active
    
    if not need_activate_left and not need_activate_right:
        logger.debug("Оба модуля уже активны")
        return True
    
    # Активировать только неактивные модули
    if need_activate_left:
        logger.info(f"Активирую левый модуль: {left_key}")
        _activate_module(left_key)
        random_delay(0.15, 0.25)
    
    if need_activate_right:
        logger.info(f"Активирую правый модуль: {right_key}")
        _activate_module(right_key)
        random_delay(0.15, 0.25)
    
    logger.info("Модули активированы")
    return True


def _activate_module(hotkey: str) -> None:
    """
    Активировать модуль по хоткею.
    
    Args:
        hotkey: Клавиша для активации модуля
    """
    logger.debug(f"Нажимаю клавишу: {hotkey}")
    press_key(hotkey)
    random_delay(0.05, 0.1)
