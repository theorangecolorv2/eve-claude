"""
Модуль для работы с инвентарем EVE Online через Sanderling.
"""
import time
import logging
from typing import Optional, Tuple
from core.sanderling.service import SanderlingService
from core.sanderling.models import InventoryFilter, InventoryItem, ContextMenuItem
from config import INVENTORY_FILTERS, CONTEXT_MENU_ACTIONS, DELAY_AFTER_CLICK, DELAY_BETWEEN_ACTIONS
from eve.mouse import click, right_click

logger = logging.getLogger(__name__)


class InventoryManager:
    """Менеджер для работы с инвентарем."""
    
    def __init__(self, sanderling: SanderlingService):
        """
        Инициализация менеджера.
        
        Args:
            sanderling: Сервис Sanderling
        """
        self.sanderling = sanderling
    
    def is_open(self) -> bool:
        """
        Проверить открыт ли инвентарь.
        
        Returns:
            True если инвентарь открыт
        """
        state = self.sanderling.get_state()
        return state and state.inventory and state.inventory.is_open
    
    def open_inventory(self) -> bool:
        """
        Открыть инвентарь через клик по кнопке Inventory в Neocom (боковая панель слева).
        
        Returns:
            True если инвентарь открыт
        """
        if self.is_open():
            logger.info("Инвентарь уже открыт")
            return True
        
        logger.info("Открываю инвентарь...")
        
        # Клик по кнопке Inventory в Neocom
        state = self.sanderling.get_state()
        if not state or not state.neocom_buttons:
            logger.error("Не удалось получить кнопки Neocom")
            return False
        
        inventory_button = None
        for button in state.neocom_buttons:
            if button.button_type == 'inventory':
                inventory_button = button
                break
        
        if not inventory_button:
            logger.error("Кнопка Inventory не найдена в Neocom")
            logger.info("Доступные кнопки: " + ", ".join([b.button_type for b in state.neocom_buttons]))
            return False
        
        logger.info(f"Кликаю по кнопке Inventory в {inventory_button.center}")
        click(inventory_button.center[0], inventory_button.center[1])
        
        # Ждем пока Sanderling перечитает интерфейс (несколько попыток)
        max_attempts = 5
        for attempt in range(max_attempts):
            time.sleep(0.5)  # Даем время Sanderling на чтение
            
            if self.is_open():
                logger.info(f"Инвентарь открыт (попытка {attempt + 1}/{max_attempts})")
                return True
            
            logger.debug(f"Попытка {attempt + 1}/{max_attempts}: инвентарь еще не открыт...")
        
        logger.warning("Инвентарь не открылся после клика")
        return False
    
    def get_filter(self, filter_name: str) -> Optional[InventoryFilter]:
        """
        Найти фильтр по имени.
        
        Args:
            filter_name: Название фильтра (из config.INVENTORY_FILTERS)
            
        Returns:
            InventoryFilter или None
        """
        state = self.sanderling.get_state()
        if not state or not state.inventory:
            return None
        
        for f in state.inventory.filters:
            if f.name == filter_name:
                return f
        
        return None
    
    def activate_filter(self, filter_name: str) -> bool:
        """Активировать фильтр инвентаря."""
        filter_obj = self.get_filter(filter_name)
        if not filter_obj:
            logger.error(f"Filter '{filter_name}' not found")
            return False
        
        if filter_obj.is_active:
            logger.info(f"Filter '{filter_name}' already active")
            return True
        
        logger.info(f"Activate filter '{filter_name}' at {filter_obj.center}")
        click(filter_obj.center[0], filter_obj.center[1])
        
        # Даем время на обновление списка предметов
        time.sleep(0.5)
        
        return True
    
    def find_item(self, item_name: str) -> Optional[InventoryItem]:
        """
        Найти предмет в инвентаре.
        
        Args:
            item_name: Название предмета (может быть частичным)
            
        Returns:
            InventoryItem или None
        """
        state = self.sanderling.get_state()
        if not state or not state.inventory:
            return None
        
        for item in state.inventory.items:
            if item_name.lower() in item.name.lower():
                return item
            if item.hint and item_name.lower() in item.hint.lower():
                return item
        
        return None
    
    def right_click_item(self, item: InventoryItem) -> bool:
        """Правый клик по предмету."""
        if not item or not item.center:
            logger.error("Item has no coordinates")
            return False
        
        logger.info(f"Right click: {item.name} at {item.center}")
        right_click(item.center[0], item.center[1])
        time.sleep(DELAY_BETWEEN_ACTIONS)
        return True
    
    def click_context_menu_item(self, menu_text: str) -> bool:
        """Кликнуть по пункту контекстного меню."""
        state = self.sanderling.get_state()
        if not state or not state.context_menu or not state.context_menu.is_open:
            logger.error(f"Context menu not open. state={state is not None}, context_menu={state.context_menu if state else None}")
            return False
        
        logger.debug(f"Context menu items: {[item.text for item in state.context_menu.items]}")
        
        for item in state.context_menu.items:
            if menu_text.lower() in item.text.lower():
                logger.info(f"Click menu: '{item.text}' at {item.center}")
                click(item.center[0], item.center[1])
                time.sleep(DELAY_AFTER_CLICK)
                return True
        
        logger.error(f"Menu item '{menu_text}' not found. Available: {[item.text for item in state.context_menu.items]}")
        return False
    
    def use_item(self, item_name: str) -> bool:
        """Использовать предмет из инвентаря."""
        item = self.find_item(item_name)
        if not item:
            logger.error(f"Item '{item_name}' not found")
            return False
        
        logger.info(f"Using item: {item.name}")
        
        # Правый клик
        if not self.right_click_item(item):
            return False
        
        # Ждем дольше чтобы Sanderling успел распарсить меню
        max_attempts = 3
        for attempt in range(max_attempts):
            time.sleep(DELAY_BETWEEN_ACTIONS)
            
            state = self.sanderling.get_state()
            if state and state.context_menu and state.context_menu.is_open:
                logger.debug(f"Context menu opened with {len(state.context_menu.items)} items")
                break
            
            logger.debug(f"Attempt {attempt + 1}/{max_attempts}: waiting for context menu...")
        else:
            logger.error("Context menu did not open after right click")
            return False
        
        # Кликнуть "Использовать"
        if not self.click_context_menu_item(CONTEXT_MENU_ACTIONS['USE']):
            if not self.click_context_menu_item(CONTEXT_MENU_ACTIONS['USE_EN']):
                return False
        
        logger.info(f"Item used: {item.name}")
        return True
    
    def use_filament(self, filament_name: str) -> bool:
        """
        Использовать филамент (полный автоматический цикл).
        
        Выполняет:
        1. Открывает инвентарь если закрыт
        2. Активирует фильтр !FILAMENT! если не активен
        3. Находит филамент
        4. Делает правый клик
        5. Кликает "Использовать"
        
        Args:
            filament_name: Название филамента (из config.FILAMENT_NAMES)
            
        Returns:
            True если успешно
        """
        logger.info(f"Использую филамент: {filament_name}")
        
        # Шаг 1: Открыть инвентарь если закрыт
        if not self.is_open():
            logger.info("Инвентарь закрыт, открываю...")
            if not self.open_inventory():
                logger.error("Не удалось открыть инвентарь")
                return False
        
        # Шаг 2: Активировать фильтр !FILAMENT! если не активен
        logger.info("Проверяю фильтр филаментов...")
        if not self.activate_filter(INVENTORY_FILTERS['FILAMENT']):
            logger.warning("Не удалось активировать фильтр филаментов")
            # Продолжаем, возможно филамент все равно виден
        
        # Подождать обновления списка предметов после фильтра
        # Sanderling должен перечитать инвентарь
        time.sleep(1.0)
        
        # Шаг 3-5: Использовать филамент
        logger.info(f"Ищу и использую филамент: {filament_name}")
        return self.use_item(filament_name)
