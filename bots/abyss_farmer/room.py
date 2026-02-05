"""
Модуль для прохождения комнаты в Abyss.
"""
import logging
import time
from core.sanderling.service import SanderlingService
from bots.abyss_farmer.cache import process_cache
from eve.mouse import random_delay
from eve.combat import recall_drones
from eve.overview_combat import clear_enemies

logger = logging.getLogger(__name__)


def room(sanderling: SanderlingService, timeout: float = 300.0) -> bool:
    """
    Пройти комнату в абиссе (с боевой логикой).
    
    Порядок действий:
    1. Ждать появления "Triglavian Cache" в overview
    2. Обработать контейнер (аппроч, атака ракетами, лут)
    3. Зачистить всех врагов (переключение на PvP Foe, выпуск дронов, лок + убийство)
    
    Args:
        sanderling: Сервис Sanderling
        timeout: Максимальное время прохождения комнаты (сек)
        
    Returns:
        True если комната пройдена успешно
    """
    logger.info("=== НАЧАЛО ПРОХОЖДЕНИЯ КОМНАТЫ ===")
    start_time = time.time()
    
    # 1. Ждать появления контейнера в overview
    logger.info("Ожидание появления Triglavian Cache...")
    cache_entry = _wait_for_cache(sanderling, timeout=60.0)
    if not cache_entry:
        logger.error("Контейнер не появился в overview")
        return False
    
    logger.info(f"Контейнер найден: {cache_entry.name} на {cache_entry.distance}")
    random_delay(0.5, 1.0)
    
    # 2. Обработать контейнер (аппроч, атака ракетами, лут)
    logger.info("Обработка контейнера (только ракеты)...")
    if not process_cache(
        sanderling,
        approach_timeout=120.0,
        kill_timeout=60.0,
        attack_distance_km=30.0,
        enable_mwd=True,
        launch_drones=False  # Дроны выпустим позже
    ):
        logger.error("Не удалось обработать контейнер")
        return False
    
    logger.info("Контейнер обработан!")
    random_delay(0.3, 0.5)  # Пауза перед зачисткой
    
    # 3. Зачистить всех врагов (переключение на PvP Foe + выпуск дронов внутри)
    logger.info("Зачистка врагов...")
    killed = clear_enemies(
        sanderling,
        guns_key="1",  # Ракеты
        drones_key="f",  # Дроны атакуют
        pvp_tab_name="PvP Foe",
        launch_drones_first=True  # Выпустить дронов перед зачисткой
    )
    
    if killed > 0:
        logger.info(f"Убито врагов: {killed}")
    else:
        logger.warning("Не удалось убить врагов (или их не было)")
    
    # 4. Вернуть дронов
    logger.info("Возвращаю дронов...")
    recall_drones()
    random_delay(0.3, 0.5)  # Пауза после возврата
    
    elapsed = time.time() - start_time
    logger.info(f"=== КОМНАТА ПРОЙДЕНА ЗА {elapsed:.1f} СЕК ===")
    return True


def _wait_for_cache(sanderling: SanderlingService, timeout: float) -> object:
    """
    Ждать появления Triglavian Cache (Bioadaptive/Biocombinative) в overview.
    
    Args:
        sanderling: Сервис Sanderling
        timeout: Таймаут ожидания (сек)
        
    Returns:
        OverviewEntry контейнера или None
    """
    start = time.time()
    last_log_time = 0
    
    while time.time() - start < timeout:
        state = sanderling.get_state()
        if not state or not state.overview:
            time.sleep(0.5)
            continue
        
        # Логируем что видим в overview каждые 10 секунд
        current_time = time.time()
        if current_time - last_log_time > 10:
            logger.info(f"В overview {len(state.overview)} записей:")
            for entry in state.overview[:5]:  # Первые 5
                logger.info(f"  - {entry.name} ({entry.type})")
            if len(state.overview) > 5:
                logger.info(f"  ... и еще {len(state.overview) - 5}")
            last_log_time = current_time
        
        # Ищем контейнер по имени (проверяем разные варианты)
        for entry in state.overview:
            if not entry.name:
                continue
            
            name_lower = entry.name.lower()
            
            # Проверяем разные варианты названия
            if any(keyword in name_lower for keyword in [
                'bioadaptive cache', 'biocombinative cache',
                'bioadaptive cache',
                'triglavian cache',
                'cache'
            ]):
                logger.info(f"Найден контейнер: '{entry.name}'")
                return entry
        
        time.sleep(0.5)
    
    # Финальный дамп если не нашли
    logger.error("Контейнер не найден! Финальный дамп overview:")
    state = sanderling.get_state()
    if state and state.overview:
        for entry in state.overview:
            logger.error(f"  - {entry.name} ({entry.type})")
    else:
        logger.error("  Overview пустой!")
    
    return None

