"""
Модуль для входа в Abyss (Бездна).
"""
import logging
from typing import Optional
from core.sanderling.service import SanderlingService
from eve.inventory import InventoryManager
from config import FILAMENT_NAMES

logger = logging.getLogger(__name__)


def enter_abyss(sanderling: SanderlingService, filament_name: str = None) -> bool:
    """
    Войти в Abyss используя филамент.
    
    Автоматически:
    - Открывает инвентарь если закрыт
    - Активирует фильтр !FILAMENT! если не активен
    - Находит и использует филамент
    
    Args:
        sanderling: Сервис Sanderling
        filament_name: Название филамента (по умолчанию Calm Exotic Filament)
        
    Returns:
        True если успешно вошли в Abyss
    """
    if filament_name is None:
        filament_name = FILAMENT_NAMES['CALM_EXOTIC']
    
    logger.info(f"Entering Abyss with filament: {filament_name}")
    
    inventory = InventoryManager(sanderling)
    
    # Используем филамент (все автоматически)
    if not inventory.use_filament(filament_name):
        logger.error("Failed to use filament")
        return False
    
    logger.info("Successfully entered Abyss")
    return True
