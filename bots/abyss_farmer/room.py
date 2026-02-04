"""
Модуль для прохождения комнаты в Abyss.
"""
import logging
import time
from core.sanderling.service import SanderlingService
from bots.abyss_farmer.cache import process_cache
from eve.mouse import random_delay

logger = logging.getLogger(__name__)


def room(sanderling: SanderlingService, timeout: float = 300.0) -> bool:
    """
    Пройти комнату в абиссе (дефолтная логика).
    
    Порядок действий:
    1. Ждать появления "Triglavian Bioadaptive Cache" в overview
    2. Обработать контейнер (аппроч, атака, лут)
    
    Args:
        sanderling: Сервис Sanderling
        timeout: Максимальное время прохождения комнаты (сек)
        
    Returns:
        True если комната пройдена успешно
    """
    logger.info("=== НАЧАЛО ПРОХОЖДЕНИЯ КОМНАТЫ ===")
    start_time = time.time()
    
    # Ждать появления контейнера в overview
    logger.info("Ожидание появления Triglavian Bioadaptive Cache...")
    cache_entry = _wait_for_cache(sanderling, timeout=60.0)
    if not cache_entry:
        logger.error("Контейнер не появился в overview")
        return False
    
    logger.info(f"Контейнер найден: {cache_entry.name} на {cache_entry.distance}")
    random_delay(0.5, 1.0)
    
    # Обработать контейнер (аппроч, атака, лут)
    logger.info("Обработка контейнера...")
    if not process_cache(
        sanderling,
        approach_timeout=120.0,
        kill_timeout=60.0,
        attack_distance_km=30.0,
        enable_mwd=True,
        launch_drones=True
    ):
        logger.error("Не удалось обработать контейнер")
        return False
    
    elapsed = time.time() - start_time
    logger.info(f"=== КОМНАТА ПРОЙДЕНА ЗА {elapsed:.1f} СЕК ===")
    return True


def _wait_for_cache(sanderling: SanderlingService, timeout: float) -> object:
    """
    Ждать появления Triglavian Bioadaptive Cache в overview.
    
    Args:
        sanderling: Сервис Sanderling
        timeout: Таймаут ожидания (сек)
        
    Returns:
        OverviewEntry контейнера или None
    """
    start = time.time()
    
    while time.time() - start < timeout:
        state = sanderling.get_state()
        if not state or not state.overview:
            time.sleep(0.5)
            continue
        
        # Ищем контейнер по имени
        for entry in state.overview:
            if entry.name and 'Triglavian Bioadaptive Cache' in entry.name:
                return entry
        
        time.sleep(0.5)
    
    return None
