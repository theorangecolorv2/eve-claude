"""
Модуль для прохождения комнаты с Overmind/Tyrannos.

Особенности:
- Аппроч контейнера, выпуск дронов
- Лок врага (Overmind/Tyrannos), отправка дронов (F)
- Лок контейнера, переключение на него в targets, атака ракетами (1)
- Дроны бьют врага, ракеты бьют контейнер одновременно
- После смерти контейнера - лут
- Орбита врага 500м, атака ракетами (1) + дронами (F каждые 15 сек)
- После смерти врага - орбита гейта, проверка врагов, возврат дронов, прыжок
"""
import logging
import time
from typing import Optional
from core.sanderling.service import SanderlingService
from core.sanderling.models import OverviewEntry, Target
from eve.mouse import click, random_delay
from eve.keyboard import press_key, key_down, key_up
from eve.modules import ensure_mid_slots_active

logger = logging.getLogger(__name__)


def overmind_room(sanderling: SanderlingService, timeout: float = 300.0) -> bool:
    """
    Пройти комнату с Overmind/Tyrannos.
    
    Args:
        sanderling: Сервис Sanderling
        timeout: Максимальное время прохождения комнаты (сек)
        
    Returns:
        True если комната пройдена успешно
    """
    logger.info("=== НАЧАЛО ПРОХОЖДЕНИЯ КОМНАТЫ (OVERMIND/TYRANNOS) ===")
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
    
    # 6. Найти Overmind/Tyrannos
    logger.info("Шаг 6: Поиск Overmind/Tyrannos...")
    enemy = _find_overmind_or_tyrannos(sanderling)
    if not enemy:
        logger.error("Overmind/Tyrannos не найден")
        return False
    
    logger.info(f"Враг найден: {enemy.name}")
    
    # 7. Ждать пока враг <= 35 км
    logger.info("Шаг 7: Ожидание врага в радиусе <= 35 км...")
    if not _wait_target_in_range(sanderling, enemy.name, max_distance_km=35.0, timeout=60.0):
        logger.warning("Враг не подлетел в радиус 35 км")
    
    # 8. Залочить врага
    logger.info("Шаг 8: Лок врага...")
    if not _lock_target(sanderling, enemy):
        logger.error("Не удалось залочить врага")
        return False
    
    # 9. Отправить дронов на врага (F)
    logger.info("Шаг 9: Отправка дронов на врага (F)...")
    press_key('f')
    random_delay(0.5, 0.8)
    
    # 10. Залочить контейнер
    logger.info("Шаг 10: Лок контейнера...")
    if not _lock_target(sanderling, cache_entry):
        logger.error("Не удалось залочить контейнер")
        return False
    
    # 11. Выбрать контейнер в overview и атаковать ракетами
    logger.info("Шаг 11: Переключение на контейнер и атака ракетами...")
    if not _select_and_attack_cache_in_overview(sanderling, cache_entry):
        logger.error("Не удалось атаковать контейнер")
        return False
    
    logger.info("Дроны бьют врага, ракеты бьют контейнер...")
    
    # 12. Ждать смерти контейнера
    logger.info("Шаг 12: Ожидание смерти контейнера...")
    if not _wait_cache_death(sanderling, timeout=60.0):
        logger.error("Контейнер не умер")
        return False
    
    logger.info("Контейнер уничтожен!")
    random_delay(1.0, 1.5)
    
    # 13. Лут контейнера
    logger.info("Шаг 13: Лут контейнера...")
    if not _loot_wreck(sanderling):
        logger.warning("Не удалось залутать контейнер, продолжаю...")
    
    # 14. Найти врага в overview/targets и выйти на орбиту 500м
    logger.info("Шаг 14: Орбита врага 500м...")
    if not _orbit_enemy_500m(sanderling, enemy):
        logger.error("Не удалось выйти на орбиту врага")
        return False
    
    # 15. Проверить что ракеты inactive, атаковать ракетами
    logger.info("Шаг 15: Проверка inactive ракет и атака...")
    if not _wait_for_guns_inactive(sanderling, timeout=15.0):
        logger.warning("Ракеты не стали inactive, продолжаю...")
    
    press_key('1')
    random_delay(0.5, 0.8)
    
    # 16. Ждать смерти врага с периодическим нажатием F
    logger.info("Шаг 16: Ожидание смерти врага...")
    if not _kill_enemy_with_periodic_f(sanderling, enemy_name=enemy.name):
        logger.error("Не удалось убить врага")
        return False
    
    logger.info("Враг убит!")
    
    # 17. Орбита гейта
    logger.info("Шаг 17: Орбита гейта...")
    if not _orbit_gate(sanderling):
        logger.error("Не удалось выйти на орбиту гейта")
        return False
    
    random_delay(0.3, 0.4)
    
    # 18. Переключиться на PvP Foe
    if not _switch_to_tab(sanderling, "PvP Foe"):
        logger.error("Не удалось переключиться на PvP Foe")
        return False
    
    random_delay(1.2, 1.5)
    
    # 19. Проверка зачистки врагов
    logger.info("Шаг 19: Проверка зачистки врагов...")
    if not _ensure_all_enemies_cleared(sanderling):
        logger.error("Не удалось зачистить всех врагов")
        return False
    
    # 20. Возврат дронов
    logger.info("Шаг 20: Возврат дронов...")
    if not _recall_drones(sanderling):
        logger.warning("Не удалось вернуть дронов")
    
    # 21. Переключиться на Main
    logger.info("Шаг 21: Переключение на Main...")
    if not _switch_to_tab(sanderling, "Main"):
        logger.error("Не удалось переключиться на Main")
        return False
    
    # 22. Прыжок через ворота
    logger.info("Шаг 22: Прыжок через ворота...")
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
    _wait_cache_death,
    _orbit_gate,
    _ensure_all_enemies_cleared,
    _recall_drones,
    _jump_through_gate,
    _parse_distance_km,
    _wait_for_guns_inactive,
    _is_wreck
)


def _find_overmind_or_tyrannos(sanderling: SanderlingService) -> Optional[OverviewEntry]:
    """
    Найти Overmind или Tyrannos в overview.
    
    Args:
        sanderling: Сервис Sanderling
        
    Returns:
        OverviewEntry или None
    """
    state = sanderling.get_state()
    if not state or not state.overview:
        return None
    
    for entry in state.overview:
        if not entry.name:
            continue
        
        name_lower = entry.name.lower()
        if 'overmind' in name_lower or 'tyrannos' in name_lower:
            return entry
    
    return None


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


def _wait_target_in_range(
    sanderling: SanderlingService,
    target_name: str,
    max_distance_km: float,
    timeout: float
) -> bool:
    """
    Ждать пока цель не окажется в радиусе <= max_distance_km.
    
    Args:
        sanderling: Сервис Sanderling
        target_name: Имя цели для поиска
        max_distance_km: Максимальная дистанция (км)
        timeout: Таймаут ожидания (сек)
        
    Returns:
        True если цель в радиусе
    """
    start = time.time()
    target_name_lower = target_name.lower()
    
    while time.time() - start < timeout:
        state = sanderling.get_state()
        if not state or not state.overview:
            time.sleep(0.5)
            continue
        
        for entry in state.overview:
            if not entry.name or not entry.distance:
                continue
            
            name_lower = entry.name.lower()
            if target_name_lower not in name_lower:
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
    
    # Ждем появления в targets
    logger.debug("Жду появления цели в targets...")
    random_delay(2.8, 3.3)
    
    return True


def _select_and_attack_cache_in_overview(sanderling: SanderlingService, cache_entry: OverviewEntry) -> bool:
    """
    Кликнуть по контейнеру в overview и атаковать ракетами (1).
    
    Args:
        sanderling: Сервис Sanderling
        cache_entry: Контейнер в overview
        
    Returns:
        True если успешно
    """
    if not cache_entry.center:
        logger.error("У контейнера нет координат")
        return False
    
    logger.info(f"Кликаю по контейнеру в overview: {cache_entry.name}")
    logger.debug(f"Координаты @ {cache_entry.center}")
    
    # Кликаем по контейнеру в overview
    click(cache_entry.center[0], cache_entry.center[1], duration=0.18)
    random_delay(0.5, 0.8)
    
    # Активируем ракеты
    logger.info("Активирую ракеты на контейнер...")
    press_key('1')
    random_delay(0.5, 0.8)
    
    return True


def _orbit_enemy_500m(sanderling: SanderlingService, enemy: OverviewEntry) -> bool:
    """
    Выйти на орбиту 500м вокруг врага.
    
    Args:
        sanderling: Сервис Sanderling
        enemy: Враг в overview
        
    Returns:
        True если успешно
    """
    # Враг уже залочен, можем кликнуть по нему в overview или targets
    # Проще кликнуть в overview
    if not enemy.center:
        logger.error("У врага нет координат")
        return False
    
    logger.debug(f"Кликаю по врагу @ {enemy.center}")
    click(enemy.center[0], enemy.center[1], duration=0.18)
    random_delay(0.5, 0.8)
    
    # Ждать появления кнопки orbit
    orbit_action = None
    for _ in range(6):
        state = sanderling.get_state()
        if state and state.selected_actions:
            orbit_action = next((a for a in state.selected_actions if 'orbit' in a.name.lower()), None)
            if orbit_action:
                break
        time.sleep(0.5)
    
    if not orbit_action:
        logger.error("Кнопка 'orbit' не найдена")
        return False
    
    logger.debug(f"Кликаю 'orbit' @ {orbit_action.center}")
    click(orbit_action.center[0], orbit_action.center[1], duration=0.18)
    random_delay(0.5, 0.8)
    
    logger.info("Орбита 500м установлена")
    return True


def _kill_enemy_with_periodic_f(sanderling: SanderlingService, enemy_name: str) -> bool:
    """
    Ждать смерти врага с периодическим нажатием F (каждые 15 секунд).
    
    Args:
        sanderling: Сервис Sanderling
        enemy_name: Имя врага (для логов)
        
    Returns:
        True если враг убит
    """
    start = time.time()
    last_f_press = start
    kill_timeout = 180.0  # 3 минуты
    f_interval = 15.0  # Дублируем F каждые 15 секунд
    
    while time.time() - start < kill_timeout:
        # Проверяем жив ли враг (есть ли он в targets)
        state = sanderling.get_state()
        if not state or not state.targets:
            elapsed = time.time() - start
            logger.info(f"Враг убит за {elapsed:.1f}с")
            return True
        
        # Проверяем есть ли враг среди залоченных
        enemy_alive = False
        for target in state.targets:
            if not target.name:
                continue
            
            name_lower = target.name.lower()
            enemy_name_lower = enemy_name.lower()
            
            if enemy_name_lower in name_lower or 'overmind' in name_lower or 'tyrannos' in name_lower:
                enemy_alive = True
                break
        
        if not enemy_alive:
            elapsed = time.time() - start
            logger.info(f"Враг убит за {elapsed:.1f}с")
            return True
        
        # Дублируем команду F каждые 15 секунд
        current_time = time.time()
        if current_time - last_f_press >= f_interval:
            logger.debug("Дублирую команду F...")
            press_key('f')
            last_f_press = current_time
        
        time.sleep(1.0)
    
    logger.error(f"Таймаут {kill_timeout}с на убийство врага")
    return False


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
    
    # Шаг 4: Открыть карго (врек уже выбран после approach)
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
    
    # Шаг 5: Ждать кнопки "Взять все" (25 секунд)
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
