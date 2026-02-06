"""
Модуль для определения типа комнаты в Abyss.
"""
import logging
import time
from typing import Optional
from core.sanderling.service import SanderlingService

logger = logging.getLogger(__name__)


def detect_room_type(sanderling: SanderlingService, timeout: float = 30.0) -> str:
    """
    Определить тип комнаты по наличию особых NPC.
    
    Алгоритм:
    1. Переключиться на Main
    2. Ждать появления контейнера
    3. Ждать 0.5 секунды
    4. Проверить наличие особых NPC
    
    Args:
        sanderling: Сервис Sanderling
        timeout: Таймаут ожидания контейнера
        
    Returns:
        "tessera" - если найден Strikegrip Tessera
        "knight" - если найден Devoted Knight
        "overmind" - если найден Overmind или Tyrannos
        "default" - стандартная комната
    """
    logger.info("Определение типа комнаты...")
    
    # Шаг 1: Переключиться на Main
    from bots.abyss_farmer.room_new import _switch_to_tab, _wait_for_cache
    
    if not _switch_to_tab(sanderling, "Main"):
        logger.warning("Не удалось переключиться на Main, используем default")
        return "default"
    
    # Шаг 2: Ждать появления контейнера
    cache_entry = _wait_for_cache(sanderling, timeout=timeout)
    if not cache_entry:
        logger.warning("Контейнер не появился, используем default")
        return "default"
    
    logger.info(f"Контейнер найден: {cache_entry.name}")
    
    # Шаг 3: Ждать 0.5 секунды
    time.sleep(0.5)
    
    # Шаг 4: Проверить наличие особых NPC
    state = sanderling.get_state()
    if not state or not state.overview:
        logger.warning("Нет данных overview, используем default")
        return "default"
    
    # Проверяем каждую запись в overview
    for entry in state.overview:
        if not entry.name:
            continue
        
        name_lower = entry.name.lower()
        
        # Проверка на Strikegrip Tessera
        if 'tessera' in name_lower or 'strikegrip' in name_lower:
            logger.info(f"Обнаружен Strikegrip Tessera: {entry.name}")
            return "tessera"
        
        # Проверка на Devoted Knight (ТОЛЬКО Knight, не Hunter!)
        if 'devoted' in name_lower and 'knight' in name_lower:
            logger.info(f"Обнаружен Devoted Knight: {entry.name}")
            return "knight"
        
        # Проверка на Overmind/Tyrannos
        if 'overmind' in name_lower or 'tyrannos' in name_lower:
            logger.info(f"Обнаружен Overmind/Tyrannos: {entry.name}")
            return "overmind"
    
    # Если особых NPC не найдено - стандартная комната
    logger.info("Особых NPC не обнаружено - стандартная комната")
    return "default"
