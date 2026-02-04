"""
Модуль для работы с Triglavian Bioadaptive Cache (контейнер с лутом).

Переиспользуемый компонент для:
- Аппроча к контейнеру
- Лока и атаки
- Ожидания смерти
- Лута врека
"""
import logging
import time
from typing import Optional
from core.sanderling.service import SanderlingService
from eve.mouse import click, random_delay
from eve.keyboard import press_key, key_down, key_up

logger = logging.getLogger(__name__)


def process_cache(
    sanderling: SanderlingService,
    approach_timeout: float = 120.0,
    kill_timeout: float = 60.0,
    attack_distance_km: float = 30.0,
    enable_mwd: bool = True,
    launch_drones: bool = True
) -> bool:
    """
    Полный цикл работы с контейнером: аппроч, атака, лут.
    
    Порядок действий:
    1. Найти контейнер в overview
    2. Аппрочить контейнер
    3. Опционально: включить МВД
    4. Опционально: выпустить дронов
    5. Ждать приближения до attack_distance_km
    6. Залочить и атаковать (ракеты + дроны)
    7. Ждать смерти контейнера
    8. Залутать врек
    
    Args:
        sanderling: Сервис Sanderling
        approach_timeout: Таймаут приближения к контейнеру (сек)
        kill_timeout: Таймаут убийства контейнера (сек)
        attack_distance_km: Дистанция для начала атаки (км)
        enable_mwd: Включить МВД при аппроче
        launch_drones: Выпустить дронов при аппроче
        
    Returns:
        True если успешно обработали контейнер
    """
    logger.info("=== ОБРАБОТКА КОНТЕЙНЕРА ===")
    
    # 1. Найти контейнер
    logger.info("Шаг 1: Поиск контейнера в overview...")
    cache_entry = find_cache(sanderling)
    if not cache_entry:
        logger.error("Контейнер не найден в overview")
        return False
    
    logger.info(f"Контейнер найден: {cache_entry.name} на {cache_entry.distance}")
    
    # 2. Аппрочить
    logger.info("Шаг 2: Аппроч к контейнеру...")
    if not approach_cache(sanderling, cache_entry):
        logger.error("Не удалось начать аппроч")
        return False
    
    random_delay(1.0, 1.5)
    
    # 3. МВД (опционально)
    if enable_mwd:
        logger.info("Шаг 3: Включаю МВД...")
        ensure_mwd_active(sanderling)
        random_delay(0.5, 1.0)
    
    # 4. Дроны (опционально)
    if launch_drones:
        logger.info("Шаг 4: Выпускаю дронов...")
        launch_drones_safe()
        random_delay(1.0, 1.5)
    
    # 5. Ждать приближения и атаковать
    logger.info(f"Шаг 5: Жду приближения до {attack_distance_km} км...")
    if not wait_and_attack(sanderling, attack_distance_km, approach_timeout):
        logger.error("Не удалось атаковать контейнер")
        return False
    
    # 6. Ждать смерти
    logger.info("Шаг 6: Жду смерти контейнера...")
    if not wait_cache_death(sanderling, kill_timeout):
        logger.error("Контейнер не умер в течение таймаута")
        return False
    
    logger.info("Контейнер уничтожен!")
    random_delay(1.0, 1.5)
    
    # 7. Лут
    logger.info("Шаг 7: Лучу врек...")
    if not loot_wreck(sanderling):
        logger.warning("Не удалось залутать врек")
    
    logger.info("=== КОНТЕЙНЕР ОБРАБОТАН ===")
    return True


def find_cache(sanderling: SanderlingService, timeout: float = 5.0) -> Optional[object]:
    """
    Найти Triglavian Bioadaptive Cache в overview.
    
    Args:
        sanderling: Сервис Sanderling
        timeout: Таймаут поиска (сек)
        
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


def approach_cache(sanderling: SanderlingService, cache_entry: object) -> bool:
    """
    Выбрать контейнер и аппрочить его.
    
    Args:
        sanderling: Сервис Sanderling
        cache_entry: OverviewEntry контейнера
        
    Returns:
        True если успешно
    """
    # Кликнуть по контейнеру в overview
    if not cache_entry.center:
        logger.error("У контейнера нет координат")
        return False
    
    logger.debug(f"Кликаю по контейнеру @ {cache_entry.center}")
    click(cache_entry.center[0], cache_entry.center[1])
    random_delay(0.5, 0.8)
    
    # Найти кнопку "approach" в selected actions
    state = sanderling.get_state()
    if not state or not state.selected_actions:
        logger.error("Нет доступных действий")
        return False
    
    approach_action = next((a for a in state.selected_actions if a.name == 'approach'), None)
    if not approach_action:
        logger.error("Кнопка 'approach' не найдена")
        return False
    
    logger.debug(f"Кликаю 'approach' @ {approach_action.center}")
    click(approach_action.center[0], approach_action.center[1])
    
    return True


def ensure_mwd_active(sanderling: SanderlingService) -> None:
    """
    Проверить что МВД включен, если нет - включить.
    МВД на кнопке 2 (mid slot).
    
    Args:
        sanderling: Сервис Sanderling
    """
    state = sanderling.get_state()
    if not state or not state.ship or not state.ship.modules:
        logger.warning("Нет данных о модулях корабля")
        # Включаем по кнопке 2 вслепую
        logger.info("Включаю МВД по кнопке 2...")
        press_key('2')
        return
    
    # Найти МВД (mid slot, обычно первый)
    mwd = next((m for m in state.ship.modules if m.slot_type == 'mid'), None)
    
    if not mwd:
        logger.warning("МВД не найден в mid слотах")
        logger.info("Включаю МВД по кнопке 2...")
        press_key('2')
        return
    
    if mwd.is_active:
        logger.debug("МВД уже активен")
        return
    
    logger.info("МВД выключен, включаю...")
    press_key('2')


def launch_drones_safe() -> None:
    """
    Выпустить дронов (Shift+F).
    Следим чтобы Shift не залип.
    """
    logger.info("Выпускаю дронов (Shift+F)...")
    
    # Зажимаем Shift
    key_down('shift')
    random_delay(0.1, 0.15)
    
    # Нажимаем F
    press_key('f')
    random_delay(0.1, 0.15)
    
    # ОБЯЗАТЕЛЬНО отпускаем Shift
    key_up('shift')
    
    logger.debug("Дроны выпущены, Shift отпущен")


def wait_and_attack(
    sanderling: SanderlingService,
    attack_distance_km: float,
    timeout: float
) -> bool:
    """
    Ждать пока долетим до контейнера и атаковать.
    
    Args:
        sanderling: Сервис Sanderling
        attack_distance_km: Дистанция для начала атаки (км)
        timeout: Таймаут ожидания (сек)
        
    Returns:
        True если успешно атаковали
    """
    start = time.time()
    
    while time.time() - start < timeout:
        state = sanderling.get_state()
        if not state or not state.overview:
            time.sleep(0.5)
            continue
        
        # Найти контейнер в overview
        cache = next((e for e in state.overview if e.name and 'Triglavian Bioadaptive Cache' in e.name), None)
        if not cache:
            logger.warning("Контейнер исчез из overview")
            time.sleep(0.5)
            continue
        
        # Парсим дистанцию
        distance_km = parse_distance_km(cache.distance)
        if distance_km is None:
            time.sleep(0.5)
            continue
        
        logger.debug(f"Дистанция до контейнера: {distance_km:.1f} км")
        
        if distance_km <= attack_distance_km:
            logger.info(f"Достигли {distance_km:.1f} км, атакую!")
            
            # Лочим контейнер (Ctrl+Click)
            logger.debug("Лочу контейнер (Ctrl+Click)...")
            key_down('ctrl')
            random_delay(0.1, 0.15)
            click(cache.center[0], cache.center[1])
            random_delay(0.1, 0.15)
            key_up('ctrl')
            
            random_delay(0.5, 0.8)
            
            # Активируем ракеты (кнопка 1)
            logger.debug("Активирую ракеты (кнопка 1)...")
            press_key('1')
            
            random_delay(0.3, 0.5)
            
            # Отправляем дронов (F)
            logger.debug("Отправляю дронов (F)...")
            press_key('f')
            
            return True
        
        time.sleep(1.0)
    
    logger.error("Таймаут ожидания приближения к контейнеру")
    return False


def parse_distance_km(distance_str: Optional[str]) -> Optional[float]:
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


def wait_cache_death(sanderling: SanderlingService, timeout: float) -> bool:
    """
    Ждать смерти контейнера (исчезновение из лока или появление врека).
    
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
        
        # Проверяем есть ли контейнер в локе
        cache_locked = False
        if state.targets:
            for target in state.targets:
                if target.name and 'Triglavian Bioadaptive Cache' in target.name:
                    cache_locked = True
                    break
        
        # Если контейнера нет в локе - он умер
        if not cache_locked:
            logger.info("Контейнер исчез из лока - уничтожен!")
            return True
        
        # Проверяем появился ли врек в overview
        if state.overview:
            for entry in state.overview:
                if entry.name and 'wreck' in entry.name.lower():
                    logger.info("Врек появился в overview - контейнер уничтожен!")
                    return True
        
        time.sleep(0.5)
    
    return False


def loot_wreck(sanderling: SanderlingService) -> bool:
    """
    Залутать врек контейнера.
    
    Args:
        sanderling: Сервис Sanderling
        
    Returns:
        True если успешно
    """
    state = sanderling.get_state()
    if not state or not state.overview:
        logger.error("Нет данных overview")
        return False
    
    # Найти врек в overview
    wreck = next((e for e in state.overview if e.name and 'wreck' in e.name.lower()), None)
    if not wreck:
        logger.warning("Врек не найден в overview")
        return False
    
    logger.debug(f"Выбираю врек: {wreck.name}")
    click(wreck.center[0], wreck.center[1])
    random_delay(0.5, 0.8)
    
    # Аппрочим врек
    state = sanderling.get_state()
    if state and state.selected_actions:
        approach = next((a for a in state.selected_actions if a.name == 'approach'), None)
        if approach:
            logger.debug("Аппрочу врек...")
            click(approach.center[0], approach.center[1])
            random_delay(2.0, 3.0)
    
    # TODO: Нажать кнопку лута (когда будет в парсере)
    # Пока просто ждем и кликаем по вреку еще раз (откроет лут окно)
    logger.debug("Открываю лут окно...")
    click(wreck.center[0], wreck.center[1])
    random_delay(0.5, 1.0)
    
    # TODO: Забрать весь лут (Ctrl+Shift+Click или кнопка "Loot All")
    
    logger.info("Лут завершен")
    return True
