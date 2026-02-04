"""UI Tree parser for extracting game state from Sanderling."""
import time
from typing import List, Optional, Tuple, Dict, Any
from .models import GameState, Target, OverviewEntry, Module, ShipState, SelectedAction, OverviewTab, NeocomButton


class UITreeParser:
    """Парсер UI tree из Sanderling."""
    
    def __init__(self):
        """Инициализация парсера."""
        self._cache_hash = None
        self._cached_state = None
    
    def parse(self, ui_tree: dict) -> GameState:
        """
        Распарсить UI tree в структурированное состояние.
        
        Args:
            ui_tree: Словарь с UI tree от Sanderling
            
        Returns:
            GameState с извлеченными данными
        """
        if not ui_tree or not isinstance(ui_tree, dict):
            return GameState(
                timestamp=time.time(),
                is_valid=False,
                warnings=["Empty or invalid UI tree"]
            )
        
        # Кэширование парсинга
        tree_hash = hash(str(ui_tree))
        if tree_hash == self._cache_hash and self._cached_state:
            return self._cached_state
        
        warnings = []
        
        # Парсинг целей
        targets = self._parse_targets(ui_tree)
        if not targets:
            warnings.append("No targets found in UI tree")
        
        # Парсинг Overview
        overview = self._parse_overview(ui_tree)
        if not overview:
            warnings.append("No overview entries found in UI tree")
        
        # Парсинг модулей и состояния корабля
        modules = self._parse_modules(ui_tree)
        shield, armor, hull = self._parse_ship_health(ui_tree)
        capacitor = self._parse_capacitor(ui_tree)
        speed = self._parse_speed(ui_tree)
        
        ship_state = ShipState(
            modules=modules,
            shield=shield,
            armor=armor,
            hull=hull,
            capacitor=capacitor,
            speed=speed
        ) if modules or shield < 1.0 or armor < 1.0 or hull < 1.0 else None
        
        # Парсинг доступных действий
        selected_actions = self._parse_selected_actions(ui_tree)
        
        # Парсинг вкладок overview
        overview_tabs = self._parse_overview_tabs(ui_tree)
        
        # Парсинг кнопок Neocom (боковая панель)
        neocom_buttons = self._parse_neocom_buttons(ui_tree)
        
        # Парсинг инвентаря
        inventory = self._parse_inventory(ui_tree)
        
        # Парсинг контекстного меню
        context_menu = self._parse_context_menu(ui_tree)
        
        # Создание состояния
        state = GameState(
            targets=targets,
            overview=overview,
            ship=ship_state,
            selected_actions=selected_actions,
            overview_tabs=overview_tabs,
            neocom_buttons=neocom_buttons,
            inventory=inventory,
            context_menu=context_menu,
            timestamp=time.time(),
            is_valid=len(warnings) == 0,
            warnings=warnings
        )
        
        # Кэширование результата
        self._cache_hash = tree_hash
        self._cached_state = state
        
        return state
    
    def _parse_targets(self, node: dict) -> List[Target]:
        """
        Извлечь залоченные цели.
        
        Args:
            node: Узел UI tree
            
        Returns:
            Список целей
        """
        targets = []
        target_nodes = self._find_nodes_by_type(node, "TargetInBar")
        
        for idx, target_node in enumerate(target_nodes):
            try:
                # Извлечь координаты
                center = self._extract_coordinates(target_node)
                bounds = self._extract_bounds(target_node)
                
                # Валидация
                if not self._validate_coordinates(center):
                    continue
                
                # Извлечь данные цели
                name = self._extract_target_name(target_node)
                target_type = self._extract_target_type(target_node)
                distance_str = self._extract_target_distance(target_node)
                
                # Конвертировать дистанцию в float (метры)
                distance = self._parse_distance(distance_str) if distance_str else None
                
                # Проверить активность цели
                is_active = self._has_child_type(target_node, "ActiveTargetIndicator")
                
                # Извлечь здоровье цели
                shield, armor, hull = self._parse_target_health(target_node)
                
                target = Target(
                    name=name or f"Target_{idx+1}",
                    type=target_type or "unknown",
                    distance=distance,
                    is_active=is_active,
                    center=center,
                    bounds=bounds,
                    shield=shield,
                    armor=armor,
                    hull=hull
                )
                targets.append(target)
                
            except Exception as e:
                # Тихо пропускаем ошибки парсинга
                continue
        
        return targets
    
    def _parse_overview(self, node: dict) -> List[OverviewEntry]:
        """
        Извлечь записи Overview.
        
        Args:
            node: Узел UI tree
            
        Returns:
            Список записей Overview
        """
        entries = []
        overview_paths = self._find_nodes_with_path(node, "OverviewScrollEntry")
        
        for idx, path in enumerate(overview_paths):
            try:
                entry_node = path[-1]
                
                # Извлечь АБСОЛЮТНЫЕ координаты
                center = self._extract_absolute_coordinates(path)
                if not center:
                    continue
                
                # Добавить половину ширины/высоты для центра
                dict_entries = entry_node.get('dictEntriesOfInterest', {})
                width = dict_entries.get('_displayWidth', 100)
                height = dict_entries.get('_displayHeight', 24)
                
                if isinstance(width, dict) and 'int_low32' in width:
                    width = width['int_low32']
                if isinstance(height, dict) and 'int_low32' in height:
                    height = height['int_low32']
                
                center = (center[0] + int(width)//2, center[1] + int(height)//2)
                
                # Извлечь bounds
                bounds = self._extract_bounds(entry_node)
                
                # Валидация
                if not self._validate_coordinates(center):
                    continue
                
                # Извлечь данные из дочерних OverviewLabel
                name, distance, entry_type = self._extract_overview_data(entry_node)
                
                entry = OverviewEntry(
                    index=idx,
                    name=name,
                    type=entry_type,
                    distance=distance,
                    center=center,
                    bounds=bounds
                )
                entries.append(entry)
                
            except Exception as e:
                # Тихо пропускаем ошибки парсинга
                continue
        
        return entries
    
    def _parse_modules(self, node: dict) -> List[Module]:
        """
        Извлечь модули корабля.
        
        Args:
            node: Узел UI tree
            
        Returns:
            Список модулей
        """
        modules = []
        module_nodes = self._find_nodes_by_type(node, "ShipSlot")
        
        for idx, module_node in enumerate(module_nodes):
            try:
                # Извлечь имя слота из _name
                dict_entries = module_node.get('dictEntriesOfInterest', {})
                slot_name = dict_entries.get('_name', f'slot_{idx}')
                
                # Определить тип слота из имени
                slot_type = self._determine_slot_type_from_name(slot_name)
                
                # Проверить активность через ModuleButton
                is_active = self._is_module_active(module_node)
                
                # Извлечь координаты
                center = self._extract_coordinates(module_node)
                
                # Валидация
                if not self._validate_coordinates(center):
                    continue
                
                module = Module(
                    slot_type=slot_type,
                    slot_name=slot_name,
                    is_active=is_active,
                    center=center
                )
                modules.append(module)
                
            except Exception as e:
                # Тихо пропускаем ошибки парсинга
                continue
        
        return modules
    
    def _find_nodes_by_type(self, node: Any, type_name: str) -> List[dict]:
        """
        Найти все узлы определенного типа.
        
        Args:
            node: Узел для поиска
            type_name: Имя типа узла
            
        Returns:
            Список найденных узлов
        """
        results = []
        
        if not isinstance(node, dict):
            return results
        
        # Проверить текущий узел
        if node.get('pythonObjectTypeName') == type_name:
            results.append(node)
        
        # Рекурсивный поиск в children
        children = node.get('children', [])
        if isinstance(children, list):
            for child in children:
                results.extend(self._find_nodes_by_type(child, type_name))
        
        return results
    
    def _find_nodes_with_path(self, node: Any, type_name: str, path: Optional[List[dict]] = None) -> List[List[dict]]:
        """
        Найти все узлы определенного типа с путем от корня.
        
        Args:
            node: Узел для поиска
            type_name: Имя типа узла
            path: Текущий путь (для рекурсии)
            
        Returns:
            Список путей к найденным узлам
        """
        if path is None:
            path = []
        
        results = []
        
        if not isinstance(node, dict):
            return results
        
        current_path = path + [node]
        
        # Проверить текущий узел
        if node.get('pythonObjectTypeName') == type_name:
            results.append(current_path)
        
        # Рекурсивный поиск в children
        children = node.get('children', [])
        if isinstance(children, list):
            for child in children:
                results.extend(self._find_nodes_with_path(child, type_name, current_path))
        
        return results
    
    def _extract_coordinates(self, node: dict) -> Optional[Tuple[int, int]]:
        """
        Извлечь АБСОЛЮТНЫЕ координаты элемента (с учетом всех родителей).
        
        Args:
            node: Узел UI tree
            
        Returns:
            Кортеж (x, y) или None
        """
        try:
            dict_entries = node.get('dictEntriesOfInterest', {})
            x = dict_entries.get('_displayX')
            y = dict_entries.get('_displayY')
            
            # Обработать int_low32
            if isinstance(x, dict) and 'int_low32' in x:
                x = x['int_low32']
            if isinstance(y, dict) and 'int_low32' in y:
                y = y['int_low32']
            
            if x is not None and y is not None:
                return (int(x), int(y))
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _extract_absolute_coordinates(self, node_path: List[dict]) -> Optional[Tuple[int, int]]:
        """
        Извлечь абсолютные координаты узла с учетом всех родителей.
        
        Args:
            node_path: Путь от корня до узла
            
        Returns:
            Кортеж (x, y) абсолютных координат
        """
        x = 0
        y = 0
        
        for node in node_path:
            dict_entries = node.get('dictEntriesOfInterest', {})
            
            node_x = dict_entries.get('_displayX', 0)
            node_y = dict_entries.get('_displayY', 0)
            
            if isinstance(node_x, dict) and 'int_low32' in node_x:
                node_x = node_x['int_low32']
            if isinstance(node_y, dict) and 'int_low32' in node_y:
                node_y = node_y['int_low32']
            
            x += int(node_x) if node_x else 0
            y += int(node_y) if node_y else 0
        
        return (x, y)
    
    def _extract_bounds(self, node: dict) -> Optional[Tuple[int, int, int, int]]:
        """
        Извлечь границы элемента.
        
        Args:
            node: Узел UI tree
            
        Returns:
            Кортеж (x, y, width, height) или None
        """
        try:
            dict_entries = node.get('dictEntriesOfInterest', {})
            x = dict_entries.get('_displayX')
            y = dict_entries.get('_displayY')
            width = dict_entries.get('_displayWidth')
            height = dict_entries.get('_displayHeight')
            
            # Обработать int_low32
            if isinstance(x, dict) and 'int_low32' in x:
                x = x['int_low32']
            if isinstance(y, dict) and 'int_low32' in y:
                y = y['int_low32']
            if isinstance(width, dict) and 'int_low32' in width:
                width = width['int_low32']
            if isinstance(height, dict) and 'int_low32' in height:
                height = height['int_low32']
            
            if all(v is not None for v in [x, y, width, height]):
                return (int(x), int(y), int(width), int(height))
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _extract_text(self, node: dict, field_name: str) -> Optional[str]:
        """
        Извлечь текст из поля узла.
        
        Args:
            node: Узел UI tree
            field_name: Имя поля
            
        Returns:
            Текст или None
        """
        dict_entries = node.get('dictEntriesOfInterest', {})
        if isinstance(dict_entries, dict):
            value = dict_entries.get(field_name)
            if value and isinstance(value, str):
                return value.strip()
        
        return None
    
    def _has_child_type(self, node: dict, type_name: str) -> bool:
        """
        Проверить наличие дочернего узла определенного типа.
        
        Args:
            node: Узел UI tree
            type_name: Имя типа
            
        Returns:
            True если найден
        """
        children = node.get('children', [])
        if isinstance(children, list):
            for child in children:
                if isinstance(child, dict) and child.get('pythonObjectTypeName') == type_name:
                    return True
        return False
    
    def _determine_slot_type(self, node: dict) -> str:
        """
        Определить тип слота модуля.
        
        Args:
            node: Узел модуля
            
        Returns:
            'high', 'mid' или 'low'
        """
        # Простая эвристика на основе позиции
        y = node.get('_displayY', 0)
        if y < 400:
            return 'high'
        elif y < 600:
            return 'mid'
        else:
            return 'low'
    
    def _determine_slot_type_from_name(self, slot_name: str) -> str:
        """
        Определить тип слота из имени.
        
        Args:
            slot_name: Имя слота (например, 'inFlightHighSlot1')
            
        Returns:
            'high', 'mid' или 'low'
        """
        name_lower = slot_name.lower()
        if 'high' in name_lower:
            return 'high'
        elif 'med' in name_lower or 'mid' in name_lower:
            return 'mid'
        elif 'low' in name_lower:
            return 'low'
        else:
            return 'unknown'
    
    def _is_module_active(self, node: dict) -> bool:
        """
        Проверить активность модуля.
        
        Args:
            node: Узел модуля
            
        Returns:
            True если модуль активен
        """
        # Найти дочерний ModuleButton и проверить ramp_active
        children = node.get('children', [])
        if isinstance(children, list):
            for child in children:
                if isinstance(child, dict) and child.get('pythonObjectTypeName') == 'ModuleButton':
                    dict_entries = child.get('dictEntriesOfInterest', {})
                    return dict_entries.get('ramp_active', False)
        
        return False
    
    def _extract_target_name(self, target_node: dict) -> Optional[str]:
        """
        Извлечь имя цели из дочерних элементов.
        
        Args:
            target_node: Узел TargetInBar
            
        Returns:
            Имя цели или None
        """
        # Найти labelContainer -> EveLabelSmall с _setText
        children = target_node.get('children', [])
        if not isinstance(children, list):
            return None
        
        for child in children:
            if not isinstance(child, dict):
                continue
            
            # Ищем labelContainer
            dict_entries = child.get('dictEntriesOfInterest', {})
            if dict_entries.get('_name') == 'labelContainer':
                # Внутри labelContainer ищем EveLabelSmall
                label_children = child.get('children', [])
                if isinstance(label_children, list) and len(label_children) >= 2:
                    # Вторая строка - это имя цели
                    second_label = label_children[1]
                    if isinstance(second_label, dict):
                        label_dict = second_label.get('dictEntriesOfInterest', {})
                        text = label_dict.get('_setText', '')
                        # Убрать <center> теги
                        if text:
                            text = text.replace('<center>', '').replace('</center>', '').strip()
                            return text
        
        return None
    
    def _extract_target_distance(self, target_node: dict) -> Optional[str]:
        """
        Извлечь дистанцию до цели.
        
        Args:
            target_node: Узел TargetInBar
            
        Returns:
            Дистанция или None
        """
        children = target_node.get('children', [])
        if not isinstance(children, list):
            return None
        
        for child in children:
            if not isinstance(child, dict):
                continue
            
            dict_entries = child.get('dictEntriesOfInterest', {})
            if dict_entries.get('_name') == 'labelContainer':
                label_children = child.get('children', [])
                if isinstance(label_children, list) and len(label_children) >= 3:
                    # Третья строка - это дистанция
                    third_label = label_children[2]
                    if isinstance(third_label, dict):
                        label_dict = third_label.get('dictEntriesOfInterest', {})
                        text = label_dict.get('_setText', '')
                        if text:
                            text = text.replace('<center>', '').replace('</center>', '').strip()
                            return text
        
        return None
    
    def _extract_target_type(self, target_node: dict) -> Optional[str]:
        """
        Извлечь тип цели (фракцию).
        
        Args:
            target_node: Узел TargetInBar
            
        Returns:
            Тип цели или None
        """
        children = target_node.get('children', [])
        if not isinstance(children, list):
            return None
        
        for child in children:
            if not isinstance(child, dict):
                continue
            
            dict_entries = child.get('dictEntriesOfInterest', {})
            if dict_entries.get('_name') == 'labelContainer':
                label_children = child.get('children', [])
                if isinstance(label_children, list) and len(label_children) >= 1:
                    # Первая строка - это тип/фракция
                    first_label = label_children[0]
                    if isinstance(first_label, dict):
                        label_dict = first_label.get('dictEntriesOfInterest', {})
                        text = label_dict.get('_setText', '')
                        if text:
                            text = text.replace('<center>', '').replace('</center>', '').strip()
                            return text
        
        return None
    
    def _extract_overview_data(self, entry_node: dict) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Извлечь данные из OverviewScrollEntry.
        
        Args:
            entry_node: Узел OverviewScrollEntry
            
        Returns:
            Кортеж (name, distance, type)
        """
        name = None
        distance = None
        entry_type = None
        
        # Найти дочерние OverviewLabel
        children = entry_node.get('children', [])
        if not isinstance(children, list):
            return (name, distance, entry_type)
        
        labels = []
        for child in children:
            if isinstance(child, dict) and child.get('pythonObjectTypeName') == 'OverviewLabel':
                dict_entries = child.get('dictEntriesOfInterest', {})
                text = dict_entries.get('_text', '')
                hint = dict_entries.get('_hint', '')
                x = dict_entries.get('_displayX', 0)
                if isinstance(x, dict) and 'int_low32' in x:
                    x = x['int_low32']
                labels.append({'text': text, 'hint': hint, 'x': x})
        
        # Сортируем по X координате (слева направо)
        labels.sort(key=lambda l: l['x'])
        
        # Структура overview (слева направо по X):
        # 1. Icon (SpaceObjectIcon) - x ~3
        # 2. Distance - x ~34 (содержит км/м)
        # 3. Name - x ~131 (длинный текст)
        # 4. Type - x ~243 (содержит *)
        # 5-6. Другие колонки - x ~389, ~447
        
        for label in labels:
            text = label['text']
            hint = label['hint']
            x = label['x']
            
            # Пропускаем пустые и "-"
            if not text or text == '-':
                continue
            
            # Дистанция: x < 100 и содержит "км" или "м"
            if x < 100 and ('км' in text or ' м' in text or 'km' in text.lower() or ' m' in text.lower()):
                distance = text
            # Тип: x > 200 и содержит "*"
            elif x > 200 and '*' in text:
                entry_type = hint if hint else text.replace('*', '').strip()
            # Имя: x между 100 и 200, самый длинный текст
            elif 100 <= x < 200 and len(text) > 10:
                name = hint if hint else text
        
        return (name, distance, entry_type)
    
    def _parse_distance(self, distance_str: str) -> Optional[float]:
        """
        Конвертировать строку дистанции в метры.
        
        Args:
            distance_str: Строка вида "1 189 м" или "188 570 км"
            
        Returns:
            Дистанция в метрах или None
        """
        if not distance_str:
            return None
        
        try:
            # Сохранить единицы измерения
            is_km = 'км' in distance_str or 'km' in distance_str.lower()
            is_m = ' м' in distance_str or ' m' in distance_str.lower()
            
            # Убрать все кроме цифр, точек и запятых
            num_str = ''
            for char in distance_str:
                if char.isdigit() or char in '.,':
                    num_str += char
            
            if not num_str:
                return None
            
            # Заменить запятые на точки
            num_str = num_str.replace(',', '.')
            
            # Конвертировать
            value = float(num_str)
            
            if is_km:
                return value * 1000
            elif is_m:
                return value
            else:
                # По умолчанию метры
                return value
        except (ValueError, AttributeError):
            return None
    
    def _validate_coordinates(self, coords: Optional[Tuple[int, int]]) -> bool:
        """
        Валидировать координаты.
        
        Args:
            coords: Координаты для проверки
            
        Returns:
            True если координаты валидны
        """
        if coords is None:
            return False
        
        x, y = coords
        
        # Проверить что координаты в разумных пределах (экран 1920x1080)
        if x < 0 or x > 3840 or y < 0 or y > 2160:
            return False
        
        return True

    
    def _parse_ship_health(self, node: dict) -> Tuple[float, float, float]:
        """
        Извлечь здоровье корабля (щиты, броня, структура).
        
        Args:
            node: Корневой узел UI tree
            
        Returns:
            Кортеж (shield, armor, hull) в диапазоне 0.0-1.0
        """
        gauges = self._find_nodes_by_type(node, 'ShipHudSpriteGauge')
        
        shield = 1.0
        armor = 1.0
        hull = 1.0
        
        for gauge in gauges:
            dict_entries = gauge.get('dictEntriesOfInterest', {})
            name = dict_entries.get('_name', '')
            value = dict_entries.get('_lastValue', 1.0)
            
            try:
                value = float(value)
            except (ValueError, TypeError):
                value = 1.0
            
            if name == 'shieldGauge':
                shield = value
            elif name == 'armorGauge':
                armor = value
            elif name == 'structureGauge':
                hull = value
        
        return (shield, armor, hull)
    
    def _parse_capacitor(self, node: dict) -> float:
        """
        Извлечь уровень энергии корабля.
        
        Args:
            node: Корневой узел UI tree
            
        Returns:
            Уровень энергии 0.0-1.0
        """
        # Ищем CapacitorContainer
        containers = self._find_nodes_by_type(node, 'CapacitorContainer')
        if not containers:
            return 1.0
        
        # Внутри CapacitorContainer есть Transform узлы с именем 'powerColumn'
        # Каждый powerColumn содержит 4 Sprite с именем 'pmark'
        # Видимые pmark (_display: True) показывают уровень энергии
        
        power_columns = self._find_nodes_by_type(containers[0], 'Transform')
        
        total_cells = 0
        visible_cells = 0
        
        for column in power_columns:
            dict_entries = column.get('dictEntriesOfInterest', {})
            if dict_entries.get('_name') != 'powerColumn':
                continue
            
            # Найти все pmark внутри этой колонки
            sprites = self._find_nodes_by_type(column, 'Sprite')
            for sprite in sprites:
                sprite_dict = sprite.get('dictEntriesOfInterest', {})
                if sprite_dict.get('_name') == 'pmark':
                    total_cells += 1
                    # Проверить видимость
                    display = sprite_dict.get('_display', True)
                    if display:
                        visible_cells += 1
        
        if total_cells == 0:
            return 1.0
        
        return visible_cells / total_cells
    
    def _parse_speed(self, node: dict) -> float:
        """
        Извлечь скорость корабля.
        
        Args:
            node: Корневой узел UI tree
            
        Returns:
            Скорость в м/с
        """
        # Ищем SpeedGauge
        gauges = self._find_nodes_by_type(node, 'SpeedGauge')
        if not gauges:
            return 0.0
        
        # Внутри SpeedGauge есть EveLabelSmall с _setText содержащим скорость
        labels = self._find_nodes_by_type(gauges[0], 'EveLabelSmall')
        
        for label in labels:
            dict_entries = label.get('dictEntriesOfInterest', {})
            text = dict_entries.get('_setText', '') or dict_entries.get('_text', '')
            
            if text and ('м/с' in text or 'm/s' in text.lower()):
                # Текст вида "311 м/с" или "1 234 м/с"
                try:
                    # Убрать все кроме цифр и пробелов
                    num_str = ''
                    for char in text:
                        if char.isdigit() or char == ' ':
                            num_str += char
                    
                    if num_str:
                        # Убрать пробелы и конвертировать
                        num_str = num_str.replace(' ', '')
                        return float(num_str)
                except (ValueError, AttributeError):
                    pass
        
        return 0.0
    
    def _parse_target_health(self, target_node: dict) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Извлечь здоровье цели.
        
        Args:
            target_node: Узел TargetInBar
            
        Returns:
            Кортеж (shield, armor, hull) в диапазоне 0.0-1.0 или None
        """
        # Найти TargetHealthBars внутри TargetInBar
        health_bars = self._find_nodes_by_type(target_node, 'TargetHealthBars')
        if not health_bars:
            return (None, None, None)
        
        health_bar = health_bars[0]
        
        shield = None
        armor = None
        hull = None
        
        # Найти контейнеры с полосками здоровья
        children = health_bar.get('children', [])
        if not isinstance(children, list):
            return (None, None, None)
        
        for container in children:
            if not isinstance(container, dict):
                continue
            
            dict_entries = container.get('dictEntriesOfInterest', {})
            name = dict_entries.get('_name', '')
            
            if name not in ['shieldBar', 'armorBar', 'hullBar']:
                continue
            
            # Внутри контейнера найти Sprite с _Right (это полоска здоровья)
            container_children = container.get('children', [])
            if not isinstance(container_children, list):
                continue
            
            for sprite in container_children:
                if not isinstance(sprite, dict):
                    continue
                
                sprite_dict = sprite.get('dictEntriesOfInterest', {})
                sprite_name = sprite_dict.get('_name', '')
                
                if '_Right' not in sprite_name:
                    continue
                
                # Получить ширину полоски
                width = sprite_dict.get('_displayWidth', 0)
                if isinstance(width, dict) and 'int_low32' in width:
                    width = width['int_low32']
                
                try:
                    width = int(width)
                    # Максимальная ширина 94px
                    percent = min(width / 94.0, 1.0)
                    
                    if name == 'shieldBar':
                        shield = percent
                    elif name == 'armorBar':
                        armor = percent
                    elif name == 'hullBar':
                        hull = percent
                except (ValueError, TypeError):
                    pass
        
        return (shield, armor, hull)
    
    def _parse_selected_actions(self, node: dict) -> List[SelectedAction]:
        """
        Извлечь доступные действия с выбранным объектом.
        
        Args:
            node: Корневой узел UI tree
            
        Returns:
            Список доступных действий с АБСОЛЮТНЫМИ координатами кнопок
        """
        actions = []
        button_paths = self._find_nodes_with_path(node, 'SelectedItemButton')
        
        for path in button_paths:
            button = path[-1]
            dict_entries = button.get('dictEntriesOfInterest', {})
            name = dict_entries.get('_name', '')
            texture = dict_entries.get('texturePath', '')
            
            # Извлечь АБСОЛЮТНЫЕ координаты центра кнопки
            center = self._extract_absolute_coordinates(path)
            if not center:
                continue
            
            # Добавить половину ширины/высоты для центра кнопки
            width = dict_entries.get('_displayWidth', 32)
            height = dict_entries.get('_displayHeight', 32)
            if isinstance(width, dict) and 'int_low32' in width:
                width = width['int_low32']
            if isinstance(height, dict) and 'int_low32' in height:
                height = height['int_low32']
            
            center = (center[0] + int(width)//2, center[1] + int(height)//2)
            
            # Извлечь имя действия из _name
            # Например: "selectedItemApproach" -> "approach"
            action_name = name.replace('selectedItem', '').replace('SelectedItem', '')
            if not action_name:
                continue
            
            # Преобразовать в snake_case
            action_name = self._camel_to_snake(action_name)
            
            action = SelectedAction(
                name=action_name,
                center=center,
                texture_path=texture if texture else None
            )
            actions.append(action)
        
        return actions
    
    def _parse_overview_tabs(self, node: dict) -> List[OverviewTab]:
        """
        Извлечь вкладки overview.
        
        Args:
            node: Корневой узел UI tree
            
        Returns:
            Список вкладок с АБСОЛЮТНЫМИ координатами для клика
        """
        tabs = []
        tab_paths = self._find_nodes_with_path(node, 'OverviewTab')
        
        for path in tab_paths:
            tab_node = path[-1]
            dict_entries = tab_node.get('dictEntriesOfInterest', {})
            name = dict_entries.get('_name', '')
            
            # Извлечь АБСОЛЮТНЫЕ координаты центра вкладки
            center = self._extract_absolute_coordinates(path)
            if not center:
                continue
            
            # Добавить половину ширины/высоты для центра вкладки
            width = dict_entries.get('_displayWidth', 40)
            height = dict_entries.get('_displayHeight', 24)
            if isinstance(width, dict) and 'int_low32' in width:
                width = width['int_low32']
            if isinstance(height, dict) and 'int_low32' in height:
                height = height['int_low32']
            
            center = (center[0] + int(width)//2, center[1] + int(height)//2)
            
            # Извлечь текст вкладки из _name
            # Например: "OverviewTab_<color=yellow>✈ Jump</color>" -> "✈ Jump"
            label = name.replace('OverviewTab_', '')
            
            # Убрать HTML теги
            import re
            label = re.sub(r'<[^>]+>', '', label)
            
            tab = OverviewTab(
                name=name,
                label=label,
                center=center
            )
            tabs.append(tab)
        
        return tabs
    
    def _camel_to_snake(self, name: str) -> str:
        """
        Преобразовать camelCase в snake_case.
        
        Args:
            name: Имя в camelCase
            
        Returns:
            Имя в snake_case
        """
        import re
        # Вставить _ перед заглавными буквами
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
        return name.lower()

    
    def _parse_neocom_buttons(self, node: dict) -> List[NeocomButton]:
        """
        Извлечь кнопки Neocom (боковая панель).
        
        Args:
            node: Корневой узел UI tree
            
        Returns:
            Список кнопок с АБСОЛЮТНЫМИ координатами для клика
        """
        buttons = []
        
        # Маппинг типов кнопок
        button_mapping = {
            'LeftSideButtonCargo': 'cargo',
            'ButtonInventory': 'inventory',
            'LeftSideButtonTactical': 'tactical',
            'LeftSideButtonScanner': 'scanner',
            'LeftSideButtonAutopilot': 'autopilot',
            'LeftSideButtonCameraTactical': 'camera_tactical',
            'LeftSideButtonCameraOrbit': 'camera_orbit',
            'LeftSideButtonCameraPOV': 'camera_pov',
        }
        
        # Найти все кнопки
        for type_name, button_type in button_mapping.items():
            button_paths = self._find_nodes_with_path(node, type_name)
            
            for path in button_paths:
                button_node = path[-1]
                
                # Извлечь АБСОЛЮТНЫЕ координаты центра кнопки
                center = self._extract_absolute_coordinates(path)
                if not center:
                    continue
                
                # Добавить половину ширины/высоты для центра кнопки
                dict_entries = button_node.get('dictEntriesOfInterest', {})
                width = dict_entries.get('_displayWidth', 36)
                height = dict_entries.get('_displayHeight', 36)
                
                if isinstance(width, dict) and 'int_low32' in width:
                    width = width['int_low32']
                if isinstance(height, dict) and 'int_low32' in height:
                    height = height['int_low32']
                
                center = (center[0] + int(width)//2, center[1] + int(height)//2)
                
                button = NeocomButton(
                    button_type=button_type,
                    center=center
                )
                buttons.append(button)
        
        return buttons

    
    def _parse_inventory(self, node: dict) -> Optional['InventoryWindow']:
        """
        Извлечь данные инвентаря.
        
        Args:
            node: Корневой узел UI tree
            
        Returns:
            InventoryWindow или None если инвентарь закрыт
        """
        from .models import InventoryWindow, InventoryFilter, InventoryItem
        
        # Найти InventoryPrimary
        inventory_paths = self._find_nodes_with_path(node, 'InventoryPrimary')
        if not inventory_paths:
            return None
        
        inv_path = inventory_paths[0]
        inv_node = inv_path[-1]
        inv_dict = inv_node.get('dictEntriesOfInterest', {})
        
        # Извлечь АБСОЛЮТНЫЕ координаты окна
        inv_center = self._extract_absolute_coordinates(inv_path)
        if not inv_center:
            return None
        
        # Извлечь размеры
        width = inv_dict.get('_displayWidth', 0)
        height = inv_dict.get('_displayHeight', 0)
        if isinstance(width, dict) and 'int_low32' in width:
            width = width['int_low32']
        if isinstance(height, dict) and 'int_low32' in height:
            height = height['int_low32']
        
        inv_x = inv_center[0]
        inv_y = inv_center[1]
        inv_bounds = (inv_x, inv_y, int(width), int(height))
        inv_center = (inv_x + int(width)//2, inv_y + int(height)//2)
        
        # Парсим фильтры
        filters = self._parse_inventory_filters(node, inv_x, inv_y)
        
        # Парсим предметы
        items = self._parse_inventory_items(node, inv_x, inv_y)
        
        # Парсим кнопку "Взять все"
        loot_all_button = self._parse_loot_all_button(node, inv_x, inv_y)
        
        return InventoryWindow(
            is_open=True,
            center=inv_center,
            bounds=inv_bounds,
            filters=filters,
            items=items,
            loot_all_button=loot_all_button
        )
    
    def _parse_inventory_filters(self, node: dict, inv_x: int, inv_y: int) -> List['InventoryFilter']:
        """
        Извлечь фильтры инвентаря.
        
        Args:
            node: Корневой узел UI tree
            inv_x: X координата окна инвентаря (для вычисления абсолютных координат)
            inv_y: Y координата окна инвентаря
            
        Returns:
            Список фильтров с АБСОЛЮТНЫМИ координатами
        """
        from .models import InventoryFilter
        
        filters = []
        filter_paths = self._find_nodes_with_path(node, 'FilterEntry')
        
        for path in filter_paths:
            filter_node = path[-1]
            filter_dict = filter_node.get('dictEntriesOfInterest', {})
            
            # Извлечь АБСОЛЮТНЫЕ координаты фильтра
            filter_center = self._extract_absolute_coordinates(path)
            if not filter_center:
                continue
            
            # Извлечь размеры
            width = filter_dict.get('_displayWidth', 120)
            height = filter_dict.get('_displayHeight', 22)
            if isinstance(width, dict) and 'int_low32' in width:
                width = width['int_low32']
            if isinstance(height, dict) and 'int_low32' in height:
                height = height['int_low32']
            
            filter_x = filter_center[0]
            filter_y = filter_center[1]
            filter_bounds = (filter_x, filter_y, int(width), int(height))
            filter_center = (filter_x + int(width)//2, filter_y + int(height)//2)
            
            # Извлечь текст фильтра рекурсивно
            filter_text = self._find_filter_text(filter_node)
            if not filter_text:
                continue
            
            # Проверить активность фильтра (есть ли Checkbox с checked=True)
            is_active = self._is_filter_active(filter_node)
            
            filter_obj = InventoryFilter(
                name=filter_text,
                center=filter_center,
                bounds=filter_bounds,
                is_active=is_active
            )
            filters.append(filter_obj)
        
        return filters
    
    def _parse_loot_all_button(self, node: dict, inv_x: int, inv_y: int) -> Optional[Tuple[int, int]]:
        """
        Найти кнопку "Взять все" (invLootAllBtn).
        
        Args:
            node: Корневой узел UI tree
            inv_x: X координата окна инвентаря
            inv_y: Y координата окна инвентаря
            
        Returns:
            Абсолютные координаты кнопки или None
        """
        # Ищем кнопку по имени "invLootAllBtn" через рекурсивный поиск
        def find_button(n: dict) -> Optional[dict]:
            """Рекурсивный поиск кнопки по имени."""
            if not isinstance(n, dict):
                return None
            
            # Проверяем текущий узел
            dict_entries = n.get('dictEntriesOfInterest', {})
            if dict_entries.get('_name') == 'invLootAllBtn':
                return n
            
            # Ищем в children
            children = n.get('children', [])
            if isinstance(children, list):
                for child in children:
                    result = find_button(child)
                    if result:
                        return result
            
            return None
        
        button_node = find_button(node)
        if not button_node:
            return None
        
        # Нужно найти путь к кнопке для вычисления абсолютных координат
        # Ищем Button с именем invLootAllBtn
        button_paths = []
        
        def find_paths(n: dict, path: List[dict] = None):
            if path is None:
                path = []
            
            if not isinstance(n, dict):
                return
            
            current_path = path + [n]
            
            # Проверяем текущий узел
            if n.get('pythonObjectTypeName') == 'Button':
                dict_entries = n.get('dictEntriesOfInterest', {})
                if dict_entries.get('_name') == 'invLootAllBtn':
                    button_paths.append(current_path)
            
            # Рекурсия в children
            children = n.get('children', [])
            if isinstance(children, list):
                for child in children:
                    find_paths(child, current_path)
        
        find_paths(node)
        
        if not button_paths:
            return None
        
        # Берем первый найденный путь
        button_path = button_paths[0]
        button_coords = self._extract_absolute_coordinates(button_path)
        
        if not button_coords:
            return None
        
        # Получаем размеры кнопки для вычисления центра
        button_dict = button_path[-1].get('dictEntriesOfInterest', {})
        
        width = button_dict.get('_displayWidth', 80)
        height = button_dict.get('_displayHeight', 24)
        
        if isinstance(width, dict) and 'int_low32' in width:
            width = width['int_low32']
        if isinstance(height, dict) and 'int_low32' in height:
            height = height['int_low32']
        
        # Вычисляем центр кнопки
        button_center = (
            button_coords[0] + int(width) // 2,
            button_coords[1] + int(height) // 2
        )
        
        return button_center
    
    def _parse_inventory_items(self, node: dict, inv_x: int, inv_y: int) -> List['InventoryItem']:
        """
        Извлечь предметы из инвентаря.
        
        Args:
            node: Корневой узел UI tree
            inv_x: X координата окна инвентаря
            inv_y: Y координата окна инвентаря
            
        Returns:
            Список предметов с АБСОЛЮТНЫМИ координатами
        """
        from .models import InventoryItem
        
        items = []
        
        # Собираем все узлы для поиска
        all_nodes = []
        def collect_nodes_with_path(n, path=None):
            if path is None:
                path = []
            if not isinstance(n, dict):
                return
            
            current_path = path + [n]
            all_nodes.append((n, current_path))
            
            # Рекурсия в children (массив)
            children = n.get('children', [])
            if isinstance(children, list):
                for child in children:
                    collect_nodes_with_path(child, current_path)
        
        collect_nodes_with_path(node)
        
        # Ищем предметы по текстуре и тексту
        for node_data, path in all_nodes:
            dict_entries = node_data.get('dictEntriesOfInterest', {})
            if not dict_entries:
                continue
            
            # Проверяем текстуру (иконка предмета)
            texture = dict_entries.get('_texturePath', '')
            
            # Проверяем текст (название предмета)
            text = dict_entries.get('_setText', '')
            hint = dict_entries.get('_hint', '')
            
            # Если есть текст с названием предмета
            if text and isinstance(text, str) and ('Filament' in text or 'filament' in text.lower()):
                # Извлечь АБСОЛЮТНЫЕ координаты
                item_center = self._extract_absolute_coordinates(path)
                if not item_center:
                    continue
                
                # Извлечь размеры
                width = dict_entries.get('_displayWidth', 64)
                height = dict_entries.get('_displayHeight', 64)
                if isinstance(width, dict) and 'int_low32' in width:
                    width = width['int_low32']
                if isinstance(height, dict) and 'int_low32' in height:
                    height = height['int_low32']
                
                item_x = item_center[0]
                item_y = item_center[1]
                item_bounds = (item_x, item_y, int(width), int(height))
                item_center = (item_x + int(width)//2, item_y + int(height)//2)
                
                # Очистить текст от HTML тегов
                import re
                clean_text = re.sub(r'<[^>]+>', '', text)
                clean_hint = re.sub(r'<[^>]+>', '', hint) if hint else None
                
                item = InventoryItem(
                    name=clean_text,
                    hint=clean_hint,
                    center=item_center,
                    bounds=item_bounds,
                    texture_path=texture if texture else None
                )
                items.append(item)
        
        return items
    
    def _find_filter_text(self, node: dict) -> Optional[str]:
        """
        Рекурсивно ищет текст фильтра в узле.
        
        Args:
            node: Узел FilterEntry
            
        Returns:
            Текст фильтра или None
        """
        if not isinstance(node, dict):
            return None
        
        # Проверяем _setText в dictEntriesOfInterest
        dict_entries = node.get('dictEntriesOfInterest', {})
        text = dict_entries.get('_setText')
        if text:
            return text
        
        # Ищем в children (массив)
        children = node.get('children')
        if isinstance(children, list):
            for child in children:
                result = self._find_filter_text(child)
                if result:
                    return result
        
        return None
    
    def _is_filter_active(self, node: dict) -> bool:
        """
        Проверяет активность фильтра.
        
        Args:
            node: Узел FilterEntry
            
        Returns:
            True если фильтр активен
        """
        if not isinstance(node, dict):
            return False
        
        # Ищем Checkbox с checked=True
        dict_entries = node.get('dictEntriesOfInterest', {})
        if dict_entries.get('pythonObjectTypeName') == 'Checkbox':
            return dict_entries.get('checked', False)
        
        # Рекурсия в children
        children = node.get('children', [])
        if isinstance(children, list):
            for child in children:
                if self._is_filter_active(child):
                    return True
        
        return False
    
    def _parse_context_menu(self, node: dict) -> Optional['ContextMenu']:
        """
        Извлечь контекстное меню.
        
        Args:
            node: Корневой узел UI tree
            
        Returns:
            ContextMenu или None если меню закрыто
        """
        from .models import ContextMenu, ContextMenuItem
        
        # Найти ContextMenu (не Menu!)
        menu_paths = self._find_nodes_with_path(node, 'ContextMenu')
        if not menu_paths:
            return None
        
        menu_items = []
        
        # Найти все MenuEntryView (не MenuEntry!)
        entry_paths = self._find_nodes_with_path(node, 'MenuEntryView')
        
        for path in entry_paths:
            entry_node = path[-1]
            entry_dict = entry_node.get('dictEntriesOfInterest', {})
            
            # Извлечь текст пункта меню из _setText
            text = entry_dict.get('_setText', '') or entry_dict.get('_text', '')
            if not text:
                # Попробовать найти в children
                children = entry_node.get('children', [])
                if isinstance(children, list):
                    for child in children:
                        if isinstance(child, dict):
                            child_dict = child.get('dictEntriesOfInterest', {})
                            text = child_dict.get('_setText', '')
                            if text:
                                break
            
            if not text:
                continue
            
            # Очистить от HTML тегов
            import re
            text = re.sub(r'<[^>]+>', '', text)
            
            # Извлечь АБСОЛЮТНЫЕ координаты
            center = self._extract_absolute_coordinates(path)
            if not center:
                continue
            
            # Извлечь размеры
            width = entry_dict.get('_displayWidth', 100)
            height = entry_dict.get('_displayHeight', 20)
            if isinstance(width, dict) and 'int_low32' in width:
                width = width['int_low32']
            if isinstance(height, dict) and 'int_low32' in height:
                height = height['int_low32']
            
            entry_x = center[0]
            entry_y = center[1]
            entry_bounds = (entry_x, entry_y, int(width), int(height))
            entry_center = (entry_x + int(width)//2, entry_y + int(height)//2)
            
            menu_item = ContextMenuItem(
                text=text,
                center=entry_center,
                bounds=entry_bounds
            )
            menu_items.append(menu_item)
        
        if not menu_items:
            return None
        
        return ContextMenu(
            is_open=True,
            items=menu_items
        )
