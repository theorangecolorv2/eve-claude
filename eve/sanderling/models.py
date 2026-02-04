# eve/sanderling/models.py
"""
Модели данных для Sanderling.

Структуры данных для удобного доступа к информации из памяти EVE Online.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class Target:
    """Залоченная цель."""
    name: str
    type: str
    distance: str
    is_active: bool = False

    # HP (опционально, если доступно)
    shield_percent: Optional[int] = None
    armor_percent: Optional[int] = None
    hull_percent: Optional[int] = None

    # Координаты на экране (для кликов)
    display_x: Optional[int] = None
    display_y: Optional[int] = None
    display_width: Optional[int] = None
    display_height: Optional[int] = None

    # Сырые данные (для отладки)
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def center(self) -> Optional[tuple]:
        """Центр элемента на экране."""
        if all([self.display_x, self.display_y, self.display_width, self.display_height]):
            return (
                self.display_x + self.display_width // 2,
                self.display_y + self.display_height // 2
            )
        return None


@dataclass
class OverviewEntry:
    """Запись в Overview."""
    name: str
    type: str
    distance: str

    # Иконки (статусы) слева
    icons: List[str] = field(default_factory=list)

    # Дополнительные колонки (если есть)
    columns: Dict[str, str] = field(default_factory=dict)

    # Координаты на экране
    display_x: Optional[int] = None
    display_y: Optional[int] = None
    display_width: Optional[int] = None
    display_height: Optional[int] = None

    # Сырые данные
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def center(self) -> Optional[tuple]:
        """Центр элемента на экране."""
        if all([self.display_x, self.display_y, self.display_width, self.display_height]):
            return (
                self.display_x + self.display_width // 2,
                self.display_y + self.display_height // 2
            )
        return None

    @property
    def distance_km(self) -> Optional[float]:
        """Дистанция в километрах (парсинг из строки)."""
        try:
            dist = self.distance.replace('\xa0', ' ').replace(' ', '')
            if 'км' in dist or 'km' in dist:
                num = ''.join(c for c in dist if c.isdigit() or c in '.,')
                return float(num.replace(',', '.'))
            elif 'м' in dist or 'm' in dist:
                num = ''.join(c for c in dist if c.isdigit() or c in '.,')
                return float(num.replace(',', '.')) / 1000
            elif 'а.е.' in dist or 'AU' in dist:
                num = ''.join(c for c in dist if c.isdigit() or c in '.,')
                return float(num.replace(',', '.')) * 149_597_870.7  # 1 AU в км
        except:
            pass
        return None


@dataclass
class Module:
    """Модуль корабля."""
    slot_name: str  # например "inFlightHighSlot1"
    is_active: bool = False

    # Количество зарядов
    ammo_count: Optional[int] = None

    # Перегрев
    is_overloaded: bool = False

    # Координаты на экране
    display_x: Optional[int] = None
    display_y: Optional[int] = None
    display_width: Optional[int] = None
    display_height: Optional[int] = None

    # Сырые данные
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def center(self) -> Optional[tuple]:
        """Центр элемента на экране."""
        if all([self.display_x, self.display_y, self.display_width, self.display_height]):
            return (
                self.display_x + self.display_width // 2,
                self.display_y + self.display_height // 2
            )
        return None

    @property
    def slot_type(self) -> Optional[str]:
        """Тип слота: high, medium, low."""
        name = self.slot_name.lower()
        if 'high' in name:
            return 'high'
        elif 'medium' in name or 'med' in name:
            return 'medium'
        elif 'low' in name:
            return 'low'
        return None

    @property
    def slot_number(self) -> Optional[int]:
        """Номер слота."""
        import re
        match = re.search(r'(\d+)$', self.slot_name)
        if match:
            return int(match.group(1))
        return None


@dataclass
class ShipState:
    """Состояние корабля."""
    # HP в процентах
    shield_percent: Optional[int] = None
    armor_percent: Optional[int] = None
    hull_percent: Optional[int] = None

    # Капаситор
    capacitor_percent: Optional[int] = None

    # Скорость (если доступно)
    speed: Optional[str] = None

    # Модули
    modules: List[Module] = field(default_factory=list)

    @property
    def active_modules_count(self) -> int:
        """Количество активных модулей."""
        return sum(1 for m in self.modules if m.is_active)

    @property
    def high_slots(self) -> List[Module]:
        """Модули в хай-слотах."""
        return [m for m in self.modules if m.slot_type == 'high']

    @property
    def medium_slots(self) -> List[Module]:
        """Модули в мид-слотах."""
        return [m for m in self.modules if m.slot_type == 'medium']

    @property
    def low_slots(self) -> List[Module]:
        """Модули в лоу-слотах."""
        return [m for m in self.modules if m.slot_type == 'low']


@dataclass
class GameState:
    """Полное состояние игры из одного чтения памяти."""
    # Время чтения
    timestamp: float = 0.0

    # Время чтения памяти (мс)
    read_time_ms: int = 0

    # Количество узлов в UI tree
    node_count: int = 0

    # Данные
    targets: List[Target] = field(default_factory=list)
    overview: List[OverviewEntry] = field(default_factory=list)
    ship: ShipState = field(default_factory=ShipState)

    # Сырой JSON (для отладки)
    raw_json: Optional[str] = None

    @property
    def targets_count(self) -> int:
        return len(self.targets)

    @property
    def overview_count(self) -> int:
        return len(self.overview)

    @property
    def active_target(self) -> Optional[Target]:
        """Текущая активная цель."""
        for t in self.targets:
            if t.is_active:
                return t
        return None

    @property
    def has_targets(self) -> bool:
        return len(self.targets) > 0
