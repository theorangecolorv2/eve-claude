"""
Eve Framework - Mouse control module
"""

import time
from typing import Optional
import pyautogui

from eve.vision import find_image, wait_image

# Disable PyAutoGUI failsafe (move mouse to corner to abort)
# Enable if needed for safety
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1  # Small pause between actions


def move_to(x: int, y: int, duration: float = 0.2):
    """
    Переместить курсор в указанную позицию.

    Args:
        x, y: Координаты
        duration: Время перемещения (секунды)
    """
    pyautogui.moveTo(x, y, duration=duration)


def click(x: int, y: int, button: str = "left"):
    """
    Клик по координатам.

    Args:
        x, y: Координаты
        button: "left", "right", или "middle"
    """
    pyautogui.click(x, y, button=button)


def double_click(x: int, y: int):
    """Двойной клик по координатам."""
    pyautogui.doubleClick(x, y)


def right_click(x: int, y: int):
    """Правый клик по координатам."""
    pyautogui.rightClick(x, y)


def click_on_image(template: str, timeout: float = 10, confidence: float = 0.9, button: str = "left") -> bool:
    """
    Найти изображение на экране и кликнуть по нему.

    Args:
        template: Путь к изображению-шаблону
        timeout: Время ожидания появления
        confidence: Порог совпадения
        button: Кнопка мыши

    Returns:
        True если клик выполнен, False если изображение не найдено
    """
    coords = wait_image(template, timeout=timeout, confidence=confidence)

    if coords:
        x, y = coords
        click(x, y, button=button)
        return True

    return False


def drag(start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5, button: str = "left"):
    """
    Перетащить от одной точки к другой.

    Args:
        start_x, start_y: Начальные координаты
        end_x, end_y: Конечные координаты
        duration: Время перетаскивания
        button: Кнопка мыши
    """
    pyautogui.moveTo(start_x, start_y)
    pyautogui.drag(end_x - start_x, end_y - start_y, duration=duration, button=button)


def scroll(clicks: int, x: Optional[int] = None, y: Optional[int] = None):
    """
    Прокрутка колесом мыши.

    Args:
        clicks: Количество "щелчков" (положительное = вверх, отрицательное = вниз)
        x, y: Координаты (опционально, текущая позиция если не указано)
    """
    pyautogui.scroll(clicks, x, y)
