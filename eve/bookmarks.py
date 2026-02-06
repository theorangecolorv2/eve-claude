"""
Модуль для работы с букмарками (локациями) в EVE Online.
"""
import logging
import time
from typing import Optional, List
from core.sanderling.service import SanderlingService
from core.sanderling.models import Bookmark
from eve.mouse import click

logger = logging.getLogger(__name__)


def get_bookmarks(sanderling: SanderlingService) -> List[Bookmark]:
    """
    Получить список всех букмарков.
    
    Args:
        sanderling: Сервис Sanderling
        
    Returns:
        Список букмарков
    """
    state = sanderling.get_state()
    if not state:
        logger.warning("Не удалось получить состояние")
        return []
    
    return state.bookmarks


def find_bookmark(sanderling: SanderlingService, name: str) -> Optional[Bookmark]:
    """
    Найти букмарк по имени.
    
    Args:
        sanderling: Сервис Sanderling
        name: Имя букмарка (может быть частичным)
        
    Returns:
        Букмарк или None если не найден
    """
    bookmarks = get_bookmarks(sanderling)
    
    for bookmark in bookmarks:
        if name.lower() in bookmark.name.lower():
            logger.info(f"Найден букмарк: {bookmark.name} at {bookmark.center}")
            return bookmark
    
    logger.warning(f"Букмарк '{name}' не найден")
    return None


def click_bookmark(sanderling: SanderlingService, name: str, button: str = 'left') -> bool:
    """
    Кликнуть на букмарк по имени.
    
    Args:
        sanderling: Сервис Sanderling
        name: Имя букмарка
        button: Кнопка мыши ('left' или 'right')
        
    Returns:
        True если успешно, False если букмарк не найден
    """
    bookmark = find_bookmark(sanderling, name)
    
    if not bookmark or not bookmark.center:
        logger.error(f"Не удалось найти букмарк '{name}' или у него нет координат")
        return False
    
    logger.info(f"Клик на букмарк '{bookmark.name}' at {bookmark.center}")
    click(bookmark.center[0], bookmark.center[1], button=button)
    time.sleep(0.3)
    
    return True


def right_click_bookmark(sanderling: SanderlingService, name: str) -> bool:
    """
    ПКМ на букмарк по имени.
    
    Args:
        sanderling: Сервис Sanderling
        name: Имя букмарка
        
    Returns:
        True если успешно, False если букмарк не найден
    """
    return click_bookmark(sanderling, name, button='right')


def double_click_bookmark(sanderling: SanderlingService, name: str) -> bool:
    """
    Двойной клик на букмарк по имени.
    
    Args:
        sanderling: Сервис Sanderling
        name: Имя букмарка
        
    Returns:
        True если успешно, False если букмарк не найден
    """
    bookmark = find_bookmark(sanderling, name)
    
    if not bookmark or not bookmark.center:
        logger.error(f"Не удалось найти букмарк '{name}' или у него нет координат")
        return False
    
    logger.info(f"Двойной клик на букмарк '{bookmark.name}' at {bookmark.center}")
    click(bookmark.center[0], bookmark.center[1], button='left')
    time.sleep(0.1)
    click(bookmark.center[0], bookmark.center[1], button='left')
    time.sleep(0.3)
    
    return True


def get_bookmark_coordinates(sanderling: SanderlingService, name: str) -> Optional[tuple]:
    """
    Получить координаты букмарка по имени.
    
    Args:
        sanderling: Сервис Sanderling
        name: Имя букмарка
        
    Returns:
        Кортеж (x, y) или None если не найден
    """
    bookmark = find_bookmark(sanderling, name)
    
    if bookmark and bookmark.center:
        return bookmark.center
    
    return None
