"""
Eve Framework - Window management module
"""

import time
from typing import Optional, List, Dict
import pygetwindow as gw


def list_windows(filter_text: Optional[str] = None) -> List[Dict]:
    """
    Получить список всех окон.

    Args:
        filter_text: Фильтр по заголовку (case-insensitive)

    Returns:
        Список словарей с информацией об окнах
    """
    windows = gw.getAllWindows()
    windows = [w for w in windows if w.title.strip()]

    if filter_text:
        filter_lower = filter_text.lower()
        windows = [w for w in windows if filter_lower in w.title.lower()]

    result = []
    for w in windows:
        result.append({
            "title": w.title,
            "left": w.left,
            "top": w.top,
            "width": w.width,
            "height": w.height,
            "is_active": w.isActive,
            "is_minimized": w.isMinimized,
            "is_maximized": w.isMaximized,
        })

    return result


def activate_window(title: str, timeout: float = 5) -> bool:
    """
    Найти и активировать окно по части заголовка.

    Args:
        title: Часть заголовка окна
        timeout: Время ожидания активации

    Returns:
        True если окно активировано, False если не найдено
    """
    windows = gw.getWindowsWithTitle(title)

    if not windows:
        return False

    win = windows[0]

    try:
        if win.isMinimized:
            win.restore()

        win.activate()

        # Wait for activation
        start = time.time()
        while time.time() - start < timeout:
            if win.isActive:
                return True
            time.sleep(0.1)

        return win.isActive
    except Exception:
        return False


def get_active_window() -> Optional[Dict]:
    """
    Получить информацию об активном окне.

    Returns:
        Словарь с информацией или None
    """
    try:
        win = gw.getActiveWindow()
        if win:
            return {
                "title": win.title,
                "left": win.left,
                "top": win.top,
                "width": win.width,
                "height": win.height,
            }
    except Exception:
        pass
    return None


def minimize_window(title: str) -> bool:
    """Свернуть окно."""
    windows = gw.getWindowsWithTitle(title)
    if not windows:
        return False

    try:
        windows[0].minimize()
        return True
    except Exception:
        return False


def maximize_window(title: str) -> bool:
    """Развернуть окно на весь экран."""
    windows = gw.getWindowsWithTitle(title)
    if not windows:
        return False

    try:
        windows[0].maximize()
        return True
    except Exception:
        return False


def close_window(title: str) -> bool:
    """Закрыть окно."""
    windows = gw.getWindowsWithTitle(title)
    if not windows:
        return False

    try:
        windows[0].close()
        return True
    except Exception:
        return False


def move_window(title: str, x: int, y: int) -> bool:
    """Переместить окно."""
    windows = gw.getWindowsWithTitle(title)
    if not windows:
        return False

    try:
        windows[0].moveTo(x, y)
        return True
    except Exception:
        return False


def resize_window(title: str, width: int, height: int) -> bool:
    """Изменить размер окна."""
    windows = gw.getWindowsWithTitle(title)
    if not windows:
        return False

    try:
        windows[0].resizeTo(width, height)
        return True
    except Exception:
        return False
