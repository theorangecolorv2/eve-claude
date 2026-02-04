"""
Единый конфигурационный файл для всего бота EVE Online.
Все захардкоженные значения собраны здесь.
"""

# ============================================================================
# ОБЩИЕ НАСТРОЙКИ
# ============================================================================

# Задержки (секунды)
DELAY_AFTER_CLICK = 0.5
DELAY_AFTER_LOCK = 3.0
DELAY_AFTER_APPROACH = 1.0
DELAY_AFTER_GUNS = 0.5
DELAY_AFTER_WARP = 2.0
DELAY_AFTER_JUMP = 5.0
DELAY_BETWEEN_ACTIONS = 1.0
DELAY_SCREENSHOT = 0.1

# Таймауты (секунды)
TIMEOUT_TARGET_LOCK = 10.0
TIMEOUT_TARGET_KILL = 60.0
TIMEOUT_WARP = 30.0
TIMEOUT_JUMP = 15.0

# ============================================================================
# НАЗВАНИЯ И ТЕКСТ
# ============================================================================

# Названия целей (для поиска в Overview)
TARGET_NAMES = {
    'PITHI': 'Pithi',
    'SANSHA': 'Sansha',
    'GURISTAS': 'Guristas',
    'ANGEL': 'Angel',
    'BLOOD': 'Blood',
}

# Названия аномалий
ANOMALY_NAMES = {
    'UBEJISHE': 'Убежище',
    'UKRYTIE': 'Укрытие',
    'RALLY_POINT': 'Rally Point',
    'HIDEAWAY': 'Hideaway',
}

# Названия станций/структур
STATION_NAMES = {
    'JITA': 'Jita',
    'AMARR': 'Amarr',
}

# Названия вкладок Overview
OVERVIEW_TABS = {
    'PVP': 'PvP',
    'PVE': 'PvE',
    'MINING': 'Mining',
    'TRAVEL': 'Travel',
    'DOCK': 'Dock',
    'JUMP': 'Jump',
}

# Названия кнопок Neocom
NEOCOM_BUTTONS = {
    'INVENTORY': 'Inventory',
    'CARGO': 'Cargo',
    'SHIP': 'Ship',
    'MARKET': 'Market',
    'JOURNAL': 'Journal',
}

# ============================================================================
# ИНВЕНТАРЬ И ПРЕДМЕТЫ
# ============================================================================

# Названия фильтров инвентаря
INVENTORY_FILTERS = {
    'FILAMENT': '!FILAMENT!',
    'DOCK': '!DOCK!',
    'AMMUNITION': 'Ammunition',
    'ORE': 'Ore and Materials',
    'MODULES': 'Ship modules',
    'SKILLBOOKS': 'Skillbooks',
    'VALUABLE': 'Valuable Items',
}

# Названия филаментов
FILAMENT_NAMES = {
    'CALM_EXOTIC': 'Calm Exotic Filament',
    'CALM_DARK': 'Calm Dark Filament',
    'CALM_ELECTRICAL': 'Calm Electrical Filament',
    'CALM_FIRESTORM': 'Calm Firestorm Filament',
    'CALM_GAMMA': 'Calm Gamma Filament',
}

# Текстуры филаментов (для поиска по иконке)
FILAMENT_TEXTURES = {
    'LEVEL_1': 'abyssalFilamentL1.png',
    'LEVEL_2': 'abyssalFilamentL2.png',
    'LEVEL_3': 'abyssalFilamentL3.png',
    'LEVEL_4': 'abyssalFilamentL4.png',
    'LEVEL_5': 'abyssalFilamentL5.png',
}

# Названия действий в контекстном меню
CONTEXT_MENU_ACTIONS = {
    'USE': 'Использовать',
    'USE_EN': 'Use',
    'ACTIVATE': 'Активировать',
    'ACTIVATE_EN': 'Activate',
    'WARP_TO': 'Warp to',
    'APPROACH': 'Approach',
    'ORBIT': 'Orbit',
    'KEEP_AT_RANGE': 'Keep at range',
    'DOCK': 'Dock',
    'JUMP': 'Jump',
    'LOCK_TARGET': 'Lock target',
}

# ============================================================================
# БОЕВЫЕ НАСТРОЙКИ
# ============================================================================

# Клавиши модулей
MODULE_KEYS = {
    'GUNS': '1',
    'MISSILES': '2',
    'SHIELD_BOOSTER': '3',
    'ARMOR_REPAIRER': '4',
    'AFTERBURNER': '5',
    'MWD': '6',
    'PROP_MOD': '5',  # Afterburner или MWD
}

# Пороги здоровья (0.0 - 1.0)
HEALTH_THRESHOLDS = {
    'SHIELD_LOW': 0.3,
    'ARMOR_LOW': 0.5,
    'HULL_CRITICAL': 0.7,
    'CAPACITOR_LOW': 0.2,
}

# Дистанции (метры)
DISTANCES = {
    'OPTIMAL_RANGE': 10000,
    'FALLOFF_RANGE': 20000,
    'WARP_MIN': 150000,
    'APPROACH_RANGE': 5000,
    'ORBIT_RANGE': 7500,
}

# ============================================================================
# НАВИГАЦИЯ
# ============================================================================

# Типы варпа
WARP_DISTANCES = {
    'ZERO': '0',
    '10KM': '10',
    '20KM': '20',
    '30KM': '30',
    '50KM': '50',
    '70KM': '70',
    '100KM': '100',
}

# ============================================================================
# КОМПЬЮТЕРНОЕ ЗРЕНИЕ (CV)
# ============================================================================

# Пороги совпадения для template matching
CV_THRESHOLDS = {
    'HIGH': 0.9,      # Высокая точность (кнопки, иконки)
    'MEDIUM': 0.8,    # Средняя точность (текст)
    'LOW': 0.7,       # Низкая точность (размытые элементы)
}

# Пути к шаблонам (относительно папки assets/)
CV_TEMPLATES = {
    # Аномалии
    'ANOMALY_UBEJISHE': 'eve_anomaly_ubejishe.png',
    'ANOMALY_UBEJISHE_HL': 'eve_anomaly_ubejishe_highlighted.png',
    'ANOMALY_UKRYTIE': 'eve_anomaly_ukrytie.png',
    'ANOMALY_UKRYTIE_HL': 'eve_anomaly_ukrytie_highlighted.png',
    
    # Кнопки и элементы UI
    'BUTTON_JUMP': 'eve_button_jump.png',
    'TAB_JUMP': 'eve_tab_jump.png',
    'TAB_PVP_FOE': 'eve_tab_pvp_foe.png',
    'WARP_0': 'eve_warp_0.png',
    'WARP_10KM': 'eve_warp_10km.png',
    'WARP_SUBMENU': 'eve_warp_submenu.png',
    
    # Гейты и объекты
    'GATE_YELLOW': 'eve_gate_yellow.png',
    'GATE_YELLOW2': 'eve_gate_yellow2.png',
    
    # Модули
    'GUN_MODULE': 'eve_gun_module.png',
    
    # HUD элементы
    'HUD_ANCHOR': 'eve_hud_anchor.png',
    'LOCK_ANCHOR': 'eve_lock_anchor.png',
    'SPEED_ZERO': 'eve_speed_zero.png',
    
    # Overview
    'OVERVIEW_EMPTY': 'eve_overview_empty.png',
    'OVERVIEW_HEADER_NAME': 'eve_overview_header_name.png',
    'OVERVIEW_TITLE': 'eve_overview_title.png',
    
    # Экспедиции
    'EXPEDITION_CLOSE': 'eve_expedition_close.png',
    'EXPEDITION_CLOSE2': 'eve_expedition_close2.png',
    'EXPEDITION_POPUP': 'eve_expedition_popup.png',
    'EXPEDITION_TEXT': 'eve_expedition_text.png',
}

# ============================================================================
# SANDERLING
# ============================================================================

# Типы узлов UI tree
SANDERLING_NODE_TYPES = {
    # Цели
    'TARGET': 'TargetInBar',
    'TARGET_SELECTED': 'SelectedItemView',
    
    # Overview
    'OVERVIEW_WINDOW': 'OverviewWindow',
    'OVERVIEW_ENTRY': 'OverviewScrollEntry',
    'OVERVIEW_LABEL': 'OverviewLabel',
    'OVERVIEW_TAB': 'OverviewTab',
    
    # Модули
    'SHIP_SLOT': 'ShipSlot',
    'MODULE_BUTTON': 'ModuleButton',
    
    # Инвентарь
    'INVENTORY_PRIMARY': 'InventoryPrimary',
    'INVENTORY_FILTERS': 'InvFilters',
    'FILTER_ENTRY': 'FilterEntry',
    'TREE_VIEW_ENTRY': 'TreeViewEntryInventory',
    'TREE_VIEW_CARGO': 'TreeViewEntryInventoryCargo',
    
    # Neocom
    'NEOCOM_BUTTON': 'LeftSideButtonCargo',
    
    # Здоровье
    'SHIP_GAUGE': 'ShipHudSpriteGauge',
    'CAPACITOR': 'CapacitorContainer',
    'SPEED_GAUGE': 'SpeedGauge',
    
    # Контекстное меню
    'MENU': 'Menu',
    'MENU_ENTRY': 'MenuEntry',
    'MENU_BUTTON': 'MenuButtonIcon',
    
    # Окна
    'WINDOW': 'Window',
    'BUTTON': 'Button',
    'CHECKBOX': 'Checkbox',
    'LABEL': 'EveLabelMedium',
}

# Имена gauge для здоровья корабля
SANDERLING_GAUGE_NAMES = {
    'SHIELD': 'shieldGauge',
    'ARMOR': 'armorGauge',
    'HULL': 'structureGauge',
}

# ============================================================================
# TELEGRAM УВЕДОМЛЕНИЯ
# ============================================================================

# Типы уведомлений
TELEGRAM_NOTIFICATIONS = {
    'BOT_STARTED': '🤖 Бот запущен',
    'BOT_STOPPED': '🛑 Бот остановлен',
    'TARGET_KILLED': '💀 Цель уничтожена',
    'ANOMALY_COMPLETED': '✅ Аномалия завершена',
    'HEALTH_LOW': '⚠️ Низкое здоровье',
    'CAPACITOR_LOW': '⚡ Низкая энергия',
    'ERROR': '❌ Ошибка',
    'WARNING': '⚠️ Предупреждение',
    'EXPEDITION_FOUND': '🎁 Найдена экспедиция',
}

# ============================================================================
# ЛОГИРОВАНИЕ
# ============================================================================

# Уровни логирования
LOG_LEVELS = {
    'DEBUG': 10,
    'INFO': 20,
    'WARNING': 30,
    'ERROR': 40,
    'CRITICAL': 50,
}

# Формат логов
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# ============================================================================
# ПУТИ К ФАЙЛАМ
# ============================================================================

# Папки
FOLDERS = {
    'ASSETS': 'assets',
    'LOGS': 'logs',
    'DATA': 'data',
    'TEMP': 'temp',
    'OUTPUT': 'output',
}

# Файлы данных
DATA_FILES = {
    'BOT_STATS': 'data/bot_stats.json',
    'TELEGRAM_USERS': 'data/telegram_users.json',
}

# ============================================================================
# РЕЖИМЫ РАБОТЫ БОТА
# ============================================================================

# Типы ботов
BOT_MODES = {
    'ANOMALY_FARMER': 'anomaly_farmer',
    'ABYSS_FARMER': 'abyss_farmer',
    'MINING': 'mining',
    'HAULING': 'hauling',
}

# Состояния бота
BOT_STATES = {
    'IDLE': 'idle',
    'SEARCHING': 'searching',
    'WARPING': 'warping',
    'COMBAT': 'combat',
    'LOOTING': 'looting',
    'DOCKING': 'docking',
    'ERROR': 'error',
}
