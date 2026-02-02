"""
Eve Framework - High-level actions for bot automation

Высокоуровневые действия:
- click_on_image, double_click_on_image, right_click_on_image
- right_click_menu (ПКМ → выбор опции)
- wait_and_click
- is_visible, wait_until_visible, wait_until_gone

Все функции используют хуманизацию по умолчанию.
"""

import time
import logging
from typing import Optional, Tuple, List

from eve.vision import find_image, wait_image, wait_image_disappear
from eve.mouse import click, double_click, right_click, move_to, random_delay

logger = logging.getLogger(__name__)


# ============================================================================
# НАСТРОЙКИ ПО УМОЛЧАНИЮ
# ============================================================================

DEFAULT_TIMEOUT = 10.0      # Таймаут ожидания по умолчанию
DEFAULT_CONFIDENCE = 0.9    # Порог совпадения по умолчанию
DEFAULT_INTERVAL = 0.3      # Интервал проверки при ожидании


# ============================================================================
# БАЗОВЫЕ ДЕЙСТВИЯ С ИЗОБРАЖЕНИЯМИ
# ============================================================================

def click_on_image(
    template: str,
    timeout: float = DEFAULT_TIMEOUT,
    confidence: float = DEFAULT_CONFIDENCE,
    region: Optional[Tuple[int, int, int, int]] = None,
    humanize: bool = True
) -> bool:
    """
    Найти изображение на экране и кликнуть по нему.

    Args:
        template: Путь к изображению-шаблону (или имя в assets/)
        timeout: Время ожидания появления (сек)
        confidence: Порог совпадения (0.0 - 1.0)
        region: Область поиска (x1, y1, x2, y2) или None
        humanize: Использовать хуманизацию

    Returns:
        True если клик выполнен, False если изображение не найдено
    """
    logger.debug(f"click_on_image: ищу '{template}' (timeout={timeout}s)")

    coords = wait_image(template, timeout=timeout, confidence=confidence)

    if coords:
        x, y = coords
        logger.debug(f"click_on_image: найдено в ({x}, {y}), кликаю")
        click(x, y, humanize=humanize)
        return True

    logger.warning(f"click_on_image: '{template}' не найден за {timeout}s")
    return False


def double_click_on_image(
    template: str,
    timeout: float = DEFAULT_TIMEOUT,
    confidence: float = DEFAULT_CONFIDENCE,
    region: Optional[Tuple[int, int, int, int]] = None,
    humanize: bool = True
) -> bool:
    """
    Найти изображение и выполнить двойной клик.

    Args:
        template: Путь к изображению-шаблону
        timeout: Время ожидания появления
        confidence: Порог совпадения
        region: Область поиска или None
        humanize: Использовать хуманизацию

    Returns:
        True если клик выполнен, False если не найдено
    """
    logger.debug(f"double_click_on_image: ищу '{template}'")

    coords = wait_image(template, timeout=timeout, confidence=confidence)

    if coords:
        x, y = coords
        logger.debug(f"double_click_on_image: найдено в ({x}, {y})")
        double_click(x, y, humanize=humanize)
        return True

    logger.warning(f"double_click_on_image: '{template}' не найден")
    return False


def right_click_on_image(
    template: str,
    timeout: float = DEFAULT_TIMEOUT,
    confidence: float = DEFAULT_CONFIDENCE,
    region: Optional[Tuple[int, int, int, int]] = None,
    humanize: bool = True
) -> bool:
    """
    Найти изображение и выполнить правый клик.

    Args:
        template: Путь к изображению-шаблону
        timeout: Время ожидания появления
        confidence: Порог совпадения
        region: Область поиска или None
        humanize: Использовать хуманизацию

    Returns:
        True если клик выполнен, False если не найдено
    """
    logger.debug(f"right_click_on_image: ищу '{template}'")

    coords = wait_image(template, timeout=timeout, confidence=confidence)

    if coords:
        x, y = coords
        logger.debug(f"right_click_on_image: найдено в ({x}, {y})")
        right_click(x, y, humanize=humanize)
        return True

    logger.warning(f"right_click_on_image: '{template}' не найден")
    return False


# ============================================================================
# КОНТЕКСТНЫЕ МЕНЮ
# ============================================================================

def right_click_menu(
    target: str,
    option: str,
    target_timeout: float = DEFAULT_TIMEOUT,
    option_timeout: float = 3.0,
    confidence: float = DEFAULT_CONFIDENCE,
    humanize: bool = True
) -> bool:
    """
    Правый клик по элементу и выбор опции из контекстного меню.

    Args:
        target: Изображение элемента для ПКМ
        option: Изображение опции в меню
        target_timeout: Время ожидания целевого элемента
        option_timeout: Время ожидания появления меню/опции
        confidence: Порог совпадения
        humanize: Использовать хуманизацию

    Returns:
        True если действие выполнено, False при ошибке

    Example:
        right_click_menu("ship_icon.png", "dock_option.png")
    """
    logger.info(f"right_click_menu: '{target}' → '{option}'")

    # 1. Ищем целевой элемент
    target_coords = wait_image(target, timeout=target_timeout, confidence=confidence)
    if not target_coords:
        logger.error(f"right_click_menu: цель '{target}' не найдена")
        return False

    # 2. Правый клик по цели
    x, y = target_coords
    right_click(x, y, humanize=humanize)

    # 3. Ждём появления меню и кликаем по опции
    random_delay(0.2, 0.4)  # Пауза для появления меню

    option_coords = wait_image(option, timeout=option_timeout, confidence=confidence)
    if not option_coords:
        logger.error(f"right_click_menu: опция '{option}' не появилась")
        # Закрываем меню кликом в сторону
        from eve.keyboard import press_key
        press_key("escape")
        return False

    # 4. Кликаем по опции
    ox, oy = option_coords
    click(ox, oy, humanize=humanize)

    logger.info(f"right_click_menu: успешно выбрана опция")
    return True


# ============================================================================
# ОЖИДАНИЕ И ДЕЙСТВИЕ
# ============================================================================

def wait_and_click(
    template: str,
    timeout: float = 30.0,
    confidence: float = DEFAULT_CONFIDENCE,
    interval: float = DEFAULT_INTERVAL,
    humanize: bool = True
) -> bool:
    """
    Ждать появления изображения и кликнуть по нему.

    Более длительное ожидание чем click_on_image (для загрузок, анимаций).

    Args:
        template: Путь к изображению-шаблону
        timeout: Максимальное время ожидания
        confidence: Порог совпадения
        interval: Интервал между проверками
        humanize: Использовать хуманизацию

    Returns:
        True если клик выполнен, False при таймауте
    """
    logger.info(f"wait_and_click: жду '{template}' (до {timeout}s)")

    coords = wait_image(template, timeout=timeout, confidence=confidence, interval=interval)

    if coords:
        x, y = coords
        logger.info(f"wait_and_click: найдено, кликаю")
        click(x, y, humanize=humanize)
        return True

    logger.error(f"wait_and_click: таймаут ожидания '{template}'")
    return False


def wait_and_double_click(
    template: str,
    timeout: float = 30.0,
    confidence: float = DEFAULT_CONFIDENCE,
    interval: float = DEFAULT_INTERVAL,
    humanize: bool = True
) -> bool:
    """
    Ждать появления изображения и выполнить двойной клик.

    Args:
        template: Путь к изображению-шаблону
        timeout: Максимальное время ожидания
        confidence: Порог совпадения
        interval: Интервал между проверками
        humanize: Использовать хуманизацию

    Returns:
        True если клик выполнен, False при таймауте
    """
    logger.info(f"wait_and_double_click: жду '{template}'")

    coords = wait_image(template, timeout=timeout, confidence=confidence, interval=interval)

    if coords:
        x, y = coords
        logger.info(f"wait_and_double_click: найдено, двойной клик")
        double_click(x, y, humanize=humanize)
        return True

    logger.error(f"wait_and_double_click: таймаут")
    return False


# ============================================================================
# ПРОВЕРКА СОСТОЯНИЯ
# ============================================================================

def is_visible(
    template: str,
    confidence: float = DEFAULT_CONFIDENCE,
    region: Optional[Tuple[int, int, int, int]] = None
) -> bool:
    """
    Проверить, видно ли изображение на экране прямо сейчас.

    Args:
        template: Путь к изображению-шаблону
        confidence: Порог совпадения
        region: Область поиска или None

    Returns:
        True если изображение найдено, False если нет
    """
    result = find_image(template, confidence=confidence, region=region)
    return result is not None


def find_on_screen(
    template: str,
    confidence: float = DEFAULT_CONFIDENCE,
    region: Optional[Tuple[int, int, int, int]] = None
) -> Optional[Tuple[int, int]]:
    """
    Найти изображение на экране и вернуть координаты.

    Args:
        template: Путь к изображению-шаблону
        confidence: Порог совпадения
        region: Область поиска или None

    Returns:
        (x, y) центр найденного изображения или None
    """
    return find_image(template, confidence=confidence, region=region)


def wait_until_visible(
    template: str,
    timeout: float = 30.0,
    confidence: float = DEFAULT_CONFIDENCE,
    interval: float = DEFAULT_INTERVAL
) -> Optional[Tuple[int, int]]:
    """
    Ждать появления изображения на экране.

    Args:
        template: Путь к изображению-шаблону
        timeout: Максимальное время ожидания
        confidence: Порог совпадения
        interval: Интервал между проверками

    Returns:
        (x, y) координаты или None при таймауте
    """
    logger.debug(f"wait_until_visible: жду '{template}'")
    return wait_image(template, timeout=timeout, confidence=confidence, interval=interval)


def wait_until_gone(
    template: str,
    timeout: float = 30.0,
    confidence: float = DEFAULT_CONFIDENCE,
    interval: float = DEFAULT_INTERVAL
) -> bool:
    """
    Ждать исчезновения изображения с экрана.

    Полезно для ожидания завершения анимаций (warp tunnel, loading).

    Args:
        template: Путь к изображению-шаблону
        timeout: Максимальное время ожидания
        confidence: Порог совпадения
        interval: Интервал между проверками

    Returns:
        True если изображение исчезло, False при таймауте
    """
    logger.debug(f"wait_until_gone: жду исчезновения '{template}'")
    result = wait_image_disappear(template, timeout=timeout, confidence=confidence, interval=interval)

    if result:
        logger.debug(f"wait_until_gone: '{template}' исчезло")
    else:
        logger.warning(f"wait_until_gone: таймаут, '{template}' всё ещё видно")

    return result


# ============================================================================
# ПОСЛЕДОВАТЕЛЬНОСТИ ДЕЙСТВИЙ
# ============================================================================

def click_sequence(
    templates: List[str],
    timeout: float = DEFAULT_TIMEOUT,
    confidence: float = DEFAULT_CONFIDENCE,
    delay_between: Tuple[float, float] = (0.3, 0.7),
    humanize: bool = True
) -> bool:
    """
    Последовательно кликнуть по нескольким изображениям.

    Args:
        templates: Список изображений для кликов
        timeout: Таймаут для каждого изображения
        confidence: Порог совпадения
        delay_between: (min, max) задержка между кликами
        humanize: Использовать хуманизацию

    Returns:
        True если все клики выполнены, False при первой ошибке
    """
    logger.info(f"click_sequence: {len(templates)} элементов")

    for i, template in enumerate(templates):
        logger.debug(f"click_sequence: [{i+1}/{len(templates)}] '{template}'")

        if not click_on_image(template, timeout=timeout, confidence=confidence, humanize=humanize):
            logger.error(f"click_sequence: не удалось кликнуть '{template}'")
            return False

        # Пауза между кликами (кроме последнего)
        if i < len(templates) - 1:
            random_delay(delay_between[0], delay_between[1])

    logger.info("click_sequence: успешно завершено")
    return True


def hover_on_image(
    template: str,
    timeout: float = DEFAULT_TIMEOUT,
    confidence: float = DEFAULT_CONFIDENCE,
    humanize: bool = True
) -> bool:
    """
    Навести курсор на изображение (без клика).

    Полезно для появления тултипов и hover-эффектов.

    Args:
        template: Путь к изображению-шаблону
        timeout: Время ожидания появления
        confidence: Порог совпадения
        humanize: Использовать хуманизацию

    Returns:
        True если курсор наведён, False если не найдено
    """
    logger.debug(f"hover_on_image: ищу '{template}'")

    coords = wait_image(template, timeout=timeout, confidence=confidence)

    if coords:
        x, y = coords
        logger.debug(f"hover_on_image: наводу на ({x}, {y})")
        move_to(x, y, humanize=humanize)
        return True

    logger.warning(f"hover_on_image: '{template}' не найден")
    return False
