"""
Eve Framework - Navigation module

Навигация по маршруту:
- has_anomalies() - проверка наличия аномалий (убежище/укрытие)
- warp_to_anomaly() - варп в аномалию
- jump_to_next_system() - прыжок в следующую систему
- farm_system() - зачистка всех аномалий в системе
"""

import os
import time
import logging
from typing import Optional, Tuple

import numpy as np
import cv2
import mss

from .vision import find_image, wait_image
from .mouse import click, right_click, move_to, random_delay, get_position
from .actions import click_on_image
from .overview import is_overview_empty, count_targets, clear_anomaly

logger = logging.getLogger(__name__)


# ============================================================================
# ANTI-SLEEP (предотвращение засыпания монитора)
# ============================================================================

def _mouse_jiggle():
    """
    Немного подвигать мышкой чтобы монитор не засыпал.
    Двигает на +-1-2 пикселя от текущей позиции.
    """
    import random
    x, y = get_position()

    # Случайное смещение на 1-2 пикселя
    dx = random.randint(-2, 2)
    dy = random.randint(-2, 2)

    # Двигаем туда и обратно
    move_to(x + dx, y + dy, duration=0.1, humanize=False)
    time.sleep(0.05)
    move_to(x, y, duration=0.1, humanize=False)

    logger.debug("Mouse jiggle (anti-sleep)")


# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

class NavigationConfig:
    """Настройки навигации."""

    # Вкладки
    TAB_JUMP_TEMPLATE = "eve_tab_jump.png"  # Вкладка Jump
    TAB_PVP_FOE_TEMPLATE = "eve_tab_pvp_foe.png"  # Вкладка PvP Foe

    # Гейты
    GATE_YELLOW_TEMPLATE = "eve_gate_yellow.png"  # Жёлтый гейт (активный)
    BUTTON_JUMP_TEMPLATE = "eve_button_jump.png"  # Кнопка Jump (>>)

    # Индикаторы
    SPEED_ZERO_TEMPLATE = "eve_speed_zero.png"  # 0.0 М/С (остановка)

    # Аномалии
    ANOMALY_UBEJISHE_TEMPLATE = "eve_anomaly_ubejishe.png"  # Убежище
    ANOMALY_UKRYTIE_TEMPLATE = "eve_anomaly_ukrytie.png"  # Укрытие

    # Варп меню
    WARP_0_TEMPLATE = "eve_warp_0.png"  # Варп в 0 м (для укрытия)
    WARP_SUBMENU_TEMPLATE = "eve_warp_submenu.png"  # "Перейти в варп-режим" (подменю)
    WARP_10KM_TEMPLATE = "eve_warp_10km.png"  # Выход в 10 км (для убежища)

    # Безопасный анкор (для отвода мышки)
    SAFE_ANCHOR_TEMPLATE = "eve_overview_title.png"  # "Обзорная панель"

    # Таймауты
    JUMP_INITIAL_WAIT = 30  # Начальное ожидание после прыжка (сек)
    JUMP_COMPLETE_TIMEOUT = 120  # Максимум ожидания "0.0" после начального (сек)
    WARP_TIMEOUT = 120  # Таймаут варпа в аномалию (сек)
    TARGETS_WAIT_TIMEOUT = 120  # Ожидание появления целей (сек)


def _get_assets_path() -> str:
    """Получить путь к папке assets."""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")


# ============================================================================
# ПРОВЕРКА АНОМАЛИЙ
# ============================================================================

def has_anomaly_ubejishe() -> bool:
    """Проверить есть ли аномалия 'Убежище'."""
    template_path = os.path.join(_get_assets_path(), NavigationConfig.ANOMALY_UBEJISHE_TEMPLATE)
    result = find_image(template_path, confidence=0.92)
    if result:
        logger.info("Найдена аномалия: Убежище")
        return True
    return False


def has_anomaly_ukrytie() -> bool:
    """Проверить есть ли аномалия 'Укрытие'."""
    template_path = os.path.join(_get_assets_path(), NavigationConfig.ANOMALY_UKRYTIE_TEMPLATE)
    result = find_image(template_path, confidence=0.92)
    if result:
        logger.info("Найдена аномалия: Укрытие")
        return True
    return False


def has_anomalies() -> bool:
    """
    Проверить есть ли аномалии (убежище или укрытие).

    Returns:
        True если есть хотя бы одна аномалия
    """
    return has_anomaly_ubejishe() or has_anomaly_ukrytie()


def find_anomaly_ukrytie() -> Optional[Tuple[int, int]]:
    """Найти координаты укрытия."""
    template_path = os.path.join(_get_assets_path(), NavigationConfig.ANOMALY_UKRYTIE_TEMPLATE)
    return find_image(template_path, confidence=0.92)


def find_anomaly_ubejishe() -> Optional[Tuple[int, int]]:
    """Найти координаты убежища."""
    template_path = os.path.join(_get_assets_path(), NavigationConfig.ANOMALY_UBEJISHE_TEMPLATE)
    return find_image(template_path, confidence=0.92)


def find_anomaly() -> Optional[Tuple[str, Tuple[int, int]]]:
    """
    Найти первую доступную аномалию.

    Returns:
        (тип, (x, y)) или None. Тип: "ukrytie" или "ubejishe"
    """
    # Сначала ищем укрытие (приоритет - варп проще)
    coords = find_anomaly_ukrytie()
    if coords:
        logger.info(f"Найдена аномалия 'Укрытие': {coords}")
        return ("ukrytie", coords)

    # Потом убежище
    coords = find_anomaly_ubejishe()
    if coords:
        logger.info(f"Найдена аномалия 'Убежище': {coords}")
        return ("ubejishe", coords)

    logger.debug("Аномалии не найдены")
    return None


# ============================================================================
# БЕЗОПАСНЫЙ АНКОР
# ============================================================================

def _click_safe_anchor() -> bool:
    """Кликнуть на безопасный анкор (отвести мышку и закрыть меню)."""
    template_path = os.path.join(_get_assets_path(), NavigationConfig.SAFE_ANCHOR_TEMPLATE)
    result = find_image(template_path, confidence=0.8)

    if result:
        logger.debug("Кликаю на безопасный анкор...")
        click(result[0], result[1])
        return True

    logger.warning("Безопасный анкор не найден")
    return False


# ============================================================================
# ВАРП В АНОМАЛИИ
# ============================================================================

def warp_to_ukrytie(coords: Tuple[int, int]) -> bool:
    """
    Варп в укрытие: ПКМ -> варп в 0.

    Args:
        coords: Координаты укрытия

    Returns:
        True если варп начат, False если нужно искать аномалию заново
    """
    warp_template = os.path.join(_get_assets_path(), NavigationConfig.WARP_0_TEMPLATE)

    logger.info("Варп в укрытие...")

    # ПКМ по укрытию (быстрый клик для аномалий)
    right_click(coords[0], coords[1], duration=0.15)
    random_delay(0.4, 0.6)

    # Ищем кнопку "варп в 0"
    warp_btn = find_image(warp_template, confidence=0.8)
    if warp_btn:
        logger.info("Нажимаю 'Варп в 0'...")
        click(warp_btn[0], warp_btn[1])
        return True

    # Кнопки нет - закрываем меню и возвращаем False
    # Вызывающий код должен заново искать аномалию (она могла исчезнуть)
    logger.warning("Кнопка варпа не найдена, закрываю меню...")
    _click_safe_anchor()
    random_delay(5.0, 6.0)
    return False


def warp_to_ubejishe(coords: Tuple[int, int]) -> bool:
    """
    Варп в убежище: ПКМ -> варп выбрать -> варп в 10 км.

    Args:
        coords: Координаты убежища

    Returns:
        True если варп начат, False если нужно искать аномалию заново
    """
    submenu_template = os.path.join(_get_assets_path(), NavigationConfig.WARP_SUBMENU_TEMPLATE)
    warp_10km_template = os.path.join(_get_assets_path(), NavigationConfig.WARP_10KM_TEMPLATE)

    logger.info("Варп в убежище...")

    # ПКМ по убежищу (быстрый клик для аномалий)
    right_click(coords[0], coords[1], duration=0.15)
    random_delay(0.4, 0.6)

    # Ищем подменю "варп выбрать"
    submenu = find_image(submenu_template, confidence=0.8)
    if not submenu:
        logger.warning("Подменю варпа не найдено, закрываю меню...")
        _click_safe_anchor()
        random_delay(5.0, 6.0)
        return False

    # Наводим на подменю
    logger.debug("Навожу на подменю варпа...")
    move_to(submenu[0], submenu[1])
    random_delay(0.3, 0.4)

    # Ищем "варп в 10 км"
    warp_btn = find_image(warp_10km_template, confidence=0.8)
    if warp_btn:
        logger.info("Нажимаю 'Варп в 10 км'...")
        click(warp_btn[0], warp_btn[1])
        return True

    # Кнопки нет - закрываем меню и возвращаем False
    logger.warning("Кнопка 'варп в 10 км' не найдена, закрываю меню...")
    _click_safe_anchor()
    random_delay(5.0, 6.0)
    return False


def warp_to_anomaly() -> bool:
    """
    Найти аномалию и варпнуть в неё.

    Returns:
        True если варп начат
    """
    anomaly = find_anomaly()
    if not anomaly:
        logger.info("Аномалий нет")
        return False

    anomaly_type, coords = anomaly

    if anomaly_type == "ukrytie":
        return warp_to_ukrytie(coords)
    else:  # ubejishe
        return warp_to_ubejishe(coords)


# ============================================================================
# ОЖИДАНИЕ ЦЕЛЕЙ
# ============================================================================

def click_tab_pvp_foe() -> bool:
    """Кликнуть на вкладку PvP Foe."""
    template_path = os.path.join(_get_assets_path(), NavigationConfig.TAB_PVP_FOE_TEMPLATE)
    result = find_image(template_path, confidence=0.8)

    if result:
        logger.info("Переключаюсь на вкладку PvP Foe...")
        click(result[0], result[1])
        random_delay(0.3, 0.5)
        return True

    logger.error("Вкладка PvP Foe не найдена")
    return False


def wait_for_targets(timeout: float = None) -> bool:
    """
    Ждать появления целей в overview.

    Args:
        timeout: Таймаут ожидания (по умолчанию из конфига)

    Returns:
        True если цели появились
    """
    timeout = timeout or NavigationConfig.TARGETS_WAIT_TIMEOUT
    logger.info(f"Жду появления целей до {timeout} сек...")

    start_time = time.time()
    last_jiggle = start_time

    while time.time() - start_time < timeout:
        # Anti-sleep: jiggle мышки каждые 15 сек
        if time.time() - last_jiggle > 15:
            _mouse_jiggle()
            last_jiggle = time.time()

        if not is_overview_empty():
            targets = count_targets()
            if targets > 0:
                logger.info(f"Цели появились: {targets}")
                # Ждём ещё 3-4 сек пока все подгрузятся
                random_delay(3.0, 4.0)
                return True
        time.sleep(1)

    logger.warning("Таймаут ожидания целей")
    return False


# ============================================================================
# ЗАЧИСТКА АНОМАЛИИ
# ============================================================================

def clear_current_anomaly(guns_key: str = "2") -> int:
    """
    Зачистить текущую аномалию (после варпа).

    Args:
        guns_key: Клавиша пушек

    Returns:
        Количество убитых целей
    """
    logger.info("=== ЗАЧИСТКА АНОМАЛИИ ===")

    # Используем функцию из overview
    killed = clear_anomaly(guns_key=guns_key)

    logger.info(f"Аномалия зачищена, убито: {killed}")

    # Ждём 5 сек после зачистки
    random_delay(4.5, 5.5)

    return killed


# ============================================================================
# НАВИГАЦИЯ
# ============================================================================

def click_tab_jump() -> bool:
    """Кликнуть на вкладку Jump."""
    template_path = os.path.join(_get_assets_path(), NavigationConfig.TAB_JUMP_TEMPLATE)
    result = find_image(template_path, confidence=0.8)

    if result:
        logger.info("Кликаю на вкладку Jump...")
        click(result[0], result[1])
        random_delay(0.3, 0.6)
        return True

    logger.error("Вкладка Jump не найдена")
    return False


def _has_yellow_pixels(x: int, y: int, region_size: int = 30, min_yellow_percent: float = 5.0) -> bool:
    """
    Проверить есть ли жёлтые пиксели в области вокруг точки.

    Args:
        x, y: Центр области
        region_size: Размер области для проверки
        min_yellow_percent: Минимальный процент жёлтых пикселей

    Returns:
        True если есть достаточно жёлтых пикселей
    """
    half = region_size // 2
    region = {
        "left": x - half,
        "top": y - half,
        "width": region_size,
        "height": region_size
    }

    with mss.mss() as sct:
        img = sct.grab(region)
        frame = np.array(img)

    # Конвертируем в HSV для проверки цвета
    if frame.shape[2] == 4:
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    else:
        frame_bgr = frame

    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)

    # Широкий диапазон жёлтого цвета в HSV
    # Hue: 15-45 (жёлтый-оранжевый), Saturation: 100-255, Value: 100-255
    lower_yellow = np.array([15, 100, 100])
    upper_yellow = np.array([45, 255, 255])

    # Маска жёлтых пикселей
    mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

    # Процент жёлтых пикселей
    yellow_pixels = np.sum(mask > 0)
    total_pixels = mask.size
    yellow_percent = (yellow_pixels / total_pixels) * 100

    logger.debug(f"Жёлтых пикселей: {yellow_percent:.1f}% (порог: {min_yellow_percent}%)")

    return yellow_percent >= min_yellow_percent


def click_yellow_gate() -> bool:
    """Кликнуть на жёлтый гейт (следующий на маршруте)."""
    template_path = os.path.join(_get_assets_path(), NavigationConfig.GATE_YELLOW_TEMPLATE)

    # Увеличенный confidence для более строгого совпадения
    result = find_image(template_path, confidence=0.85)

    if result:
        x, y = result

        # Дополнительная проверка: есть ли жёлтые пиксели в области?
        if not _has_yellow_pixels(x, y):
            logger.warning(f"Найден гейт @ {result}, но он НЕ жёлтый - пропускаю")
            return False

        logger.info(f"Кликаю на жёлтый гейт: {result}")
        click(x, y)
        random_delay(0.3, 0.6)
        return True

    logger.error("Жёлтый гейт не найден")
    return False


def click_jump_button() -> bool:
    """Нажать кнопку Jump."""
    template_path = os.path.join(_get_assets_path(), NavigationConfig.BUTTON_JUMP_TEMPLATE)
    result = find_image(template_path, confidence=0.8)

    if result:
        logger.info("Нажимаю кнопку Jump...")
        click(result[0], result[1])
        return True

    logger.error("Кнопка Jump не найдена")
    return False


def wait_jump_complete() -> bool:
    """
    Ожидать завершения прыжка.

    Returns:
        True если прыжок завершён
    """
    logger.info(f"Ожидаю {NavigationConfig.JUMP_INITIAL_WAIT} сек (время прыжка)...")

    # Начальное ожидание с anti-sleep jiggle
    initial_wait = NavigationConfig.JUMP_INITIAL_WAIT
    waited = 0
    while waited < initial_wait:
        time.sleep(1)
        waited += 1
        # Jiggle каждые 15 сек
        if waited % 15 == 0:
            _mouse_jiggle()

    logger.info(f"Жду индикатор '0.0 М/С' до {NavigationConfig.JUMP_COMPLETE_TIMEOUT} сек...")

    template_path = os.path.join(_get_assets_path(), NavigationConfig.SPEED_ZERO_TEMPLATE)

    start_time = time.time()
    last_jiggle = start_time

    while time.time() - start_time < NavigationConfig.JUMP_COMPLETE_TIMEOUT:
        # Anti-sleep: jiggle каждые 15 сек
        if time.time() - last_jiggle > 15:
            _mouse_jiggle()
            last_jiggle = time.time()

        result = find_image(template_path, confidence=0.85)
        if result:
            logger.info("Прыжок завершён - корабль остановился (0.0 М/С)")
            random_delay(5.0, 6.0)
            logger.info("Система загружена")
            return True
        time.sleep(1)

    logger.error("Таймаут ожидания завершения прыжка")
    return False


def jump_to_next_system() -> bool:
    """
    Прыгнуть в следующую систему по маршруту.

    Returns:
        True если успешно перешли в новую систему
    """
    logger.info("=== ПРЫЖОК В СЛЕДУЮЩУЮ СИСТЕМУ ===")

    if not click_tab_jump():
        return False
    random_delay(0.5, 0.8)

    if not click_yellow_gate():
        return False
    random_delay(0.3, 0.5)

    if not click_jump_button():
        return False

    if not wait_jump_complete():
        return False

    logger.info("=== ПРЫЖОК ЗАВЕРШЁН ===")
    return True


# ============================================================================
# ОСНОВНОЙ ЦИКЛ ФАРМА
# ============================================================================

def farm_anomaly(guns_key: str = "2") -> bool:
    """
    Найти аномалию, варпнуть и зачистить.

    Returns:
        True если аномалия зачищена
    """
    # 1. Варп в аномалию
    if not warp_to_anomaly():
        return False

    # 2. Сразу переключаемся на PvP Foe
    random_delay(1.0, 1.5)

    if not click_tab_pvp_foe():
        logger.error("Не удалось переключиться на PvP Foe")
        return False

    # 3. Ждём появления целей (60 сек - пока летим)
    if not wait_for_targets(timeout=60):
        logger.warning("Цели не появились - аномалия уже зачищена")
        return True  # Считаем как успех

    # 4. Зачищаем
    clear_current_anomaly(guns_key)

    # 5. Пауза после зачистки
    random_delay(5.0, 6.0)

    return True


def farm_system(guns_key: str = "2") -> int:
    """
    Зачистить все аномалии в системе.

    Args:
        guns_key: Клавиша пушек

    Returns:
        Количество зачищенных аномалий
    """
    logger.info("=== ФАРМ СИСТЕМЫ ===")
    cleared = 0

    while has_anomalies():
        logger.info(f"--- Аномалия #{cleared + 1} ---")

        if farm_anomaly(guns_key):
            cleared += 1
        else:
            logger.warning("Не удалось зачистить аномалию")
            break

    logger.info(f"=== СИСТЕМА ЗАЧИЩЕНА: {cleared} аномалий ===")
    return cleared
