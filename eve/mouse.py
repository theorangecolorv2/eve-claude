"""
Eve Framework - Mouse control module with humanization

Хуманизированное управление мышью:
- Bezier curves для плавных движений
- Рандомные задержки между действиями
- Случайное смещение от центра при клике
"""

import time
import random
import logging
from typing import Optional, Tuple, List
import pyautogui

# Disable PyAutoGUI failsafe (move mouse to corner to abort)
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0  # Мы сами контролируем паузы

logger = logging.getLogger(__name__)


# ============================================================================
# НАСТРОЙКИ ХУМАНИЗАЦИИ
# ============================================================================

class HumanConfig:
    """Настройки хуманизации - можно менять под свои нужды."""

    # Движение мыши
    MOVE_DURATION_MIN = 0.08        # Минимальное время движения (сек) - быстрее
    MOVE_DURATION_MAX = 0.25        # Максимальное время движения (сек) - быстрее
    MOVE_STEPS_PER_SECOND = 120     # Точек в секунду (плавность)

    # Bezier curve
    BEZIER_CONTROL_POINTS = 2       # Количество контрольных точек (2-3)
    BEZIER_DEVIATION_MIN = 2        # Минимальное отклонение контрольных точек (px)
    BEZIER_DEVIATION_MAX = 40       # Максимальное отклонение (px)

    # Клики
    CLICK_OFFSET_MAX = 3            # Максимальное смещение от центра (px)
    CLICK_DELAY_MIN = 0.02          # Задержка перед кликом (сек)
    CLICK_DELAY_MAX = 0.08          # Максимальная задержка
    CLICK_DURATION_MIN = 0.05       # Время удержания кнопки
    CLICK_DURATION_MAX = 0.12

    # Между действиями
    ACTION_DELAY_MIN = 0.1          # Пауза между действиями
    ACTION_DELAY_MAX = 0.25


# ============================================================================
# BEZIER CURVE
# ============================================================================

def _bezier_point(t: float, points: List[Tuple[float, float]]) -> Tuple[float, float]:
    """
    Вычислить точку на кривой Безье.

    Args:
        t: Параметр от 0 до 1
        points: Контрольные точки [(x1,y1), (x2,y2), ...]

    Returns:
        (x, y) точка на кривой
    """
    n = len(points) - 1
    x = 0.0
    y = 0.0

    for i, (px, py) in enumerate(points):
        # Биномиальный коэффициент
        binom = 1
        for j in range(min(i, n - i)):
            binom = binom * (n - j) // (j + 1)

        # Полином Бернштейна
        bernstein = binom * (t ** i) * ((1 - t) ** (n - i))
        x += px * bernstein
        y += py * bernstein

    return (x, y)


def _generate_bezier_path(
    start: Tuple[int, int],
    end: Tuple[int, int],
    duration: float
) -> List[Tuple[int, int]]:
    """
    Генерировать путь движения мыши по кривой Безье.

    Args:
        start: Начальная точка (x, y)
        end: Конечная точка (x, y)
        duration: Время движения в секундах

    Returns:
        Список точек для движения
    """
    # Количество шагов
    num_steps = max(10, int(duration * HumanConfig.MOVE_STEPS_PER_SECOND))

    # Расстояние между точками
    distance = ((end[0] - start[0])**2 + (end[1] - start[1])**2) ** 0.5

    # Отклонение пропорционально расстоянию (но в пределах)
    # Для коротких расстояний (<50px) отклонение минимально
    deviation = min(
        HumanConfig.BEZIER_DEVIATION_MAX,
        max(HumanConfig.BEZIER_DEVIATION_MIN, distance * 0.08)
    )

    # Генерируем контрольные точки
    control_points = [start]

    for i in range(HumanConfig.BEZIER_CONTROL_POINTS):
        # Равномерно распределяем контрольные точки
        t = (i + 1) / (HumanConfig.BEZIER_CONTROL_POINTS + 1)

        # Базовая позиция на прямой линии
        base_x = start[0] + (end[0] - start[0]) * t
        base_y = start[1] + (end[1] - start[1]) * t

        # Добавляем случайное отклонение
        offset_x = random.uniform(-deviation, deviation)
        offset_y = random.uniform(-deviation, deviation)

        control_points.append((base_x + offset_x, base_y + offset_y))

    control_points.append(end)

    # Генерируем путь
    path = []
    for i in range(num_steps + 1):
        t = i / num_steps
        point = _bezier_point(t, control_points)
        path.append((int(point[0]), int(point[1])))

    return path


# ============================================================================
# ОСНОВНЫЕ ФУНКЦИИ ДВИЖЕНИЯ
# ============================================================================

def get_position() -> Tuple[int, int]:
    """Получить текущую позицию курсора."""
    return pyautogui.position()


def move_to(
    x: int,
    y: int,
    duration: Optional[float] = None,
    humanize: bool = True
) -> None:
    """
    Переместить курсор в указанную позицию.

    Args:
        x, y: Целевые координаты
        duration: Время перемещения (None = автоматически)
        humanize: Использовать хуманизацию (Bezier curve)
    """
    if not humanize:
        # Прямое движение без хуманизации
        pyautogui.moveTo(x, y, duration=duration or 0.1)
        return

    current = get_position()

    # Автоматическое время на основе расстояния
    if duration is None:
        distance = ((x - current[0])**2 + (y - current[1])**2) ** 0.5
        # Больше расстояние = больше времени (но в пределах)
        duration = min(
            HumanConfig.MOVE_DURATION_MAX,
            max(
                HumanConfig.MOVE_DURATION_MIN,
                distance / 2000  # ~500px/sec
            )
        )

    # Генерируем путь
    path = _generate_bezier_path(current, (x, y), duration)

    if len(path) < 2:
        pyautogui.moveTo(x, y)
        return

    # Время между шагами
    step_delay = duration / len(path)

    # Двигаемся по точкам
    for point in path[1:]:  # Пропускаем первую (текущую позицию)
        pyautogui.moveTo(point[0], point[1], duration=0, _pause=False)
        time.sleep(step_delay)


def move_mouse(x: int, y: int, duration: Optional[float] = None) -> None:
    """
    Переместить мышь в указанную позицию (алиас для move_to с хуманизацией).
    
    Args:
        x, y: Целевые координаты
        duration: Время перемещения (None = автоматически)
    """
    move_to(x, y, duration=duration, humanize=True)


# ============================================================================
# ФУНКЦИИ КЛИКОВ
# ============================================================================

def _apply_click_offset(x: int, y: int) -> Tuple[int, int]:
    """Добавить случайное смещение к точке клика."""
    offset_x = random.randint(-HumanConfig.CLICK_OFFSET_MAX, HumanConfig.CLICK_OFFSET_MAX)
    offset_y = random.randint(-HumanConfig.CLICK_OFFSET_MAX, HumanConfig.CLICK_OFFSET_MAX)
    return (x + offset_x, y + offset_y)


def _human_click_delay() -> None:
    """Случайная задержка перед/после клика."""
    delay = random.uniform(HumanConfig.CLICK_DELAY_MIN, HumanConfig.CLICK_DELAY_MAX)
    time.sleep(delay)


def click(
    x: int,
    y: int,
    button: str = "left",
    humanize: bool = True,
    duration: Optional[float] = None
) -> None:
    """
    Клик по координатам.

    Args:
        x, y: Координаты
        button: "left", "right", или "middle"
        humanize: Использовать хуманизацию
        duration: Время движения мыши (None = автоматически)
    """
    if humanize:
        # Смещение от точной точки
        x, y = _apply_click_offset(x, y)

        # Плавное движение к цели
        move_to(x, y, humanize=True, duration=duration)

        # Пауза перед кликом
        _human_click_delay()

        # Клик с реалистичным временем удержания
        click_duration = random.uniform(
            HumanConfig.CLICK_DURATION_MIN,
            HumanConfig.CLICK_DURATION_MAX
        )
        pyautogui.mouseDown(button=button, _pause=False)
        time.sleep(click_duration)
        pyautogui.mouseUp(button=button, _pause=False)

        # Небольшая пауза после клика
        _human_click_delay()
    else:
        pyautogui.click(x, y, button=button)


def double_click(x: int, y: int, humanize: bool = True) -> None:
    """
    Двойной клик по координатам.

    Args:
        x, y: Координаты
        humanize: Использовать хуманизацию
    """
    if humanize:
        x, y = _apply_click_offset(x, y)
        move_to(x, y, humanize=True)
        _human_click_delay()

        # Два клика с небольшим интервалом
        for i in range(2):
            click_duration = random.uniform(
                HumanConfig.CLICK_DURATION_MIN,
                HumanConfig.CLICK_DURATION_MAX
            )
            pyautogui.mouseDown(button="left", _pause=False)
            time.sleep(click_duration)
            pyautogui.mouseUp(button="left", _pause=False)

            if i == 0:
                # Пауза между кликами (важно для double-click)
                time.sleep(random.uniform(0.05, 0.12))

        _human_click_delay()
    else:
        pyautogui.doubleClick(x, y)


def right_click(x: int, y: int, humanize: bool = True, duration: Optional[float] = None) -> None:
    """
    Правый клик по координатам.

    Args:
        x, y: Координаты
        humanize: Использовать хуманизацию
        duration: Время движения мыши (None = автоматически)
    """
    click(x, y, button="right", humanize=humanize, duration=duration)


def middle_click(x: int, y: int, humanize: bool = True) -> None:
    """
    Средний клик (колёсико) по координатам.

    Args:
        x, y: Координаты
        humanize: Использовать хуманизацию
    """
    click(x, y, button="middle", humanize=humanize)


# ============================================================================
# DRAG & DROP
# ============================================================================

def drag(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    duration: Optional[float] = None,
    button: str = "left",
    humanize: bool = True
) -> None:
    """
    Перетащить от одной точки к другой.

    Args:
        start_x, start_y: Начальные координаты
        end_x, end_y: Конечные координаты
        duration: Время перетаскивания (None = автоматически)
        button: Кнопка мыши
        humanize: Использовать хуманизацию
    """
    if humanize:
        # Двигаемся к начальной точке
        move_to(start_x, start_y, humanize=True)
        _human_click_delay()

        # Зажимаем кнопку
        pyautogui.mouseDown(button=button, _pause=False)
        time.sleep(random.uniform(0.05, 0.1))

        # Перетаскиваем
        if duration is None:
            distance = ((end_x - start_x)**2 + (end_y - start_y)**2) ** 0.5
            duration = max(0.3, min(1.0, distance / 800))

        move_to(end_x, end_y, duration=duration, humanize=True)

        time.sleep(random.uniform(0.05, 0.1))
        pyautogui.mouseUp(button=button, _pause=False)
        _human_click_delay()
    else:
        pyautogui.moveTo(start_x, start_y)
        pyautogui.drag(end_x - start_x, end_y - start_y, duration=duration or 0.5, button=button)


# ============================================================================
# SCROLL
# ============================================================================

def scroll(
    clicks: int,
    x: Optional[int] = None,
    y: Optional[int] = None,
    humanize: bool = True
) -> None:
    """
    Прокрутка колесом мыши.

    Args:
        clicks: Количество "щелчков" (положительное = вверх, отрицательное = вниз)
        x, y: Координаты (опционально)
        humanize: Использовать хуманизацию
    """
    if humanize and x is not None and y is not None:
        move_to(x, y, humanize=True)
        _human_click_delay()

    if humanize:
        # Прокручиваем по частям с паузами
        direction = 1 if clicks > 0 else -1
        remaining = abs(clicks)

        while remaining > 0:
            # Случайное количество за раз (1-3)
            chunk = min(remaining, random.randint(1, 3))
            pyautogui.scroll(chunk * direction, x, y)
            remaining -= chunk

            if remaining > 0:
                time.sleep(random.uniform(0.05, 0.15))
    else:
        pyautogui.scroll(clicks, x, y)


# ============================================================================
# УТИЛИТЫ
# ============================================================================

def random_delay(min_sec: float = None, max_sec: float = None) -> None:
    """
    Случайная пауза между действиями.

    Args:
        min_sec: Минимальное время (по умолчанию из конфига)
        max_sec: Максимальное время (по умолчанию из конфига)
    """
    min_sec = min_sec or HumanConfig.ACTION_DELAY_MIN
    max_sec = max_sec or HumanConfig.ACTION_DELAY_MAX
    time.sleep(random.uniform(min_sec, max_sec))
