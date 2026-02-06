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
    
    def stack_all_items(self, item_name: str) -> bool:
        """
        Сложить все предметы в стопки через контекстное меню.
        
        Делает ПКМ по указанному предмету и выбирает "Сложить все предметы в стопки".
        
        Args:
            item_name: Название предмета для клика
            
        Returns:
            True если успешно
        """
        logger.info("Складываю все предметы в стопки...")
        
        # Ищем предмет
        item = self.find_item(item_name)
        if not item:
            logger.error(f"Предмет '{item_name}' не найден")
            return False
        
        logger.info(f"Делаю ПКМ по предмету: {item.name}")
        
        # Правый клик
        if not self.right_click_item(item):
            return False
        
        # Ждем появления меню
        max_attempts = 3
        for attempt in range(max_attempts):
            time.sleep(DELAY_BETWEEN_ACTIONS)
            
            state = self.sanderling.get_state()
            if state and state.context_menu and state.context_menu.is_open:
                logger.debug(f"Контекстное меню открыто с {len(state.context_menu.items)} пунктами")
                break
            
            logger.debug(f"Попытка {attempt + 1}/{max_attempts}: жду открытия контекстного меню...")
        else:
            logger.error("Контекстное меню не открылось после ПКМ")
            return False
        
        # Кликнуть "Сложить все предметы в стопки"
        if not self.click_context_menu_item(CONTEXT_MENU_ACTIONS['STACK_ALL']):
            if not self.click_context_menu_item(CONTEXT_MENU_ACTIONS['STACK_ALL_EN']):
                logger.error("Не удалось найти пункт меню 'Stack All'")
                return False
        
        logger.info("Предметы складываются в стопки, жду завершения...")
        time.sleep(2.0)  # Ждем пока предметы сложатся
        
        return True
    
    def use_filament(self, filament_name: str) -> bool:
        """
        Использовать филамент (полный автоматический цикл).
        
        Выполняет:
        1. Открывает инвентарь если закрыт
        2. Активирует фильтр !FILAMENT! если не активен
        3. Складывает все филаменты в стопки (Stack All)
        4. Находит филамент
        5. Делает правый клик
        6. Кликает "Использовать"
        7. Ждет появления кнопки "Активировать для флота"
        8. Кликает "Активировать для флота"
        
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
        
        # Шаг 2: Активировать фильтр !FILAMENT!
        logger.info("Активирую фильтр филаментов...")
        filter_obj = self.get_filter(INVENTORY_FILTERS['FILAMENT'])
        if not filter_obj:
            logger.error("Фильтр !FILAMENT! не найден")
            return False
        
        # Кликаем по фильтру
        logger.info(f"Кликаю по фильтру в {filter_obj.center}")
        click(filter_obj.center[0], filter_obj.center[1])
        
        # Ждем обновления инвентаря
        logger.info("Жду обновления инвентаря после фильтра...")
        time.sleep(2.0)
        
        # Проверяем появился ли филамент
        item = self.find_item(filament_name)
        if not item:
            # Филамент не появился, значит фильтр был включен и мы его выключили
            # Кликаем еще раз чтобы включить обратно
            logger.info("Филамент не появился, кликаю по фильтру еще раз...")
            click(filter_obj.center[0], filter_obj.center[1])
            time.sleep(2.0)
        
        # Шаг 3: Сложить все филаменты в стопки
        logger.info("Складываю филаменты в стопки...")
        if not self.stack_all_items(filament_name):
            logger.warning("Не удалось сложить предметы в стопки, продолжаю...")
            # Продолжаем даже если не получилось - возможно уже сложены
        
        # Ждем обновления инвентаря после складывания
        time.sleep(1.0)
        
        # Шаг 4-6: Использовать филамент
        logger.info(f"Ищу и использую филамент: {filament_name}")
        if not self.use_item(filament_name):
            return False
        
        # Шаг 7-8: Ждем кнопку "Активировать для флота" и кликаем
        logger.info("Жду появления кнопки 'Активировать для флота'...")
        if not self.click_activate_fleet_button():
            logger.warning("Не удалось нажать кнопку 'Активировать для флота'")
            return False
        
        logger.info("Кнопка 'Активировать для флота' нажата")
        
        # Шаг 9: Ждем появления Abyssal Trace в Overview
        logger.info("Жду появления Abyssal Trace в Overview...")
        if not self.wait_and_jump_abyssal_trace():
            logger.warning("Не удалось прыгнуть через Abyssal Trace")
            return False
        
        # Шаг 10: Ждем появления финальной кнопки "Активировать" и нажимаем
        logger.info("Жду появления финальной кнопки 'Активировать'...")
        if not self.click_final_activate_button():
            logger.warning("Не удалось нажать финальную кнопку 'Активировать'")
            return False
        
        logger.info("Филамент успешно активирован и вход в абисс выполнен!")
        return True
    
    def click_activate_fleet_button(self, timeout: float = 10.0) -> bool:
        """
        Ждет появления кнопки "Активировать для флота" и кликает по ней.
        
        Args:
            timeout: Максимальное время ожидания в секундах
            
        Returns:
            True если успешно
        """
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            state = self.sanderling.get_state()
            
            # Ищем кнопку ActivateButton с текстом "Активировать для флота"
            if state and state.ui_tree:
                button = self._find_activate_button(state.ui_tree)
                if button:
                    x = button.get('_displayX', 0)
                    y = button.get('_displayY', 0)
                    w = button.get('_displayWidth', 0)
                    h = button.get('_displayHeight', 0)
                    
                    center_x = x + w // 2
                    center_y = y + h // 2
                    
                    logger.info(f"Найдена кнопка 'Активировать для флота' в ({center_x}, {center_y})")
                    click(center_x, center_y)
                    time.sleep(DELAY_AFTER_CLICK)
                    return True
            
            time.sleep(0.5)
        
        logger.error(f"Кнопка 'Активировать для флота' не появилась за {timeout} секунд")
        return False
    
    def wait_and_jump_abyssal_trace(self, timeout: float = 30.0) -> bool:
        """
        Ждет появления Abyssal Trace в Overview и прыгает через него.
        
        Args:
            timeout: Максимальное время ожидания в секундах
            
        Returns:
            True если успешно
        """
        import time
        start_time = time.time()
        
        logger.info("Ищу Abyssal Trace в Overview...")
        
        # Шаг 1: Ждем появления Abyssal Trace в Overview
        abyssal_trace = None
        while time.time() - start_time < timeout:
            state = self.sanderling.get_state()
            
            if not state or not state.overview:
                time.sleep(0.5)
                continue
            
            # Ищем Abyssal Trace в Overview
            for entry in state.overview:
                if entry.name and 'Abyssal Trace' in entry.name:
                    abyssal_trace = entry
                    break
            
            if abyssal_trace and abyssal_trace.center:
                logger.info(f"Найден Abyssal Trace в {abyssal_trace.center}")
                break
            
            time.sleep(0.5)
        
        if not abyssal_trace:
            logger.error(f"Abyssal Trace не появился за {timeout} секунд")
            return False
        
        # Шаг 2: Кликаем по Abyssal Trace
        logger.info("Кликаю по Abyssal Trace...")
        click(abyssal_trace.center[0], abyssal_trace.center[1])
        time.sleep(DELAY_AFTER_CLICK)
        
        # Шаг 3: Ждем появления кнопки Jump/Activate в selected_actions
        logger.info("Жду появления кнопки активации...")
        jump_timeout = 10.0
        jump_start = time.time()
        
        while time.time() - jump_start < jump_timeout:
            state = self.sanderling.get_state()
            
            if state and state.selected_actions:
                for action in state.selected_actions:
                    if action.name and ('jump' in action.name.lower() or 'activate' in action.name.lower()):
                        logger.info(f"Найдена кнопка активации '{action.name}' в {action.center}")
                        click(action.center[0], action.center[1])
                        time.sleep(DELAY_AFTER_CLICK)
                        logger.info("Прыжок через Abyssal Trace выполнен!")
                        return True
            
            time.sleep(0.5)
        
        logger.error(f"Кнопка активации не появилась за {jump_timeout} секунд")
        return False
    
    def click_final_activate_button(self, timeout: float = 10.0) -> bool:
        """
        Ждет появления финальной кнопки "Активировать" и кликает по ней.
        
        Это последняя кнопка перед входом в абисс.
        
        Args:
            timeout: Максимальное время ожидания в секундах
            
        Returns:
            True если успешно
        """
        import time
        start_time = time.time()
        
        logger.info("Ищу финальную кнопку 'Активировать'...")
        
        while time.time() - start_time < timeout:
            state = self.sanderling.get_state()
            
            # Ищем кнопку ActivateButton с текстом "Активировать"
            if state and state.ui_tree:
                button = self._find_final_activate_button(state.ui_tree)
                if button:
                    x = button.get('_displayX', 0)
                    y = button.get('_displayY', 0)
                    w = button.get('_displayWidth', 0)
                    h = button.get('_displayHeight', 0)
                    
                    center_x = x + w // 2
                    center_y = y + h // 2
                    
                    logger.info(f"Найдена финальная кнопка 'Активировать' в ({center_x}, {center_y})")
                    click(center_x, center_y)
                    time.sleep(DELAY_AFTER_CLICK)
                    logger.info("Финальная кнопка 'Активировать' нажата!")
                    return True
            
            time.sleep(0.5)
        
        logger.error(f"Финальная кнопка 'Активировать' не появилась за {timeout} секунд")
        return False
    
    def _find_final_activate_button(self, node, parent_x=0, parent_y=0) -> dict:
        """Рекурсивно ищет финальную кнопку ActivateButton с текстом 'Активировать'."""
        if not isinstance(node, dict):
            return None
        
        # Получаем координаты текущего узла
        dict_entries = node.get('dictEntriesOfInterest', {})
        display_x = dict_entries.get('_displayX', 0)
        display_y = dict_entries.get('_displayY', 0)
        
        # Обрабатываем случай когда координаты - словари с int_low32
        if isinstance(display_x, dict):
            display_x = display_x.get('int_low32', 0)
        if isinstance(display_y, dict):
            display_y = display_y.get('int_low32', 0)
        
        # Проверяем что координаты - числа
        if not isinstance(display_x, (int, float)):
            display_x = 0
        if not isinstance(display_y, (int, float)):
            display_y = 0
            
        current_x = parent_x + display_x
        current_y = parent_y + display_y
        
        # Проверяем тип узла
        if node.get('pythonObjectTypeName') == 'ActivateButton':
            # Ищем дочерний EveLabelMedium с текстом "Активировать" (БЕЗ "для флота")
            children = node.get('children', [])
            if isinstance(children, list):
                for child in children:
                    if isinstance(child, dict):
                        if child.get('pythonObjectTypeName') == 'EveLabelMedium':
                            child_dict = child.get('dictEntriesOfInterest', {})
                            text = child_dict.get('_setText', '')
                            # Ищем просто "Активировать", а не "Активировать для флота"
                            if text == 'Активировать' or text == 'Activate':
                                # Возвращаем абсолютные координаты кнопки
                                w = dict_entries.get('_displayWidth', 0)
                                h = dict_entries.get('_displayHeight', 0)
                                if isinstance(w, dict):
                                    w = w.get('int_low32', 0)
                                if isinstance(h, dict):
                                    h = h.get('int_low32', 0)
                                if not isinstance(w, (int, float)):
                                    w = 0
                                if not isinstance(h, (int, float)):
                                    h = 0
                                return {
                                    '_displayX': current_x,
                                    '_displayY': current_y,
                                    '_displayWidth': w,
                                    '_displayHeight': h
                                }
        
        # Рекурсивный поиск в детях
        children = node.get('children')
        if isinstance(children, list):
            for child in children:
                result = self._find_final_activate_button(child, current_x, current_y)
                if result:
                    return result
        
        return None
    
    def _find_activate_button(self, node, parent_x=0, parent_y=0) -> dict:
        """Рекурсивно ищет кнопку ActivateButton с текстом 'Активировать для флота'."""
        if not isinstance(node, dict):
            return None
        
        # Получаем координаты текущего узла
        dict_entries = node.get('dictEntriesOfInterest', {})
        display_x = dict_entries.get('_displayX', 0)
        display_y = dict_entries.get('_displayY', 0)
        
        # Обрабатываем случай когда координаты - словари с int_low32
        if isinstance(display_x, dict):
            display_x = display_x.get('int_low32', 0)
        if isinstance(display_y, dict):
            display_y = display_y.get('int_low32', 0)
        
        # Проверяем что координаты - числа
        if not isinstance(display_x, (int, float)):
            display_x = 0
        if not isinstance(display_y, (int, float)):
            display_y = 0
            
        current_x = parent_x + display_x
        current_y = parent_y + display_y
        
        # Проверяем тип узла
        if node.get('pythonObjectTypeName') == 'ActivateButton':
            # Ищем дочерний EveLabelMedium с нужным текстом
            children = node.get('children', [])
            if isinstance(children, list):
                for child in children:
                    if isinstance(child, dict):
                        if child.get('pythonObjectTypeName') == 'EveLabelMedium':
                            child_dict = child.get('dictEntriesOfInterest', {})
                            text = child_dict.get('_setText', '')
                            if 'Активировать для флота' in text or 'Activate for Fleet' in text:
                                # Возвращаем абсолютные координаты кнопки
                                w = dict_entries.get('_displayWidth', 0)
                                h = dict_entries.get('_displayHeight', 0)
                                if isinstance(w, dict):
                                    w = w.get('int_low32', 0)
                                if isinstance(h, dict):
                                    h = h.get('int_low32', 0)
                                if not isinstance(w, (int, float)):
                                    w = 0
                                if not isinstance(h, (int, float)):
                                    h = 0
                                return {
                                    '_displayX': current_x,
                                    '_displayY': current_y,
                                    '_displayWidth': w,
                                    '_displayHeight': h
                                }
        
        # Рекурсивный поиск в детях
        children = node.get('children')
        if isinstance(children, list):
            for child in children:
                result = self._find_activate_button(child, current_x, current_y)
                if result:
                    return result
        
        return None
