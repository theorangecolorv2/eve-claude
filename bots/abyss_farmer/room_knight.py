"""
Модуль для прохождения комнаты с Devoted Knight.

Особенности:
- ПКМ по Knight → наведение на "выйти на орбиту" → клик "30 км"
- Выпуск дронов
- Ожидание Knight <= 35км
- Лок Knight
- Атака только дронами (F каждые 15 секунд)
- После смерти Knight - аппроч к контейнеру, ожидание <= 35км, атака
- Лут контейнера (таймаут 45 секунд)
- Орбита гейта, проверка врагов, возврат дронов, прыжок
"""
import logging
import time
from typing import Optional
from core.sanderling.service import SanderlingService
from core.sanderling.models import OverviewEntry
from eve.mouse import click, right_click, move_mouse, random_delay
from eve.keyboard import press_key, key_down, key_up
from eve.modules import ensure_mid_slots_active

logger = logging.getLogger(__name__)


def knight_room(sanderling: SanderlingService, timeout: float = 300.0) -> bool:
    """
    Пройти комнату с Devoted Knight.
    
    Args:
        sanderling: Сервис Sanderling
        timeout: Максимальное время прохождения комнаты (сек)
        
    Returns:
        True если комната пройдена успешно
    """
    logger.info("=== НАЧАЛО ПРОХОЖДЕНИЯ КОМНАТЫ (KNIGHT) ===")
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
    random_delay(0.5, 0.6)
    
    # 4. Проверить наличие Devoted Knight
    logger.info("Шаг 4: Поиск Devoted Knight...")
    knight = _find_knight(sanderling)
    if not knight:
        logger.error("Devoted Knight не найден")
        return False
    
    logger.info(f"Knight найден: {knight.name}")
    
    # 5. ПКМ по Knight → наведение на орбиту → клик 30 км
    logger.info("Шаг 5: Орбита Knight 30 км...")
    if not _orbit_30km(sanderling, knight):
        logger.error("Не удалось выйти на орбиту 30 км")
        return False
    
    # 6. Выпустить дронов
    logger.info("Шаг 6: Выпуск дронов...")
    _launch_drones()
    random_delay(1.5, 2.0)
    
    # 7. Ждать пока Knight <= 35 км
    logger.info("Шаг 7: Ожидание Knight в радиусе <= 35 км...")
    if not _wait_target_in_range(sanderling, "Knight", max_distance_km=35.0, timeout=60.0):
        logger.warning("Knight не подлетел в радиус 35 км")
    
    # 8. Залочить Knight
    logger.info("Шаг 8: Лок Knight...")
    if not _lock_target(sanderling, knight):
        logger.error("Не удалось залочить Knight")
        return False
    
    # 9. Атаковать дронами с периодическим дублированием команды F
    logger.info("Шаг 9: Атака Knight дронами...")
    if not _kill_with_drones_only(sanderling, target_name="Knight"):
        logger.error("Не удалось убить Knight")
        return False
    
    logger.info("Knight убит!")
    
    # 10. Найти контейнер в overview
    logger.info("Шаг 10: Поиск контейнера...")
    cache_entry = _wait_for_cache(sanderling, timeout=30.0)
    if not cache_entry:
        logger.error("Контейнер не найден")
        return False
    
    # Проверяем это остов или живой контейнер
    is_wreck = _is_wreck(cache_entry)
    
    if is_wreck:
        logger.info("Контейнер уже уничтожен (остов), пропускаю убийство...")
        random_delay(1.0, 1.5)
        # Сразу переходим к луту
        if not _loot_wreck(sanderling):
            logger.warning("Не удалось залутать контейнер, продолжаю...")
        # Переходим к орбите гейта (пропускаем шаги 11-16)
    else:
        # 11. Аппроч к контейнеру
        logger.info("Шаг 11: Аппроч к контейнеру...")
        if not _approach_target(sanderling, cache_entry):
            logger.error("Не удалось начать аппроч к контейнеру")
            return False
        
        # 12. Ждать пока контейнер <= 35 км
        logger.info("Шаг 12: Ожидание контейнера в радиусе <= 35 км...")
        if not _wait_target_in_range(sanderling, "cache", max_distance_km=35.0, timeout=60.0):
            logger.warning("Контейнер не подлетел в радиус 35 км")
        
        # 13. Залочить контейнер
        logger.info("Шаг 13: Лок контейнера...")
        if not _lock_target(sanderling, cache_entry):
            logger.error("Не удалось залочить контейнер")
            return False
        
        # 14. Атаковать контейнер (1 + F)
        logger.info("Шаг 14: Атака контейнера...")
        press_key('1')
        random_delay(0.3, 0.5)
        press_key('f')
        random_delay(0.5, 0.8)
        
        # 15. Ждать смерти контейнера
        logger.info("Шаг 15: Ожидание смерти контейнера...")
        if not _wait_cache_death(sanderling, timeout=60.0):
            logger.error("Контейнер не умер")
            return False
        
        logger.info("Контейнер уничтожен!")
        random_delay(1.0, 1.5)
        
        # 16. Лут контейнера (таймаут 45 секунд)
        logger.info("Шаг 16: Лут контейнера...")
        if not _loot_wreck(sanderling):
            logger.warning("Не удалось залутать контейнер, продолжаю...")
    
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
    _parse_distance_km
)


def _find_knight(sanderling: SanderlingService) -> Optional[OverviewEntry]:
    """
    Найти Devoted Knight в overview (ТОЛЬКО Knight, не Hunter!).
    
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
        # Проверяем оба слова вместе
        if 'devoted' in name_lower and 'knight' in name_lower:
            return entry
    
    return None


def _orbit_30km(sanderling: SanderlingService, target: OverviewEntry) -> bool:
    """
    ПКМ по цели → наведение на "выйти на орбиту" → клик "30 км".
    
    Args:
        sanderling: Сервис Sanderling
        target: Цель в overview
        
    Returns:
        True если успешно
    """
    if not target.center:
        logger.error("У цели нет координат")
        return False
    
    # Шаг 1: ПКМ по цели
    logger.debug(f"ПКМ по цели @ {target.center}")
    right_click(target.center[0], target.center[1], duration=0.18)
    random_delay(0.5, 0.8)
    
    # Шаг 2: Ждать появления контекстного меню (несколько попыток)
    state = None
    for attempt in range(3):
        state = sanderling.get_state()
        if state and state.context_menu and state.context_menu.is_open:
            logger.debug(f"Контекстное меню открыто, пунктов: {len(state.context_menu.items)}")
            break
        
        if attempt < 2:
            logger.debug(f"Контекстное меню не открылось, попытка {attempt + 1}/3...")
            time.sleep(0.7)
    else:
        logger.error("Контекстное меню не открылось после 3 попыток")
        return False
    
    # Шаг 3: Найти пункт "Выйти на орбиту"
    orbit_item = None
    for item in state.context_menu.items:
        text_lower = item.text.lower()
        if 'орбит' in text_lower and 'выйти' in text_lower:
            orbit_item = item
            break
    
    if not orbit_item:
        logger.error("Пункт 'Выйти на орбиту' не найден")
        return False
    
    logger.debug(f"Найден пункт: '{orbit_item.text}' @ {orbit_item.center}")
    
    # Шаг 4: Навести мышку на "Выйти на орбиту" (без клика)
    logger.debug("Наведение мышки на 'Выйти на орбиту'...")
    move_mouse(orbit_item.center[0], orbit_item.center[1])
    
    # Ждем появления подменю (несколько попыток)
    logger.debug("Жду появления подменю с радиусами...")
    submenu_appeared = False
    for attempt in range(5):
        time.sleep(0.7)
        
        state = sanderling.get_state()
        if not state or not state.context_menu:
            continue
        
        # Проверяем есть ли пункты с радиусами
        has_radius_items = any("км" in item.text or " м" in item.text for item in state.context_menu.items 
                              if item.text.strip() in ["500 м", "1 000 м", "2 500 м", "5 000 м", "7 500 м", 
                                                       "10 км", "15 км", "20 км", "25 км", "30 км"])
        
        if has_radius_items:
            logger.debug(f"Подменю появилось, пунктов: {len(state.context_menu.items)}")
            submenu_appeared = True
            break
        
        logger.debug(f"Подменю не появилось, попытка {attempt + 1}/5...")
    
    if not submenu_appeared:
        logger.error("Подменю с радиусами не появилось")
        logger.error(f"Доступные пункты: {[item.text for item in state.context_menu.items]}")
        return False
    
    # Шаг 5: Получить обновленное состояние с подменю
    state = sanderling.get_state()
    if not state or not state.context_menu:
        logger.error("Подменю исчезло")
        return False
    
    logger.debug(f"Подменю открыто, пунктов: {len(state.context_menu.items)}")
    
    # Шаг 6: Найти пункт "30 км"
    orbit_30km_item = None
    for item in state.context_menu.items:
        text = item.text.strip()
        if text == "30 км" or text == "30км":
            orbit_30km_item = item
            break
    
    if not orbit_30km_item:
        logger.error("Пункт '30 км' не найден")
        logger.error(f"Доступные пункты: {[item.text for item in state.context_menu.items]}")
        return False
    
    logger.debug(f"Найден пункт '30 км' @ {orbit_30km_item.center}")
    
    # Шаг 7: Кликнуть на "30 км"
    logger.debug("Клик на '30 км'...")
    click(orbit_30km_item.center[0], orbit_30km_item.center[1], duration=0.18)
    random_delay(0.5, 0.8)
    
    logger.info("Орбита 30 км установлена")
    return True


def _launch_drones():
    """
    Выпустить дронов (Shift+F).
    """
    logger.debug("Выпускаю дронов: Shift+F")
    logger.debug("Зажимаю Shift...")
    
    try:
        key_down('shift')
        random_delay(0.15, 0.2)
        
        logger.debug("Нажимаю F...")
        press_key('f')
        random_delay(0.15, 0.2)
    finally:
        logger.debug("Отпускаю Shift...")
        key_up('shift')
    
    logger.info("Команда выпуска дронов отправлена")


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
    
    # Ждем появления в targets
    logger.debug("Жду появления цели в targets...")
    random_delay(2.8, 3.3)
    
    return True


def _kill_with_drones_only(sanderling: SanderlingService, target_name: str) -> bool:
    """
    Убить цель только дронами с периодическим дублированием команды F.
    
    Отправляет команду F каждые 15 секунд до смерти цели.
    
    Args:
        sanderling: Сервис Sanderling
        target_name: Имя цели (для логов)
        
    Returns:
        True если цель убита
    """
    logger.info("Начинаю атаку дронами (F)...")
    press_key('f')
    
    start = time.time()
    last_f_press = start
    kill_timeout = 180.0  # 3 минуты
    f_interval = 15.0  # Дублируем F каждые 15 секунд
    
    while time.time() - start < kill_timeout:
        # Проверяем жива ли цель
        state = sanderling.get_state()
        if not state or not state.targets or len(state.targets) == 0:
            elapsed = time.time() - start
            logger.info(f"Цель убита за {elapsed:.1f}с")
            return True
        
        # Дублируем команду F каждые 15 секунд
        current_time = time.time()
        if current_time - last_f_press >= f_interval:
            logger.debug("Дублирую команду F...")
            press_key('f')
            last_f_press = current_time
        
        time.sleep(1.0)
    
    logger.error(f"Таймаут {kill_timeout}с на убийство цели")
    return False


def _loot_wreck(sanderling: SanderlingService) -> bool:
    """
    Залутать врек контейнера (таймаут 45 секунд).
    
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
    
    # Шаг 5: Ждать кнопки "Взять все" (45 секунд)
    logger.info("Жду кнопки 'Взять все'...")
    for attempt in range(37):  # 45 секунд (37 × 1.2с)
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
    
    logger.warning("Не удалось найти кнопку 'Взять все' за 45 секунд, продолжаю...")
    return True  # Продолжаем выполнение


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
            
            name_lower = entry.name.lower()
            type_lower = (entry.type or "").lower()
            
            if 'остов' in name_lower or 'wreck' in name_lower or 'wreck' in type_lower:
                logger.debug(f"Найден врек: '{entry.name}'")
                return entry
        
        time.sleep(0.5)
    
    logger.error("Врек не найден!")
    return None



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
