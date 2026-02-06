"""
Новый модуль для прохождения комнаты в Abyss (default room).

Пайплайн:
1. Переключиться на вкладку Main
2. Проверить что мид слоты активны
3. Ждать появления контейнера (Triglavian Bioadaptive Cache)
4. Кликнуть на контейнер, ждать кнопки "approach"
5. Кликнуть на approach
6. Выпустить дронов (Shift+F)
7. Переключиться на вкладку PvP Foe, ждать появления целей
8. Ждать пока любая цель не окажется на расстоянии <= 35км
9. Залочить первую цель в 35км, ждать лока, убить (1 + F)
10. Ждать смерти цели (исчезновение из targets)
11. Переключиться на Main, ждать контейнера в овере
12. Залочить контейнер, ждать inactive ракет, нажать 1
13. Ждать смерти контейнера, ждать врека
14. Кликнуть по вреку, approach, открыть карго (БЕЗ повторного клика на врек), взять все
15. Кликнуть на Gate/Conduit, orbit
16. Переключиться на PvP Foe через 0.3с
17. Убивать все цели в PvP Foe (лок + F + 1)
18. Собрать дронов (Shift+R), дождаться возврата всех дронов
19. Прыгнуть через ворота (Jump)
"""
import logging
import time
import re
from typing import Optional
from core.sanderling.service import SanderlingService
from core.sanderling.models import OverviewEntry
from eve.mouse import click, random_delay
from eve.keyboard import press_key, key_down, key_up
from eve.modules import ensure_mid_slots_active

logger = logging.getLogger(__name__)


def default_room(sanderling: SanderlingService, timeout: float = 300.0) -> bool:
    """
    Пройти стандартную комнату в абиссе.
    
    Args:
        sanderling: Сервис Sanderling
        timeout: Максимальное время прохождения комнаты (сек)
        
    Returns:
        True если комната пройдена успешно
    """
    logger.info("=== НАЧАЛО ПРОХОЖДЕНИЯ КОМНАТЫ (DEFAULT) ===")
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
    
    # 4-5. Кликнуть на контейнер и выбрать approach
    logger.info("Шаг 4-5: Аппроч к контейнеру...")
    if not _approach_target(sanderling, cache_entry):
        logger.error("Не удалось начать аппроч к контейнеру")
        return False
    
    # 6. Выпустить дронов
    logger.info("Шаг 6: Выпуск дронов...")
    _launch_drones_manual()
    random_delay(1.5, 2.0)
    
    # 7. Переключиться на PvP Foe и ждать целей
    logger.info("Шаг 7: Переключение на PvP Foe...")
    if not _switch_to_tab(sanderling, "PvP Foe"):
        logger.error("Не удалось переключиться на PvP Foe")
        return False
    
    # Ждем обновления данных от Sanderling
    logger.debug("Жду обновления данных от Sanderling...")
    random_delay(1.2, 1.5)
    
    logger.info("Ожидание появления целей...")
    if not _wait_for_enemies(sanderling, timeout=30.0):
        logger.warning("Цели не появились")
    
    # 8-10. Ждать цель в 35км, залочить и убить первую
    logger.info("Шаг 8-10: Убийство первой цели...")
    if not _kill_first_enemy_in_range(sanderling, max_distance_km=35.0, timeout=60.0):
        logger.warning("Не удалось убить первую цель")
    
    # 11-14. Переключиться на Main, убить контейнер, залутать
    logger.info("Шаг 11-14: Уничтожение контейнера и лут...")
    if not _kill_and_loot_cache(sanderling):
        logger.error("Не удалось убить/залутать контейнер")
        return False
    
    # 15-16. Кликнуть на Gate/Conduit, orbit, переключиться на PvP Foe
    logger.info("Шаг 15-16: Орбита гейта...")
    if not _orbit_gate(sanderling):
        logger.error("Не удалось выйти на орбиту гейта")
        return False
    
    random_delay(0.3, 0.4)
    
    if not _switch_to_tab(sanderling, "PvP Foe"):
        logger.error("Не удалось переключиться на PvP Foe после гейта")
        return False
    
    # Ждем обновления данных от Sanderling
    logger.debug("Жду обновления данных от Sanderling...")
    random_delay(1.2, 1.5)
    
    # 17. Убить все цели в PvP Foe
    logger.info("Шаг 17: Зачистка оставшихся врагов...")
    if not _ensure_all_enemies_cleared(sanderling):
        logger.error("Не удалось зачистить всех врагов")
        return False
    
    # 18. Собрать дронов
    logger.info("Шаг 18: Возврат дронов...")
    if not _recall_drones(sanderling):
        logger.warning("Не удалось вернуть дронов")
    
    # 19. Переключиться на Main перед поиском ворот
    logger.info("Шаг 19: Переключение на Main...")
    if not _switch_to_tab(sanderling, "Main"):
        logger.error("Не удалось переключиться на Main")
        return False
    
    # 20. Прыгнуть через ворота
    logger.info("Шаг 20: Прыжок через ворота...")
    if not _jump_through_gate(sanderling):
        logger.error("Не удалось прыгнуть через ворота")
        return False
    
    elapsed = time.time() - start_time
    logger.info(f"=== КОМНАТА ПРОЙДЕНА ЗА {elapsed:.1f} СЕК ===")
    return True


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def _switch_to_tab(sanderling: SanderlingService, tab_name: str) -> bool:
    """
    Переключиться на вкладку overview.
    
    Args:
        sanderling: Сервис Sanderling
        tab_name: Название вкладки (сначала ищет точное совпадение, потом частичное)
        
    Returns:
        True если успешно
    """
    logger.debug(f"Переключаюсь на вкладку '{tab_name}'...")
    
    state = sanderling.get_state()
    if not state or not state.overview_tabs:
        logger.error("Нет данных о вкладках overview")
        return False
    
    # Очищаем искомое имя
    import re
    tab_name_clean = ''.join(c for c in tab_name if c.isalnum() or c.isspace()).strip().lower()
    
    # Сначала ищем ТОЧНОЕ совпадение
    target_tab = None
    for tab in state.overview_tabs:
        # Убираем HTML теги и спецсимволы из label
        label_clean = re.sub(r'<[^>]+>', '', tab.label)
        label_clean = ''.join(c for c in label_clean if c.isalnum() or c.isspace())
        label_clean = label_clean.strip().lower()
        
        if label_clean == tab_name_clean:
            target_tab = tab
            logger.debug(f"Найдено точное совпадение: '{tab_name}'")
            break
    
    # Если не нашли точное - ищем частичное
    if not target_tab:
        for tab in state.overview_tabs:
            label_clean = re.sub(r'<[^>]+>', '', tab.label)
            label_clean = ''.join(c for c in label_clean if c.isalnum() or c.isspace())
            label_clean = label_clean.strip().lower()
            
            if tab_name_clean in label_clean:
                target_tab = tab
                logger.debug(f"Найдено частичное совпадение: '{tab_name}'")
                break
    
    if not target_tab:
        logger.error(f"Вкладка '{tab_name}' не найдена")
        logger.error(f"Доступные вкладки: {[t.label for t in state.overview_tabs]}")
        return False
    
    # Кликаем по вкладке
    logger.debug(f"Кликаю по вкладке '{tab_name}' @ {target_tab.center}")
    click(target_tab.center[0], target_tab.center[1], duration=0.18)  # Было 0.15, +20%
    random_delay(0.5, 0.6)
    
    return True


def _wait_for_cache(sanderling: SanderlingService, timeout: float) -> Optional[OverviewEntry]:
    """
    Ждать появления контейнера в overview.
    
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
        
        # Ищем контейнер
        for entry in state.overview:
            if not entry.name:
                continue
            
            name_lower = entry.name.lower()
            
            # TODO: уточнить точное название контейнера
            if any(keyword in name_lower for keyword in [
                'bioadaptive cache',
                'biocombinative cache',
                'triglavian cache',
                'cache'
            ]):
                logger.debug(f"Найден контейнер: '{entry.name}'")
                return entry
        
        time.sleep(0.5)
    
    logger.error("Контейнер не найден!")
    return None


def _approach_target(sanderling: SanderlingService, target: OverviewEntry) -> bool:
    """
    Кликнуть на цель и выбрать approach.
    
    Args:
        sanderling: Сервис Sanderling
        target: Цель в overview
        
    Returns:
        True если успешно
    """
    # Кликнуть по цели
    if not target.center:
        logger.error("У цели нет координат")
        return False
    
    logger.debug(f"Кликаю по цели @ {target.center}")
    click(target.center[0], target.center[1], duration=0.18)
    random_delay(0.5, 0.8)
    
    # Ждать появления кнопки approach
    approach_action = None
    for _ in range(6):  # 6 попыток по 0.5 сек = 3 сек
        state = sanderling.get_state()
        if state and state.selected_actions:
            approach_action = next((a for a in state.selected_actions if 'approach' in a.name.lower()), None)
            if approach_action:
                break
        time.sleep(0.5)
    
    if not approach_action:
        logger.error("Кнопка 'approach' не найдена")
        return False
    
    logger.debug(f"Кликаю 'approach' @ {approach_action.center}")
    click(approach_action.center[0], approach_action.center[1], duration=0.18)
    random_delay(0.3, 0.5)
    
    return True


def _orbit_target(sanderling: SanderlingService, target: OverviewEntry) -> bool:
    """
    Кликнуть на цель и выбрать orbit.
    
    Args:
        sanderling: Сервис Sanderling
        target: Цель в overview
        
    Returns:
        True если успешно
    """
    # Кликнуть по цели
    if not target.center:
        logger.error("У цели нет координат")
        return False
    
    logger.debug(f"Кликаю по цели @ {target.center}")
    click(target.center[0], target.center[1], duration=0.18)  # Было 0.15, +20%
    random_delay(0.5, 0.8)
    
    # Ждать появления кнопки orbit
    orbit_action = None
    for _ in range(6):  # 6 попыток по 0.5 сек = 3 сек
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
    random_delay(0.3, 0.5)
    
    return True


def _launch_drones_manual():
    """
    Выпустить дронов (Shift+F).
    """
    logger.debug("Выпускаю дронов: Shift+F")
    
    try:
        # Зажимаем Shift
        key_down('shift')
        random_delay(0.15, 0.2)
        
        # Нажимаем F
        press_key('f')
        random_delay(0.15, 0.2)
        
    finally:
        # ОБЯЗАТЕЛЬНО отпускаем Shift
        key_up('shift')
    
    logger.info("Дроны выпущены")
    random_delay(0.5, 0.8)


def _wait_for_enemies(sanderling: SanderlingService, timeout: float) -> bool:
    """
    Ждать появления целей в overview.
    
    Args:
        sanderling: Сервис Sanderling
        timeout: Таймаут ожидания (сек)
        
    Returns:
        True если цели появились
    """
    start = time.time()
    
    while time.time() - start < timeout:
        state = sanderling.get_state()
        if state and state.overview and len(state.overview) > 0:
            logger.debug(f"Появились цели: {len(state.overview)}")
            return True
        time.sleep(0.5)
    
    return False


def _kill_first_enemy_in_range(
    sanderling: SanderlingService,
    max_distance_km: float,
    timeout: float
) -> bool:
    """
    Ждать пока любая цель не окажется в радиусе <= 35км, залочить и убить.
    
    Args:
        sanderling: Сервис Sanderling
        max_distance_km: Максимальная дистанция (км)
        timeout: Таймаут ожидания (сек)
        
    Returns:
        True если успешно убили
    """
    logger.info(f"Жду цель в радиусе <= {max_distance_km} км...")
    start = time.time()
    
    # Шаг 1: Ждать пока цель не окажется в радиусе
    target_entry = None
    while time.time() - start < timeout:
        state = sanderling.get_state()
        if not state or not state.overview:
            time.sleep(0.5)
            continue
        
        # Ищем первую цель в радиусе
        for entry in state.overview:
            if not entry.distance:
                continue
            
            distance_km = _parse_distance_km(entry.distance)
            if distance_km is None:
                continue
            
            if distance_km <= max_distance_km:
                target_entry = entry
                logger.info(f"Цель в радиусе: {entry.name} на {distance_km:.1f} км")
                break
        
        if target_entry:
            break
        
        time.sleep(0.5)
    
    if not target_entry:
        logger.warning(f"Цель не появилась в радиусе {max_distance_km} км за {timeout}с")
        return False
    
    # Шаг 2: Залочить цель (Ctrl+Click)
    logger.info("Лочу цель...")
    key_down('ctrl')
    random_delay(0.05, 0.1)
    click(target_entry.center[0], target_entry.center[1], duration=0.12)  # Быстрый клик для лока
    random_delay(0.05, 0.1)
    key_up('ctrl')
    
    # Шаг 3: Ждать появления в targets
    logger.info("Жду появления цели в targets...")
    random_delay(2.5, 3.0)  # Было 2.0-2.5, +0.5
    
    # Шаг 4: Убить (1 + F)
    logger.info("Убиваю цель (1 + F)...")
    press_key('1')  # Ракеты
    random_delay(0.3, 0.5)
    press_key('f')  # Дроны атакуют
    random_delay(0.3, 0.5)
    
    # Шаг 5: Ждать смерти (исчезновение из targets)
    logger.info("Жду смерти цели...")
    start = time.time()
    kill_timeout = 60.0
    
    while time.time() - start < kill_timeout:
        state = sanderling.get_state()
        
        # Если targets пустой - цель умерла
        if not state or not state.targets or len(state.targets) == 0:
            elapsed = time.time() - start
            logger.info(f"Цель убита за {elapsed:.1f}с")
            return True
        
        time.sleep(1.0)
    
    logger.warning(f"Таймаут {kill_timeout}с на убийство цели")
    return False


def _kill_and_loot_cache(sanderling: SanderlingService) -> bool:
    """
    Переключиться на Main, убить контейнер, залутать врек.
    
    Args:
        sanderling: Сервис Sanderling
        
    Returns:
        True если успешно
    """
    # Шаг 1: Переключиться на Main
    logger.info("Переключаюсь на Main...")
    if not _switch_to_tab(sanderling, "Main"):
        logger.error("Не удалось переключиться на Main")
        return False
    
    # Шаг 2: Ждать появления контейнера в overview
    logger.info("Жду появления контейнера в overview...")
    cache_entry = _wait_for_cache(sanderling, timeout=30.0)
    if not cache_entry:
        logger.error("Контейнер не появился в overview")
        return False
    
    logger.info(f"Контейнер найден: {cache_entry.name}")
    
    # Проверяем это остов или живой контейнер
    is_wreck = _is_wreck(cache_entry)
    
    if is_wreck:
        logger.info("Контейнер уже уничтожен (остов), пропускаю убийство...")
        random_delay(1.0, 1.5)
        # Сразу переходим к луту
        if not _loot_wreck_direct(sanderling, cache_entry):
            logger.warning("Не удалось залутать остов, продолжаю...")
        return True
    
    # Шаг 3: Залочить контейнер (Ctrl+Click)
    logger.info("Лочу контейнер...")
    key_down('ctrl')
    random_delay(0.05, 0.1)
    click(cache_entry.center[0], cache_entry.center[1], duration=0.12)  # Быстрый клик для лока
    random_delay(0.05, 0.1)
    key_up('ctrl')
    
    # Шаг 4: Ждать появления в targets
    logger.info("Жду появления контейнера в targets...")
    random_delay(2.5, 3.0)  # Было 2.0-2.5, +0.5
    
    # Шаг 5: Проверить что ракеты (модуль верхнего слота) inactive
    logger.info("Проверяю что ракеты inactive...")
    if not _wait_for_guns_inactive(sanderling, timeout=15.0):
        logger.warning("Ракеты не стали inactive, продолжаю...")
    
    # Шаг 6: Нажать 1 (ракеты)
    logger.info("Активирую ракеты...")
    press_key('1')
    random_delay(0.5, 0.8)
    
    # Шаг 7: Ждать смерти контейнера
    logger.info("Жду смерти контейнера...")
    if not _wait_cache_death(sanderling, timeout=60.0):
        logger.error("Контейнер не умер")
        return False
    
    logger.info("Контейнер уничтожен!")
    random_delay(1.0, 1.5)
    
    # Шаг 8: Ждать появления врека
    logger.info("Жду появления врека...")
    wreck_entry = _wait_for_wreck(sanderling, timeout=10.0)
    if not wreck_entry:
        logger.error("Врек не появился")
        return False
    
    logger.info(f"Врек найден: {wreck_entry.name}")
    
    # Шаг 9: Кликнуть по вреку
    logger.info("Кликаю по вреку...")
    click(wreck_entry.center[0], wreck_entry.center[1], duration=0.18)
    random_delay(0.5, 0.8)
    
    # Шаг 10: Ждать кнопки действий, кликнуть approach
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
    
    # Шаг 11: Открыть карго врека (врек уже выбран после approach, не нужно кликать снова)
    logger.info("Открываю карго врека...")
    for attempt in range(10):
        # Небольшая пауза после approach
        random_delay(0.5, 0.8)
        
        state = sanderling.get_state()
        if not state or not state.selected_actions:
            continue
        
        # Ищем кнопку open_cargo
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
    
    # Шаг 12: Ждать появления кнопки "Взять все"
    logger.info("Жду кнопки 'Взять все'...")
    for attempt in range(20):  # Было 15, стало 20 (25 секунд)
        random_delay(1.2, 1.5)
        
        state = sanderling.get_state()
        if not state or not state.inventory or not state.inventory.loot_all_button:
            continue
        
        # Кликаем "Взять все"
        button_coords = state.inventory.loot_all_button
        logger.info(f"Кликаю 'Взять все' @ {button_coords}")
        click(button_coords[0], button_coords[1], duration=0.18)
        random_delay(1.2, 1.5)
        
        logger.info("Лут завершен")
        return True
    
    logger.warning("Не удалось найти кнопку 'Взять все' за 25 секунд, продолжаю...")
    return True  # Продолжаем выполнение


def _orbit_gate(sanderling: SanderlingService) -> bool:
    """
    Найти Gate/Conduit и выйти на орбиту.
    
    Args:
        sanderling: Сервис Sanderling
        
    Returns:
        True если успешно
    """
    # Шаг 1: Найти Gate/Conduit в overview
    logger.info("Ищу Gate/Conduit...")
    gate_entry = _wait_for_gate(sanderling, timeout=10.0)
    if not gate_entry:
        logger.error("Gate/Conduit не найден")
        return False
    
    logger.info(f"Gate/Conduit найден: {gate_entry.name}")
    
    # Шаг 2: Кликнуть на Gate/Conduit и выбрать orbit
    return _orbit_target(sanderling, gate_entry)


def _clear_all_enemies(sanderling: SanderlingService) -> int:
    """
    Убить все цели в PvP Foe (лок + F + 1).
    
    Args:
        sanderling: Сервис Sanderling
        
    Returns:
        Количество убитых врагов
    """
    logger.info("Зачистка всех врагов...")
    
    total_killed = 0
    max_waves = 10
    wave = 0
    
    while wave < max_waves:
        wave += 1
        
        # Проверяем есть ли враги в overview
        state = sanderling.get_state()
        if not state or not state.overview or len(state.overview) == 0:
            logger.info(f"Нет врагов в overview - зачистка завершена! Убито: {total_killed}")
            break
        
        enemies_count = len(state.overview)
        logger.info(f"--- Волна {wave}: {enemies_count} врагов ---")
        
        # Лочим до 5 целей (Ctrl+Click по каждой)
        logger.info("Лочу врагов...")
        key_down('ctrl')
        random_delay(0.15, 0.25)
        
        to_lock = min(5, enemies_count)
        for i in range(to_lock):
            enemy = state.overview[i]
            if not enemy.center:
                continue
            
            logger.debug(f"  Ctrl+Click по врагу #{i+1}: {enemy.name}")
            click(enemy.center[0], enemy.center[1], duration=0.12)  # Быстрый клик для лока
            random_delay(0.3, 0.4)
        
        key_up('ctrl')
        
        # Ждем пока залочатся
        logger.info("Жду лока...")
        random_delay(2.8, 3.3)  # Было 2.5-3.0, +0.3
        
        # Убиваем залоченных (по одному)
        state = sanderling.get_state()
        if not state or not state.targets:
            logger.warning("Нет залоченных целей")
            break
        
        locked_count = len(state.targets)
        logger.info(f"Залочено {locked_count} целей, убиваю...")
        
        for i in range(locked_count):
            # Проверяем есть ли еще цели
            state = sanderling.get_state()
            if not state or not state.targets or len(state.targets) == 0:
                logger.info("Лок пустой")
                break
            
            logger.info(f"Убиваю цель {i+1}/{locked_count}...")
            
            # Активируем ракеты + дроны
            press_key('1')
            random_delay(0.3, 0.5)
            press_key('f')
            random_delay(0.3, 0.5)
            
            # Ждем смерти (уменьшение количества targets)
            current_targets = len(state.targets)
            start = time.time()
            kill_timeout = 60.0
            
            while time.time() - start < kill_timeout:
                state = sanderling.get_state()
                
                if not state or not state.targets:
                    logger.info("Цель убита - лок пустой")
                    total_killed += 1
                    break
                
                new_count = len(state.targets)
                if new_count < current_targets:
                    elapsed = time.time() - start
                    logger.info(f"Цель убита за {elapsed:.1f}с")
                    total_killed += 1
                    break
                
                time.sleep(1.0)
            else:
                logger.warning(f"Таймаут на цель {i+1}")
                break
            
            random_delay(0.3, 0.6)
        
        logger.info(f"Волна {wave} завершена, убито в волне: {locked_count}, всего: {total_killed}")
        random_delay(0.5, 1.0)
    
    if wave >= max_waves:
        logger.warning(f"Достигнут лимит волн ({max_waves})")
    
    logger.info(f"=== ЗАЧИСТКА ЗАВЕРШЕНА: {total_killed} ВРАГОВ ===")
    return total_killed



def _parse_distance_km(distance_str: Optional[str]) -> Optional[float]:
    """
    Парсить дистанцию из строки в километры.
    
    Args:
        distance_str: "1 189 м" или "188 км"
        
    Returns:
        Дистанция в км или None
    """
    if not distance_str:
        return None
    
    try:
        # Убираем все кроме цифр и точек
        num_str = ''.join(c for c in distance_str if c.isdigit() or c == '.')
        if not num_str:
            return None
        
        value = float(num_str)
        
        # Конвертируем в км
        if 'км' in distance_str or 'km' in distance_str.lower():
            return value
        elif 'м' in distance_str or 'm' in distance_str.lower():
            return value / 1000.0
        else:
            # По умолчанию метры
            return value / 1000.0
    except (ValueError, AttributeError):
        return None


def _wait_for_guns_inactive(sanderling: SanderlingService, timeout: float) -> bool:
    """
    Ждать пока ракеты (модуль верхнего слота) станут inactive.
    
    Args:
        sanderling: Сервис Sanderling
        timeout: Таймаут ожидания (сек)
        
    Returns:
        True если ракеты inactive
    """
    start = time.time()
    
    while time.time() - start < timeout:
        state = sanderling.get_state()
        if not state or not state.ship or not state.ship.modules:
            time.sleep(0.5)
            continue
        
        # Ищем модули верхнего слота
        high_modules = [m for m in state.ship.modules if m.slot_type == 'high']
        
        if not high_modules:
            logger.warning("Нет модулей верхнего слота")
            return True
        
        # Проверяем что все неактивны
        all_inactive = all(not m.is_active for m in high_modules)
        
        if all_inactive:
            logger.debug("Ракеты inactive")
            return True
        
        time.sleep(0.5)
    
    logger.warning(f"Таймаут {timeout}с ожидания inactive ракет")
    return False


def _wait_cache_death(sanderling: SanderlingService, timeout: float) -> bool:
    """
    Ждать смерти контейнера (исчезновение из targets).
    
    Args:
        sanderling: Сервис Sanderling
        timeout: Таймаут ожидания (сек)
        
    Returns:
        True если контейнер умер
    """
    start = time.time()
    
    while time.time() - start < timeout:
        state = sanderling.get_state()
        if not state:
            time.sleep(0.5)
            continue
        
        # Проверяем есть ли контейнер в targets
        cache_locked = False
        if state.targets:
            for target in state.targets:
                name_str = (target.name or "").lower()
                type_str = (target.type or "").lower()
                if any(keyword in name_str or keyword in type_str for keyword in [
                    'bioadaptive cache',
                    'biocombinative cache',
                    'cache'
                ]):
                    cache_locked = True
                    break
        
        # Если контейнера нет в targets - он умер
        if not cache_locked:
            logger.info("Контейнер исчез из targets - уничтожен!")
            return True
        
        time.sleep(0.5)
    
    logger.warning(f"Таймаут {timeout}с ожидания смерти контейнера")
    return False


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
        
        # Ищем врек
        for entry in state.overview:
            if not entry.name:
                continue
            
            name_lower = entry.name.lower()
            type_lower = (entry.type or "").lower()
            
            if 'остов' in name_lower or 'wreck' in name_lower or 'wreck' in type_lower:
                logger.debug(f"Найден врек: '{entry.name}'")
                return entry
        
        time.sleep(0.5)
    
    logger.error("Врек не найден!")
    return None


def _wait_for_gate(sanderling: SanderlingService, timeout: float) -> Optional[OverviewEntry]:
    """
    Ждать появления Gate или Conduit в overview.
    
    Args:
        sanderling: Сервис Sanderling
        timeout: Таймаут ожидания (сек)
        
    Returns:
        OverviewEntry гейта/кондуита или None
    """
    start = time.time()
    
    while time.time() - start < timeout:
        state = sanderling.get_state()
        if not state or not state.overview:
            time.sleep(0.5)
            continue
        
        # Ищем Gate или Conduit (частичное вхождение)
        for entry in state.overview:
            if not entry.name:
                continue
            
            name_lower = entry.name.lower()
            type_lower = (entry.type or "").lower()
            
            # Проверяем оба варианта
            if 'gate' in name_lower or 'gate' in type_lower or \
               'conduit' in name_lower or 'conduit' in type_lower:
                logger.debug(f"Найден Gate/Conduit: '{entry.name}' (type: '{entry.type}')")
                return entry
        
        time.sleep(0.5)
    
    logger.error("Gate/Conduit не найден!")
    return None



def _recall_drones(sanderling: SanderlingService) -> bool:
    """
    Вернуть дронов в корабль (Shift+R) и дождаться их возврата.
    
    Args:
        sanderling: Сервис Sanderling
        
    Returns:
        True если дроны вернулись
    """
    logger.info("Возвращаю дронов (Shift+R)...")
    
    # Проверяем есть ли дроны в космосе
    state = sanderling.get_state()
    if not state or not state.drones:
        logger.warning("Нет данных о дронах")
        return True  # Продолжаем, возможно окно дронов закрыто
    
    if state.drones.in_space_count == 0:
        logger.info("Дроны уже в корабле")
        return True
    
    logger.info(f"Дронов в космосе: {state.drones.in_space_count}")
    
    # Отправляем команду возврата
    try:
        key_down('shift')
        random_delay(0.15, 0.2)
        press_key('r')
        random_delay(0.15, 0.2)
    finally:
        key_up('shift')
    
    logger.info("Команда возврата отправлена")
    random_delay(1.0, 1.5)
    
    # Ждем пока все дроны вернутся
    logger.info("Жду возврата дронов...")
    start = time.time()
    timeout = 30.0
    
    while time.time() - start < timeout:
        state = sanderling.get_state()
        
        if not state or not state.drones:
            # Если нет данных о дронах, ждем еще
            time.sleep(1.0)
            continue
        
        # Проверяем количество дронов в космосе
        if state.drones.in_space_count == 0:
            elapsed = time.time() - start
            logger.info(f"Все дроны вернулись за {elapsed:.1f}с")
            return True
        
        # Проверяем состояние дронов
        returning_count = 0
        for drone in state.drones.drones_in_space:
            if drone.state == "Returning":
                returning_count += 1
        
        logger.debug(f"Дронов в космосе: {state.drones.in_space_count}, возвращается: {returning_count}")
        time.sleep(1.0)
    
    logger.warning(f"Таймаут {timeout}с ожидания возврата дронов")
    logger.warning(f"Осталось дронов в космосе: {state.drones.in_space_count if state and state.drones else '?'}")
    return False


def _jump_through_gate(sanderling: SanderlingService) -> bool:
    """
    Найти ворота и прыгнуть через них (Jump).
    
    Args:
        sanderling: Сервис Sanderling
        
    Returns:
        True если успешно
    """
    logger.info("Ищу ворота для прыжка...")
    
    # Шаг 1: Найти Gate/Conduit в overview
    gate_entry = _wait_for_gate(sanderling, timeout=10.0)
    if not gate_entry:
        logger.error("Gate/Conduit не найден")
        return False
    
    logger.info(f"Gate/Conduit найден: {gate_entry.name}")
    
    # Шаг 2: Кликнуть на Gate/Conduit
    logger.info("Кликаю на Gate/Conduit...")
    click(gate_entry.center[0], gate_entry.center[1], duration=0.18)
    random_delay(0.5, 0.8)
    
    # Шаг 3: Ждать появления кнопки Jump
    logger.info("Жду кнопки Jump...")
    jump_action = None
    for _ in range(10):
        state = sanderling.get_state()
        if state and state.selected_actions:
            # Ищем кнопку jump (может быть activate_gate или jump)
            jump_action = next((a for a in state.selected_actions 
                              if 'jump' in a.name.lower() or 'activate' in a.name.lower()), None)
            if jump_action:
                break
        time.sleep(0.5)
    
    if not jump_action:
        logger.error("Кнопка Jump не найдена")
        return False
    
    # Шаг 4: Кликнуть Jump
    logger.info(f"Кликаю Jump @ {jump_action.center}")
    click(jump_action.center[0], jump_action.center[1], duration=0.18)
    random_delay(1.0, 1.5)
    
    logger.info("Прыжок инициирован")
    return True



def _ensure_all_enemies_cleared(sanderling: SanderlingService) -> bool:
    """
    Убедиться что все враги зачищены во вкладке PvP Foe.
    
    Проверяет наличие врагов в overview. Если враги есть:
    - Если дальше 35км: собрать дронов, ждать подлета, выпустить, убить
    - Если ближе 35км: убить сразу
    
    Args:
        sanderling: Сервис Sanderling
        
    Returns:
        True если все враги зачищены
    """
    max_iterations = 5
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        logger.info(f"Проверка зачистки врагов (итерация {iteration}/{max_iterations})...")
        
        # Проверяем есть ли враги в overview
        state = sanderling.get_state()
        if not state or not state.overview or len(state.overview) == 0:
            logger.info("Нет врагов в overview - зачистка завершена")
            return True
        
        enemies_count = len(state.overview)
        logger.info(f"Обнаружено врагов в overview: {enemies_count}")
        
        # Проверяем дистанцию до ближайшего врага
        min_distance_km = None
        for entry in state.overview:
            if not entry.distance:
                continue
            
            distance_km = _parse_distance_km(entry.distance)
            if distance_km is None:
                continue
            
            if min_distance_km is None or distance_km < min_distance_km:
                min_distance_km = distance_km
        
        if min_distance_km is None:
            logger.warning("Не удалось определить дистанцию до врагов")
            min_distance_km = 100.0  # Считаем что далеко
        
        logger.info(f"Ближайший враг на расстоянии: {min_distance_km:.1f} км")
        
        # Если враги дальше 35км - собираем дронов и ждем
        if min_distance_km > 35.0:
            logger.info("Враги дальше 35 км - собираю дронов и жду подлета...")
            
            # Собрать дронов
            if not _recall_drones(sanderling):
                logger.warning("Не удалось вернуть дронов")
            
            # Ждать пока враги подлетят <= 35км
            logger.info("Жду пока враги подлетят <= 35 км...")
            start = time.time()
            timeout = 60.0
            
            while time.time() - start < timeout:
                state = sanderling.get_state()
                if not state or not state.overview:
                    time.sleep(1.0)
                    continue
                
                # Проверяем дистанцию
                closest_distance = None
                for entry in state.overview:
                    if not entry.distance:
                        continue
                    
                    distance_km = _parse_distance_km(entry.distance)
                    if distance_km is None:
                        continue
                    
                    if closest_distance is None or distance_km < closest_distance:
                        closest_distance = distance_km
                
                if closest_distance and closest_distance <= 35.0:
                    logger.info(f"Враг подлетел: {closest_distance:.1f} км")
                    break
                
                time.sleep(1.0)
            else:
                logger.warning("Таймаут ожидания подлета врагов")
            
            # Выпустить дронов
            logger.info("Выпускаю дронов...")
            _launch_drones_manual()
            random_delay(1.5, 2.0)
        
        # Убить всех врагов
        logger.info("Убиваю врагов...")
        killed = _clear_all_enemies(sanderling)
        logger.info(f"Убито врагов: {killed}")
        
        # Небольшая пауза перед следующей проверкой
        random_delay(1.0, 1.5)
    
    logger.error(f"Достигнут лимит итераций ({max_iterations})")
    return False



def _is_wreck(entry: OverviewEntry) -> bool:
    """
    Проверить является ли запись остовом.
    
    Args:
        entry: Запись в overview
        
    Returns:
        True если это остов
    """
    if not entry.name:
        return False
    
    name_lower = entry.name.lower()
    type_lower = (entry.type or "").lower()
    
    return 'остов' in name_lower or 'wreck' in name_lower or 'wreck' in type_lower


def _loot_wreck_direct(sanderling: SanderlingService, wreck_entry: OverviewEntry) -> bool:
    """
    Залутать остов напрямую (когда контейнер уже уничтожен).
    
    Args:
        sanderling: Сервис Sanderling
        wreck_entry: Запись остова в overview
        
    Returns:
        True если успешно
    """
    logger.info(f"Лутаю остов: {wreck_entry.name}")
    
    # Шаг 1: Кликнуть по вреку
    logger.info("Кликаю по вреку...")
    click(wreck_entry.center[0], wreck_entry.center[1], duration=0.18)
    random_delay(0.5, 0.8)
    
    # Шаг 2: Ждать кнопки approach
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
    
    # Шаг 3: Открыть карго (врек уже выбран после approach)
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
    
    # Шаг 4: Ждать кнопки "Взять все"
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
