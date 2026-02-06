"""
Модуль для прохождения комнаты с Vila.

Особенности:
- Vila NPC выпускают дронов Vila Swarmer
- Свармеров НЕ убивать!
- Убивать только основные корабли с "Vila" (но не "Swarmer")
- Аппроч контейнера, убийство всех Vila, лут, прыжок
"""
import logging
import time
from typing import List, Optional
from core.sanderling.service import SanderlingService
from core.sanderling.models import OverviewEntry
from eve.mouse import click, random_delay
from eve.keyboard import press_key, key_down, key_up
from eve.modules import ensure_mid_slots_active

logger = logging.getLogger(__name__)


def vila_room(sanderling: SanderlingService, timeout: float = 300.0) -> bool:
    """
    Пройти комнату с Vila.
    
    Args:
        sanderling: Сервис Sanderling
        timeout: Максимальное время прохождения комнаты (сек)
        
    Returns:
        True если комната пройдена успешно
    """
    logger.info("=== НАЧАЛО ПРОХОЖДЕНИЯ КОМНАТЫ (VILA) ===")
    start_time = time.time()
    
    # 1. Переключиться на вкладку Main
    logger.info("Шаг 1: Переключение на вкладку Main...")
    if not _switch_to_tab(sanderling, "Main"):
        logger.error("Не удалось переключиться на вкладку Main")
        return False
    
    # 2. Проверить что мид слоты активны
    logger.info("Шаг 2: Проверка мид слотов...")
    ensure_mid_slots_active(sanderling_service=sanderling)
    random_delay(0.3, 0.5)
    
    # 3. Ждать появления контейнера
    logger.info("Шаг 3: Ожидание контейнера...")
    cache_entry = _wait_for_cache(sanderling, timeout=60.0)
    if not cache_entry:
        logger.error("Контейнер не появился")
        return False
    
    logger.info(f"Контейнер найден: {cache_entry.name}")
    
    # 4. Аппроч к контейнеру
    logger.info("Шаг 4: Аппроч к контейнеру...")
    if not _approach_target(sanderling, cache_entry):
        logger.error("Не удалось начать аппроч к контейнеру")
        return False
    
    # 5. Выпустить дронов
    logger.info("Шаг 5: Выпуск дронов...")
    _launch_drones()
    random_delay(1.5, 2.0)
    
    # 6. Переключиться на PvP Foe
    logger.info("Шаг 6: Переключение на PvP Foe...")
    if not _switch_to_tab(sanderling, "PvP Foe"):
        logger.error("Не удалось переключиться на PvP Foe")
        return False
    
    random_delay(1.2, 1.5)
    
    # 7. Убить всех Vila (но не Swarmer)
    logger.info("Шаг 7: Убийство всех Vila (исключая Swarmer)...")
    killed = _kill_all_vila_except_swarmers(sanderling)
    logger.info(f"Убито Vila: {killed}")
    
    # 8. Проверить что контейнер жив или остов
    logger.info("Шаг 8: Проверка контейнера...")
    if not _switch_to_tab(sanderling, "Main"):
        logger.error("Не удалось переключиться на Main")
        return False
    
    cache_entry = _wait_for_cache(sanderling, timeout=30.0)
    if not cache_entry:
        logger.error("Контейнер не найден")
        return False
    
    is_wreck = _is_wreck(cache_entry)
    
    if is_wreck:
        logger.info("Контейнер уже уничтожен (остов), пропускаю убийство...")
        random_delay(1.0, 1.5)
        if not _loot_wreck(sanderling):
            logger.warning("Не удалось залутать контейнер, продолжаю...")
    else:
        # 9. Убить контейнер
        logger.info("Шаг 9: Убийство контейнера...")
        if not _kill_cache(sanderling, cache_entry):
            logger.error("Не удалось убить контейнер")
            return False
        
        # 10. Лут контейнера
        logger.info("Шаг 10: Лут контейнера...")
        if not _loot_wreck(sanderling):
            logger.warning("Не удалось залутать контейнер, продолжаю...")
    
    # 11. Возврат дронов
    logger.info("Шаг 11: Возврат дронов...")
    if not _recall_drones(sanderling):
        logger.warning("Не удалось вернуть дронов")
    
    # 12. Переключиться на Main
    logger.info("Шаг 12: Переключение на Main...")
    if not _switch_to_tab(sanderling, "Main"):
        logger.error("Не удалось переключиться на Main")
        return False
    
    # 13. Прыжок через ворота
    logger.info("Шаг 13: Прыжок через ворота...")
    if not _jump_through_gate(sanderling):
        logger.error("Не удалось прыгнуть через ворота")
        return False
    
    elapsed = time.time() - start_time
    logger.info(f"=== КОМНАТА ПРОЙДЕНА ЗА {elapsed:.1f} СЕК ===")
    return True


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

from bots.abyss_farmer.room_new import (
    _switch_to_tab,
    _wait_for_cache,
    _approach_target,
    _recall_drones,
    _jump_through_gate,
    _is_wreck,
    _parse_distance_km
)


def _launch_drones():
    """
    Выпустить дронов (Shift+F).
    """
    logger.debug("Выпускаю дронов: Shift+F")
    
    try:
        key_down('shift')
        random_delay(0.15, 0.2)
        press_key('f')
        random_delay(0.15, 0.2)
    finally:
        key_up('shift')
    
    logger.info("Команда выпуска дронов отправлена")


def _kill_all_vila_except_swarmers(sanderling: SanderlingService) -> int:
    """
    Убить всех Vila, исключая Swarmer.
    
    Args:
        sanderling: Сервис Sanderling
        
    Returns:
        Количество убитых врагов
    """
    killed_count = 0
    max_iterations = 10
    
    for iteration in range(1, max_iterations + 1):
        logger.info(f"Проверка Vila (итерация {iteration}/{max_iterations})...")
        
        # Получить список Vila (не Swarmer)
        vila_enemies = _get_vila_enemies(sanderling)
        
        if not vila_enemies:
            logger.info("Все Vila убиты")
            break
        
        logger.info(f"Обнаружено Vila: {len(vila_enemies)}")
        
        # Убить волну
        wave_killed = _kill_vila_wave(sanderling, vila_enemies)
        killed_count += wave_killed
        
        random_delay(1.0, 1.5)
    
    return killed_count


def _get_vila_enemies(sanderling: SanderlingService) -> List[OverviewEntry]:
    """
    Получить список Vila врагов (исключая Swarmer).
    
    Args:
        sanderling: Сервис Sanderling
        
    Returns:
        Список Vila врагов
    """
    state = sanderling.get_state()
    if not state or not state.overview:
        return []
    
    vila_enemies = []
    
    for entry in state.overview:
        if not entry.name:
            continue
        
        name_lower = entry.name.lower()
        
        # Проверяем что есть "vila" но НЕТ "swarmer"
        if 'vila' in name_lower and 'swarmer' not in name_lower:
            vila_enemies.append(entry)
    
    return vila_enemies


def _kill_vila_wave(sanderling: SanderlingService, enemies: List[OverviewEntry]) -> int:
    """
    Убить волну Vila врагов.
    
    Args:
        sanderling: Сервис Sanderling
        enemies: Список врагов
        
    Returns:
        Количество убитых
    """
    if not enemies:
        return 0
    
    # Берем до 2 врагов
    targets = enemies[:2]
    
    logger.info(f"--- Волна: {len(targets)} врагов ---")
    
    # Лочим врагов
    logger.info("Лочу врагов...")
    for i, enemy in enumerate(targets, 1):
        logger.debug(f"  Ctrl+Click по врагу #{i}: {enemy.name}")
        key_down('ctrl')
        random_delay(0.05, 0.1)
        click(enemy.center[0], enemy.center[1], duration=0.12)
        random_delay(0.05, 0.1)
        key_up('ctrl')
        random_delay(0.3, 0.5)
    
    # Ждем лока
    logger.debug("Жду лока целей...")
    random_delay(2.8, 3.3)
    
    # Атакуем
    logger.info("Атакую (1 + F)...")
    press_key('1')
    random_delay(0.3, 0.5)
    press_key('f')
    random_delay(0.5, 0.8)
    
    # Ждем смерти
    logger.info("Жду смерти врагов...")
    if not _wait_targets_dead(sanderling, timeout=95.0):  # 95 секунд
        logger.warning("Таймаут ожидания смерти врагов")
        return 0
    
    return len(targets)


def _wait_targets_dead(sanderling: SanderlingService, timeout: float) -> bool:
    """
    Ждать пока все залоченные цели не умрут.
    
    Args:
        sanderling: Сервис Sanderling
        timeout: Таймаут ожидания (сек)
        
    Returns:
        True если все цели мертвы
    """
    start = time.time()
    last_f_press = start
    f_interval = 15.0
    
    while time.time() - start < timeout:
        state = sanderling.get_state()
        
        # Проверяем есть ли залоченные цели
        if not state or not state.targets or len(state.targets) == 0:
            logger.info("Все цели мертвы")
            return True
        
        # Дублируем F каждые 15 секунд
        current_time = time.time()
        if current_time - last_f_press >= f_interval:
            logger.debug("Дублирую команду F...")
            press_key('f')
            last_f_press = current_time
        
        time.sleep(1.0)
    
    return False


def _kill_cache(sanderling: SanderlingService, cache_entry: OverviewEntry) -> bool:
    """
    Убить контейнер.
    
    Args:
        sanderling: Сервис Sanderling
        cache_entry: Контейнер в overview
        
    Returns:
        True если успешно
    """
    # Ждать пока контейнер <= 35 км
    logger.info("Ожидание контейнера в радиусе <= 35 км...")
    if not _wait_target_in_range(sanderling, "cache", max_distance_km=35.0, timeout=60.0):
        logger.warning("Контейнер не подлетел в радиус 35 км")
    
    # Залочить контейнер
    logger.info("Лок контейнера...")
    if not _lock_target(sanderling, cache_entry):
        logger.error("Не удалось залочить контейнер")
        return False
    
    # Атаковать (1 + F)
    logger.info("Атака контейнера...")
    press_key('1')
    random_delay(0.3, 0.5)
    press_key('f')
    random_delay(0.5, 0.8)
    
    # Ждать смерти
    logger.info("Ожидание смерти контейнера...")
    if not _wait_cache_death(sanderling, timeout=95.0):  # 95 секунд
        logger.error("Контейнер не умер")
        return False
    
    logger.info("Контейнер уничтожен!")
    random_delay(1.0, 1.5)
    return True


def _wait_target_in_range(
    sanderling: SanderlingService,
    target_keyword: str,
    max_distance_km: float,
    timeout: float
) -> bool:
    """
    Ждать пока цель не окажется в радиусе <= max_distance_km.
    
    Args:
        sanderling: Сервис Sanderling
        target_keyword: Ключевое слово для поиска цели
        max_distance_km: Максимальная дистанция (км)
        timeout: Таймаут ожидания (сек)
        
    Returns:
        True если цель в радиусе
    """
    start = time.time()
    target_keyword_lower = target_keyword.lower()
    
    while time.time() - start < timeout:
        state = sanderling.get_state()
        if not state or not state.overview:
            time.sleep(0.5)
            continue
        
        for entry in state.overview:
            if not entry.name or not entry.distance:
                continue
            
            name_lower = entry.name.lower()
            if target_keyword_lower not in name_lower:
                continue
            
            distance_km = _parse_distance_km(entry.distance)
            if distance_km is None:
                continue
            
            if distance_km <= max_distance_km:
                logger.info(f"Цель в радиусе: {entry.name} на {distance_km:.1f} км")
                return True
        
        time.sleep(0.5)
    
    logger.warning(f"Цель не подлетела в радиус {max_distance_km} км за {timeout}с")
    return False


def _lock_target(sanderling: SanderlingService, target: OverviewEntry) -> bool:
    """
    Залочить цель (Ctrl+Click).
    
    Args:
        sanderling: Сервис Sanderling
        target: Цель в overview
        
    Returns:
        True если успешно
    """
    if not target.center:
        logger.error("У цели нет координат")
        return False
    
    logger.debug(f"Лочу цель @ {target.center}")
    key_down('ctrl')
    random_delay(0.05, 0.1)
    click(target.center[0], target.center[1], duration=0.12)
    random_delay(0.05, 0.1)
    key_up('ctrl')
    
    logger.debug("Жду появления цели в targets...")
    random_delay(2.8, 3.3)
    
    return True


def _wait_cache_death(sanderling: SanderlingService, timeout: float) -> bool:
    """
    Ждать смерти контейнера.
    
    Args:
        sanderling: Сервис Sanderling
        timeout: Таймаут ожидания (сек)
        
    Returns:
        True если контейнер умер
    """
    from bots.abyss_farmer.room_new import _wait_cache_death as wait_cache_death_impl
    return wait_cache_death_impl(sanderling, timeout)


def _loot_wreck(sanderling: SanderlingService) -> bool:
    """
    Залутать врек контейнера (таймаут 25 секунд).
    
    Args:
        sanderling: Сервис Sanderling
        
    Returns:
        True если успешно
    """
    # Шаг 1: Ждать появления врека
    logger.info("Жду появления врека...")
    wreck_entry = _wait_for_wreck(sanderling, timeout=10.0)
    if not wreck_entry:
        logger.error("Врек не появился")
        return False
    
    logger.info(f"Врек найден: {wreck_entry.name}")
    
    # Шаг 2: Кликнуть по вреку
    logger.info("Кликаю по вреку...")
    click(wreck_entry.center[0], wreck_entry.center[1], duration=0.18)
    random_delay(0.5, 0.8)
    
    # Шаг 3: Ждать кнопки approach
    logger.info("Жду кнопки approach...")
    approach_action = None
    for _ in range(6):
        state = sanderling.get_state()
        if state and state.selected_actions:
            approach_action = next((a for a in state.selected_actions if 'approach' in a.name.lower()), None)
            if approach_action:
                break
        time.sleep(0.5)
    
    if approach_action:
        logger.info("Кликаю approach...")
        click(approach_action.center[0], approach_action.center[1], duration=0.18)
        random_delay(0.5, 0.8)
    
    # Шаг 4: Открыть карго
    logger.info("Открываю карго врека...")
    for attempt in range(10):
        random_delay(0.5, 0.8)
        
        state = sanderling.get_state()
        if not state or not state.selected_actions:
            continue
        
        open_cargo = next((a for a in state.selected_actions if a.name == 'open_cargo'), None)
        if not open_cargo:
            continue
        
        logger.info("Кликаю open_cargo...")
        click(open_cargo.center[0], open_cargo.center[1], duration=0.18)
        random_delay(1.2, 1.5)
        break
    else:
        logger.error("Не удалось открыть карго врека")
        return False
    
    # Шаг 5: Ждать кнопки "Взять все"
    logger.info("Жду кнопки 'Взять все'...")
    for attempt in range(20):
        random_delay(1.2, 1.5)
        
        state = sanderling.get_state()
        if not state or not state.inventory or not state.inventory.loot_all_button:
            continue
        
        button_coords = state.inventory.loot_all_button
        logger.info(f"Кликаю 'Взять все' @ {button_coords}")
        click(button_coords[0], button_coords[1], duration=0.18)
        random_delay(1.2, 1.5)
        
        logger.info("Лут завершен")
        return True
    
    logger.warning("Не удалось найти кнопку 'Взять все' за 25 секунд, продолжаю...")
    return True


def _wait_for_wreck(sanderling: SanderlingService, timeout: float) -> Optional[OverviewEntry]:
    """
    Ждать появления врека в overview.
    
    Args:
        sanderling: Сервис Sanderling
        timeout: Таймаут ожидания (сек)
        
    Returns:
        OverviewEntry врека или None
    """
    start = time.time()
    
    while time.time() - start < timeout:
        state = sanderling.get_state()
        if not state or not state.overview:
            time.sleep(0.5)
            continue
        
        for entry in state.overview:
            if not entry.name:
                continue
            
            if _is_wreck(entry):
                logger.debug(f"Найден врек: '{entry.name}'")
                return entry
        
        time.sleep(0.5)
    
    logger.error("Врек не найден!")
    return None
