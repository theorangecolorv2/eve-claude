"""
Eve Framework - Overview Combat module

Боевые функции для работы с Overview:
- Переключение на вкладку с врагами
- Лок врагов волнами (с учётом лимита 5)
- Убийство врагов
"""

import logging
import time
from typing import Optional, List

from core.sanderling.service import SanderlingService
from core.sanderling.models import OverviewEntry
from eve.mouse import click, random_delay
from eve.keyboard import key_down, key_up, press_key

logger = logging.getLogger(__name__)


def switch_to_pvp_tab(sanderling: SanderlingService, tab_name: str = "PvP Foe") -> bool:
    """
    Переключиться на вкладку overview с врагами.
    
    Args:
        sanderling: Сервис Sanderling
        tab_name: Название вкладки (по умолчанию "PvP Foe")
        
    Returns:
        True если успешно переключились
    """
    logger.info(f"Переключаюсь на вкладку '{tab_name}'...")
    
    state = sanderling.get_state()
    if not state or not state.overview_tabs:
        logger.error("Нет данных о вкладках overview")
        return False
    
    # Ищем вкладку по имени (частичное совпадение)
    target_tab = None
    for tab in state.overview_tabs:
        if tab_name.lower() in tab.label.lower():
            target_tab = tab
            break
    
    if not target_tab:
        logger.error(f"Вкладка '{tab_name}' не найдена")
        logger.info(f"Доступные вкладки: {[t.label for t in state.overview_tabs]}")
        return False
    
    # Кликаем по вкладке
    logger.info(f"Кликаю по вкладке '{target_tab.label}' в {target_tab.center}")
    click(target_tab.center[0], target_tab.center[1])
    random_delay(0.5, 0.6)  # Короткая пауза после переключения
    
    return True


def get_all_enemies(sanderling: SanderlingService) -> List[OverviewEntry]:
    """
    Получить список всех врагов из overview.
    
    ВАЖНО: Перед вызовом нужно переключиться на вкладку с врагами!
    
    Args:
        sanderling: Сервис Sanderling
        
    Returns:
        Список врагов из overview
    """
    state = sanderling.get_state()
    if not state or not state.overview:
        return []
    
    # Если мы на вкладке "PvP Foe", то все записи - враги
    return state.overview


def lock_enemies_batch(sanderling: SanderlingService, max_locks: int = 5) -> int:
    """
    Залочить врагов пачкой (с учётом лимита локов).
    
    ВАЖНО: Перед вызовом нужно переключиться на вкладку с врагами!
    
    Args:
        sanderling: Сервис Sanderling
        max_locks: Максимум локов (по умолчанию 5)
        
    Returns:
        Количество залоченных врагов
    """
    enemies = get_all_enemies(sanderling)
    
    if not enemies:
        logger.info("Нет врагов в overview")
        return 0
    
    # Лочим только первые max_locks целей
    to_lock = enemies[:max_locks]
    logger.info(f"Лочу {len(to_lock)} врагов (лимит: {max_locks})...")
    
    # Зажимаем Ctrl
    key_down("ctrl")
    random_delay(0.15, 0.25)
    
    # Кликаем по каждому врагу
    for i, enemy in enumerate(to_lock):
        if not enemy.center:
            continue
        
        logger.debug(f"  Ctrl+Click по врагу #{i+1}: {enemy.name} в {enemy.center}")
        click(enemy.center[0], enemy.center[1])
        random_delay(0.3, 0.4)  # Пауза между локами
    
    # Отпускаем Ctrl
    random_delay(0.1, 0.2)
    key_up("ctrl")
    
    logger.info(f"Залочено {len(to_lock)} врагов")
    return len(to_lock)


def kill_locked_batch(
    sanderling: SanderlingService,
    guns_key: str = "1",
    drones_key: str = "f",
    check_interval: float = 1.0,
    kill_timeout: float = 60.0
) -> int:
    """
    Убить всех текущих залоченных врагов дронами + ракетами.
    
    Логика:
    1. Проверяем сколько целей залочено
    2. Для каждой цели: включаем пушки + дроны -> ждём уменьшения количества целей
    3. Повторяем пока есть залоченные цели
    
    Args:
        sanderling: Сервис Sanderling
        guns_key: Клавиша активации пушек
        drones_key: Клавиша атаки дронами
        check_interval: Интервал проверки статуса (сек)
        kill_timeout: Таймаут на убийство ОДНОЙ цели (сек)
        
    Returns:
        Количество убитых врагов
    """
    # Проверяем сколько целей залочено
    state = sanderling.get_state()
    if not state or not state.targets:
        logger.info("Нет залоченных целей")
        return 0
    
    initial_count = len(state.targets)
    logger.info(f"=== УБИВАЮ {initial_count} ЗАЛОЧЕННЫХ ЦЕЛЕЙ ===")
    killed = 0
    
    for i in range(initial_count):
        # Проверяем есть ли ещё залоченные цели
        state = sanderling.get_state()
        if not state or not state.targets:
            logger.info(f"Лок пустой после {killed} убийств")
            break
        
        current_targets = len(state.targets)
        logger.info(f"--- Цель {i+1}/{initial_count} (залочено: {current_targets}, убито: {killed}) ---")
        
        # Включаем пушки
        logger.debug(f"Нажимаю '{guns_key}' для активации пушек...")
        press_key(guns_key)
        random_delay(0.3, 0.5)
        
        # Дроны атакуют
        logger.debug(f"Нажимаю '{drones_key}' для атаки дронами...")
        press_key(drones_key)
        random_delay(0.3, 0.5)  # Пауза после команды дронам
        
        logger.debug("Жду смерти цели (проверяю количество целей)...")
        
        # Ждём пока количество целей не уменьшится
        start_time = time.time()
        while time.time() - start_time < kill_timeout:
            state = sanderling.get_state()
            
            # Проверяем что цель умерла (уменьшилось количество)
            if not state or not state.targets:
                logger.info(f"Цель {i+1} убита - лок пустой")
                killed += 1
                break
            
            new_count = len(state.targets)
            if new_count < current_targets:
                elapsed = time.time() - start_time
                logger.info(f"Цель {i+1} убита за {elapsed:.1f}с (было {current_targets}, стало {new_count})")
                killed += 1
                break
            
            time.sleep(check_interval)
        else:
            logger.warning(f"Таймаут {kill_timeout}с на цель {i+1}")
            break
        
        # Пауза перед следующей целью
        random_delay(0.3, 0.6)
    
    logger.info(f"=== УБИТО {killed} ЦЕЛЕЙ ===")
    return killed


def clear_enemies(
    sanderling: SanderlingService,
    guns_key: str = "1",
    drones_key: str = "f",
    pvp_tab_name: str = "PvP Foe",
    max_locks: int = 5,
    max_waves: int = 10,
    launch_drones_first: bool = True
) -> int:
    """
    Полная зачистка врагов волнами: переключение на вкладку, выпуск дронов, лок пачками, убийство.
    
    Логика:
    1. Переключаемся на вкладку с врагами
    2. Выпускаем дронов (если launch_drones_first=True)
    3. ЦИКЛ: пока есть враги в overview (макс max_waves волн):
       - Лочим до max_locks врагов
       - Убиваем всех залоченных
       - Проверяем остались ли враги
    
    Args:
        sanderling: Сервис Sanderling
        guns_key: Клавиша активации пушек
        drones_key: Клавиша атаки дронами
        pvp_tab_name: Название вкладки с врагами
        max_locks: Максимум локов за раз (по умолчанию 5)
        max_waves: Максимум волн (защита от зацикливания)
        launch_drones_first: Выпустить дронов перед зачисткой
        
    Returns:
        Общее количество убитых врагов
    """
    logger.info("=== ЗАЧИСТКА ВРАГОВ (ВОЛНАМИ) ===")
    
    # 1. Переключаемся на вкладку с врагами
    if not switch_to_pvp_tab(sanderling, pvp_tab_name):
        logger.error("Не удалось переключиться на вкладку с врагами")
        return 0
    
    # 2. Выпускаем дронов (если нужно)
    if launch_drones_first:
        from eve.combat import launch_drones
        logger.info("Выпускаю дронов...")
        launch_drones()
        random_delay(1.2, 1.4)  # Ждём выпуска дронов
    
    total_killed = 0
    wave = 0
    
    while wave < max_waves:
        wave += 1
        
        # Проверяем есть ли враги в overview
        enemies = get_all_enemies(sanderling)
        if not enemies:
            logger.info(f"Нет врагов в overview - зачистка завершена! Всего убито: {total_killed}")
            break
        
        logger.info(f"--- ВОЛНА {wave}: {len(enemies)} врагов в overview ---")
        
        # Лочим пачку (до max_locks)
        locked = lock_enemies_batch(sanderling, max_locks)
        if locked == 0:
            logger.warning("Не удалось залочить врагов")
            break
        
        # Пауза после лока (цели должны залочиться)
        random_delay(2.0, 2.1)  # Ждём чтобы лок применился
        
        # Убиваем залоченных
        killed = kill_locked_batch(sanderling, guns_key, drones_key)
        total_killed += killed
        
        logger.info(f"Волна {wave} завершена: убито {killed}, всего {total_killed}")
        
        # Пауза между волнами
        random_delay(0.3, 0.5)
    
    if wave >= max_waves:
        logger.warning(f"Достигнут лимит волн ({max_waves}). Убито: {total_killed}")
    
    logger.info(f"=== ЗАЧИСТКА ЗАВЕРШЕНА: {total_killed} ВРАГОВ ===")
    return total_killed
