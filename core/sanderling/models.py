"""Data models for Sanderling UI tree parsing."""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class Target:
    """Залоченная цель."""
    name: str
    type: str
    distance: Optional[float] = None
    is_active: bool = False
    center: Optional[Tuple[int, int]] = None
    bounds: Optional[Tuple[int, int, int, int]] = None  # x, y, width, height
    
    # Здоровье цели (0.0-1.0)
    shield: Optional[float] = None
    armor: Optional[float] = None
    hull: Optional[float] = None


@dataclass
class OverviewEntry:
    """Запись в Overview."""
    index: int
    name: Optional[str] = None
    type: Optional[str] = None
    distance: Optional[str] = None
    center: Optional[Tuple[int, int]] = None
    bounds: Optional[Tuple[int, int, int, int]] = None


@dataclass
class Module:
    """Модуль корабля."""
    slot_type: str  # 'high', 'mid', 'low'
    slot_name: str
    is_active: bool = False
    ammo_count: Optional[int] = None
    center: Optional[Tuple[int, int]] = None


@dataclass
class SelectedAction:
    """Доступное действие с выбранным объектом."""
    name: str  # 'approach', 'warpTo', 'orbit', etc.
    center: Tuple[int, int]  # Координаты кнопки для клика
    texture_path: Optional[str] = None


@dataclass
class OverviewTab:
    """Вкладка обзора."""
    name: str  # Имя вкладки
    label: str  # Текст на вкладке (например, "✈ Jump", "✥ PvP Foe")
    center: Tuple[int, int]  # Координаты для клика


@dataclass
class NeocomButton:
    """Кнопка Neocom (боковая панель)."""
    button_type: str  # 'cargo', 'inventory', 'tactical', 'scanner', 'autopilot', etc.
    center: Tuple[int, int]  # АБСОЛЮТНЫЕ координаты для клика


@dataclass
class ShipState:
    """Состояние корабля."""
    modules: List[Module] = field(default_factory=list)
    
    # Здоровье корабля (0.0-1.0)
    shield: float = 1.0
    armor: float = 1.0
    hull: float = 1.0
    
    # Энергия и скорость
    capacitor: float = 1.0  # 0.0-1.0
    speed: float = 0.0  # м/с


@dataclass
class InventoryFilter:
    """Фильтр инвентаря."""
    name: str  # Название фильтра (например, "!FILAMENT!")
    center: Tuple[int, int]  # АБСОЛЮТНЫЕ координаты для клика
    bounds: Tuple[int, int, int, int]  # x, y, width, height (абсолютные)
    is_active: bool = False  # Активен ли фильтр


@dataclass
class InventoryItem:
    """Предмет в инвентаре."""
    name: str  # Название предмета
    hint: Optional[str] = None  # Подсказка (полное название)
    quantity: int = 1  # Количество
    center: Tuple[int, int] = None  # АБСОЛЮТНЫЕ координаты для клика
    bounds: Optional[Tuple[int, int, int, int]] = None  # x, y, width, height
    texture_path: Optional[str] = None  # Путь к текстуре иконки
    item_type: Optional[str] = None  # Тип предмета


@dataclass
class InventoryWindow:
    """Окно инвентаря."""
    is_open: bool = False
    center: Tuple[int, int] = None  # Центр окна
    bounds: Optional[Tuple[int, int, int, int]] = None  # x, y, width, height
    filters: List[InventoryFilter] = field(default_factory=list)
    items: List[InventoryItem] = field(default_factory=list)
    loot_all_button: Optional[Tuple[int, int]] = None  # Координаты кнопки "Взять все"


@dataclass
class ContextMenuItem:
    """Пункт контекстного меню."""
    text: str  # Текст пункта меню
    center: Tuple[int, int]  # АБСОЛЮТНЫЕ координаты для клика
    bounds: Optional[Tuple[int, int, int, int]] = None


@dataclass
class ContextMenu:
    """Контекстное меню."""
    is_open: bool = False
    items: List[ContextMenuItem] = field(default_factory=list)


@dataclass
class Drone:
    """Дрон в космосе или в отсеке."""
    name: str  # Название дрона (например, "Caldari Navy Hornet")
    state: str  # Состояние: "Idle" (Бездействует), "Fighting" (Сражается), "Returning" (Возвращается)
    
    # Здоровье дрона (0.0-1.0)
    shield: float = 1.0
    armor: float = 1.0
    hull: float = 1.0
    
    # Координаты записи в окне дронов
    center: Optional[Tuple[int, int]] = None
    bounds: Optional[Tuple[int, int, int, int]] = None


@dataclass
class DronesState:
    """Состояние дронов."""
    drones_in_space: List[Drone] = field(default_factory=list)  # Дроны в космосе
    drones_in_bay: List[Drone] = field(default_factory=list)  # Дроны в отсеке
    
    # Количество дронов
    in_space_count: int = 0  # Сколько дронов в космосе
    max_drones: int = 5  # Максимум дронов
    
    # Окно дронов открыто?
    window_open: bool = False


@dataclass
class Bookmark:
    """Букмарк (локация)."""
    name: str  # Название букмарка (например, "1 SPOT 1", "2 SPOT 2", "3 HOME 3")
    hint: Optional[str] = None  # Подсказка (полное название)
    center: Optional[Tuple[int, int]] = None  # АБСОЛЮТНЫЕ координаты для клика
    bounds: Optional[Tuple[int, int, int, int]] = None  # x, y, width, height (абсолютные)


@dataclass
class GameState:
    """Состояние игры из UI tree."""
    targets: List[Target] = field(default_factory=list)
    overview: List[OverviewEntry] = field(default_factory=list)
    ship: Optional[ShipState] = None
    selected_actions: List[SelectedAction] = field(default_factory=list)
    overview_tabs: List[OverviewTab] = field(default_factory=list)
    neocom_buttons: List[NeocomButton] = field(default_factory=list)
    inventory: Optional[InventoryWindow] = None
    context_menu: Optional[ContextMenu] = None
    drones: Optional[DronesState] = None
    bookmarks: List[Bookmark] = field(default_factory=list)
    ui_tree: Optional[dict] = None  # Сырое UI tree для дополнительного парсинга
    timestamp: float = 0.0
    is_valid: bool = True
    warnings: List[str] = field(default_factory=list)
