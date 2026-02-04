# eve/sanderling/parser.py
"""
Парсер UI tree из памяти EVE Online.

Преобразует сырой JSON от read-memory-64-bit в удобные структуры данных.
"""

import re
from typing import Dict, Any, List, Optional
from .models import Target, OverviewEntry, Module, ShipState, GameState


class UITreeParser:
    """Парсер UI tree."""

    def __init__(self, raw_data: Dict[str, Any]):
        self.raw = raw_data
        self._all_nodes_cache = None

    def parse(self) -> GameState:
        """Распарсить всё дерево в GameState."""
        state = GameState()
        state.targets = self.parse_targets()
        state.overview = self.parse_overview()
        state.ship = self.parse_ship()
        state.node_count = len(self._get_all_nodes())
        return state

    def _get_all_nodes(self) -> List[Dict]:
        """Получить все узлы дерева (с кэшированием)."""
        if self._all_nodes_cache is None:
            self._all_nodes_cache = []
            self._collect_nodes(self.raw, self._all_nodes_cache)
        return self._all_nodes_cache

    def _collect_nodes(self, node: Dict, results: List):
        """Рекурсивно собрать все узлы."""
        if not node:
            return
        results.append(node)
        for child in (node.get('children') or []):
            if child:
                self._collect_nodes(child, results)

    def _find_nodes_by_type(self, type_name: str) -> List[Dict]:
        """Найти все узлы заданного типа."""
        return [
            n for n in self._get_all_nodes()
            if n.get('pythonObjectTypeName') == type_name
        ]

    def _find_nodes_by_name(self, name: str) -> List[Dict]:
        """Найти узлы по имени."""
        return [
            n for n in self._get_all_nodes()
            if n.get('dictEntriesOfInterest', {}).get('_name') == name
        ]

    def _get_props(self, node: Dict) -> Dict:
        """Получить свойства узла."""
        return node.get('dictEntriesOfInterest', {})

    def _get_text(self, node: Dict) -> str:
        """Получить текст из узла."""
        props = self._get_props(node)
        return props.get('_setText', '') or props.get('_text', '') or ''

    def _clean_text(self, text: str) -> str:
        """Очистить текст от HTML тегов и лишних пробелов."""
        if not text:
            return ''
        # Убираем HTML теги типа <center>
        text = re.sub(r'<[^>]+>', '', text)
        # Убираем лишние пробелы
        text = text.strip()
        return text

    def _find_children_of_type(self, node: Dict, type_name: str) -> List[Dict]:
        """Найти дочерние узлы заданного типа (рекурсивно)."""
        results = []
        self._find_children_of_type_recursive(node, type_name, results)
        return results

    def _find_children_of_type_recursive(self, node: Dict, type_name: str, results: List):
        if not node:
            return
        if node.get('pythonObjectTypeName') == type_name:
            results.append(node)
        for child in (node.get('children') or []):
            if child:
                self._find_children_of_type_recursive(child, type_name, results)

    # =========== TARGETS ===========

    def parse_targets(self) -> List[Target]:
        """Распарсить залоченные цели."""
        targets = []
        target_nodes = self._find_nodes_by_type('TargetInBar')

        for node in target_nodes:
            target = self._parse_single_target(node)
            if target:
                targets.append(target)

        return targets

    def _parse_single_target(self, node: Dict) -> Optional[Target]:
        """Распарсить одну цель."""
        props = self._get_props(node)

        # Координаты
        display_x = props.get('_displayX')
        display_y = props.get('_displayY')
        display_width = props.get('_displayWidth')
        display_height = props.get('_displayHeight')

        # Извлекаем int если это словарь
        if isinstance(display_x, dict):
            display_x = display_x.get('int_low32', display_x.get('int'))
        if isinstance(display_y, dict):
            display_y = display_y.get('int_low32', display_y.get('int'))
        if isinstance(display_width, dict):
            display_width = display_width.get('int_low32', display_width.get('int'))
        if isinstance(display_height, dict):
            display_height = display_height.get('int_low32', display_height.get('int'))

        # Текстовые лейблы (имя, тип, дистанция)
        labels = self._find_children_of_type(node, 'EveLabelSmall')
        texts = [self._clean_text(self._get_text(l)) for l in labels]
        texts = [t for t in texts if t]  # убираем пустые

        name = texts[0] if len(texts) > 0 else '?'
        type_name = texts[1] if len(texts) > 1 else ''
        distance = texts[2] if len(texts) > 2 else ''

        # Активная цель?
        active_indicators = self._find_children_of_type(node, 'ActiveTargetIndicator')
        is_active = len(active_indicators) > 0

        return Target(
            name=name,
            type=type_name,
            distance=distance,
            is_active=is_active,
            display_x=display_x,
            display_y=display_y,
            display_width=display_width,
            display_height=display_height,
            raw=props
        )

    # =========== OVERVIEW ===========

    def parse_overview(self) -> List[OverviewEntry]:
        """Распарсить записи Overview."""
        entries = []
        entry_nodes = self._find_nodes_by_type('OverviewScrollEntry')

        for node in entry_nodes:
            entry = self._parse_single_overview_entry(node)
            if entry:
                entries.append(entry)

        return entries

    def _parse_single_overview_entry(self, node: Dict) -> Optional[OverviewEntry]:
        """Распарсить одну запись Overview."""
        props = self._get_props(node)

        # Координаты
        display_x = props.get('_displayX')
        display_y = props.get('_displayY')
        display_width = props.get('_displayWidth')
        display_height = props.get('_displayHeight')

        # Извлекаем int если это словарь
        if isinstance(display_x, dict):
            display_x = display_x.get('int_low32', display_x.get('int'))
        if isinstance(display_y, dict):
            display_y = display_y.get('int_low32', display_y.get('int'))
        if isinstance(display_width, dict):
            display_width = display_width.get('int_low32', display_width.get('int'))
        if isinstance(display_height, dict):
            display_height = display_height.get('int_low32', display_height.get('int'))

        # Найти все OverviewLabel внутри
        labels = self._find_children_of_type(node, 'OverviewLabel')

        texts = []
        icons = []
        for label in labels:
            text = self._clean_text(self._get_props(label).get('_text', ''))
            if text:
                if text == '-':
                    icons.append('-')
                else:
                    texts.append(text)

        # Обычно порядок: Type, Name, Distance (но может отличаться)
        # Попробуем определить по содержимому
        type_name = ''
        name = ''
        distance = ''

        for t in texts:
            # Дистанция содержит цифры и единицы измерения
            if re.search(r'\d+.*(?:км|м|а\.е\.|km|m|AU)', t, re.IGNORECASE):
                distance = t
            # Если нет type_name, первый текст - это type
            elif not type_name:
                type_name = t
            # Иначе это имя
            elif not name:
                name = t
            else:
                # Дополнительные колонки
                pass

        return OverviewEntry(
            name=name,
            type=type_name,
            distance=distance,
            icons=icons,
            display_x=display_x,
            display_y=display_y,
            display_width=display_width,
            display_height=display_height,
            raw=props
        )

    # =========== SHIP ===========

    def parse_ship(self) -> ShipState:
        """Распарсить состояние корабля."""
        state = ShipState()
        state.modules = self.parse_modules()
        # TODO: HP, capacitor, speed
        return state

    def parse_modules(self) -> List[Module]:
        """Распарсить модули корабля."""
        modules = []
        slot_nodes = self._find_nodes_by_type('ShipSlot')

        # Найти все busyContainer для определения активности
        busy_map = {}  # slot_address -> is_active
        all_nodes = self._get_all_nodes()

        for slot_node in slot_nodes:
            module = self._parse_single_module(slot_node)
            if module:
                modules.append(module)

        return modules

    def _parse_single_module(self, slot_node: Dict) -> Optional[Module]:
        """Распарсить один модуль."""
        props = self._get_props(slot_node)
        slot_name = props.get('_name', '')

        if not slot_name:
            return None

        # Координаты
        display_x = props.get('_displayX')
        display_y = props.get('_displayY')
        display_width = props.get('_displayWidth')
        display_height = props.get('_displayHeight')

        # Извлекаем int если это словарь
        if isinstance(display_x, dict):
            display_x = display_x.get('int_low32', display_x.get('int'))
        if isinstance(display_y, dict):
            display_y = display_y.get('int_low32', display_y.get('int'))
        if isinstance(display_width, dict):
            display_width = display_width.get('int_low32', display_width.get('int'))
        if isinstance(display_height, dict):
            display_height = display_height.get('int_low32', display_height.get('int'))

        # Активность - ищем busyContainer с children
        is_active = False
        busy_containers = self._find_children_by_name(slot_node, 'busyContainer')
        for bc in busy_containers:
            if bc.get('children'):
                is_active = True
                break

        # Количество патронов
        ammo_count = None
        labels = self._find_children_of_type(slot_node, 'Label')
        for label in labels:
            text = self._get_text(label)
            if text and text.isdigit():
                ammo_count = int(text)
                break

        # Перегрев
        is_overloaded = False
        overload_sprites = self._find_children_by_name(slot_node, 'overloadBtn')
        for sprite in overload_sprites:
            texture = self._get_props(sprite).get('_texturePath', '')
            if 'slotOverloadOn' in texture:
                is_overloaded = True
                break

        return Module(
            slot_name=slot_name,
            is_active=is_active,
            ammo_count=ammo_count,
            is_overloaded=is_overloaded,
            display_x=display_x,
            display_y=display_y,
            display_width=display_width,
            display_height=display_height,
            raw=props
        )

    def _find_children_by_name(self, node: Dict, name: str) -> List[Dict]:
        """Найти дочерние узлы по имени (рекурсивно)."""
        results = []
        self._find_children_by_name_recursive(node, name, results)
        return results

    def _find_children_by_name_recursive(self, node: Dict, name: str, results: List):
        if not node:
            return
        if self._get_props(node).get('_name') == name:
            results.append(node)
        for child in (node.get('children') or []):
            if child:
                self._find_children_by_name_recursive(child, name, results)
