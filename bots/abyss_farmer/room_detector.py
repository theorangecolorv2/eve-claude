"""
Модуль для определения типа комнаты в Abyss.
"""
import logging
import time
import random
from typing import Optional
from core.sanderling.service import SanderlingService

logger = logging.getLogger(__name__)


def detect_room_type(sanderling: SanderlingService, timeout: float = 30.0) -> str:
    """
    Определить тип комнаты по наличию особых NPC.
    
    Алгоритм:
    1. Переключиться на Main
    2. Ждать 9.5-9.8 секунд (прогрузка комнаты)
    3. Ждать появления контейнера (не остова!)
    4. Ждать 0.5 секунды
    5. Проверить наличие особых NPC
    
    Args:
        sanderling: Сервис Sanderling
        timeout: Таймаут ожидания контейнера
        
    Returns:
        "tessera" - если найден Strikegrip Tessera
        "knight" - если найден Devoted Knight
        "overmind" - если найден Overmind или Tyrannos
        "vila" - если найден Vila (не Swarmer)
        "default" - стандартная комната
    """
    logger.info("Определение типа комнаты...")
    
    # Шаг 1: Переключиться на Main
    from bots.abyss_farmer.room_new import _switch_to_tab
    
    if not _switch_to_tab(sanderling, "Main"):
        logger.warning("Не удалось переключиться на Main, используем default")
        return "default"
    
    # Шаг 2: Ждать прогрузки комнаты (3.3-3.5 секунд)
    pause = random.uniform(3.3, 3.5)
    logger.info(f"Жду прогрузки комнаты {pause:.1f} секунд...")
    time.sleep(pause)
    
    # Шаг 3: Ждать появления контейнера (не остова!)
    cache_entry = _wait_for_cache_not_wreck(sanderling, timeout=timeout)
    if not cache_entry:
        logger.warning("Контейнер не появился, используем default")
        return "default"
    
    logger.info(f"Контейнер найден: {cache_entry.name}")
    
    # Шаг 4: Ждать 2 секунды чтобы цели прогрузились
    logger.info("Жду прогрузки целей (2 сек)...")
    time.sleep(2.0)
    
    # Шаг 5: Проверить наличие особых NPC
    state = sanderling.get_state()
    if not state or not state.overview:
        logger.warning("Нет данных overview, используем default")
        return "default"
    
    # Логируем все цели для отладки
    logger.debug(f"Цели в overview: {[entry.name for entry in state.overview if entry.name]}")
    
    # Проверяем каждую запись в overview
    for entry in state.overview:
        if not entry.name:
            continue
        
        name_lower = entry.name.lower()
        
        # Проверка на Strikegrip Tessera (частичное вхождение)
        if 'tessera' in name_lower:
            logger.info(f"Обнаружен Tessera: {entry.name}")
            return "tessera"
        
        # Проверка на Devoted Knight (ТОЛЬКО Knight, не Hunter!)
        if 'devoted' in name_lower and 'knight' in name_lower:
            logger.info(f"Обнаружен Devoted Knight: {entry.name}")
            return "knight"
        
        # Проверка на Vila (но не Swarmer)
        if 'vila' in name_lower and 'swarmer' not in name_lower:
            logger.info(f"Обнаружен Vila: {entry.name}")
            return "vila"
        
        # Проверка на Overmind/Tyrannos
        if 'overmind' in name_lower or 'tyrannos' in name_lower:
            logger.info(f"Обнаружен Overmind/Tyrannos: {entry.name}")
            return "overmind"
    
    # Если особых NPC не найдено - стандартная комната
    logger.info("Особых NPC не обнаружено - стандартная комната")
    return "default"


def _wait_for_cache_not_wreck(sanderling: SanderlingService, timeout: float) -> Optional:
    """
    Ждать появления контейнера (не остова!) в overview.
    
    Args:
        sanderling: Сервис Sanderling
        timeout: Таймаут ожидания (сек)
        
    Returns:
        OverviewEntry контейнера или None
    """
    from bots.abyss_farmer.room_new import _is_wreck
    
    start = time.time()
    
    while time.time() - start < timeout:
        state = sanderling.get_state()
        if not state or not state.overview:
            time.sleep(0.5)
            continue
        
        for entry in state.overview:
            if not entry.name:
                continue
            
            name_lower = entry.name.lower()
            
            # Проверяем что это cache и НЕ wreck
            if any(keyword in name_lower for keyword in ['cache', 'bioadaptive', 'biocombinative']):
                # Проверяем что это не остов
                if not _is_wreck(entry):
                    logger.debug(f"Найден контейнер (не остов): '{entry.name}'")
                    return entry
        
        time.sleep(0.5)
    
    logger.error("Контейнер не найден!")
    return None
