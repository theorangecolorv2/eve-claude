# Работа с инвентарем через Sanderling

## Обзор

Модуль `eve/inventory.py` предоставляет высокоуровневый API для работы с инвентарем EVE Online через Sanderling. Все координаты вычисляются автоматически и являются абсолютными (относительно экрана).

## Возможности

- ✅ Получение абсолютных координат фильтров инвентаря
- ✅ Получение абсолютных координат предметов
- ✅ Активация фильтров
- ✅ Поиск предметов по имени
- ✅ Правый клик по предметам
- ✅ Работа с контекстным меню
- ✅ Использование предметов (включая филаменты)

## Конфигурация

Все захардкоженные значения находятся в **`config.py`**:

```python
# Названия фильтров инвентаря
INVENTORY_FILTERS = {
    'FILAMENT': '!FILAMENT!',
    'DOCK': '!DOCK!',
    'AMMUNITION': 'Ammunition',
    # ...
}

# Названия филаментов
FILAMENT_NAMES = {
    'CALM_EXOTIC': 'Calm Exotic Filament',
    'CALM_DARK': 'Calm Dark Filament',
    # ...
}

# Названия действий в контекстном меню
CONTEXT_MENU_ACTIONS = {
    'USE': 'Использовать',
    'USE_EN': 'Use',
    'ACTIVATE': 'Активировать',
    # ...
}
```

## Структура данных

### InventoryWindow

```python
@dataclass
class InventoryWindow:
    is_open: bool                           # Открыт ли инвентарь
    center: Tuple[int, int]                 # Центр окна (абсолютные координаты)
    bounds: Tuple[int, int, int, int]       # x, y, width, height
    filters: List[InventoryFilter]          # Список фильтров
    items: List[InventoryItem]              # Список предметов
```

### InventoryFilter

```python
@dataclass
class InventoryFilter:
    name: str                               # Название фильтра
    center: Tuple[int, int]                 # АБСОЛЮТНЫЕ координаты для клика
    bounds: Tuple[int, int, int, int]       # x, y, width, height
    is_active: bool                         # Активен ли фильтр
```

### InventoryItem

```python
@dataclass
class InventoryItem:
    name: str                               # Название предмета
    hint: Optional[str]                     # Подсказка (полное название)
    quantity: int                           # Количество
    center: Tuple[int, int]                 # АБСОЛЮТНЫЕ координаты для клика
    bounds: Tuple[int, int, int, int]       # x, y, width, height
    texture_path: Optional[str]             # Путь к текстуре иконки
```

### ContextMenu

```python
@dataclass
class ContextMenu:
    is_open: bool                           # Открыто ли меню
    items: List[ContextMenuItem]            # Пункты меню

@dataclass
class ContextMenuItem:
    text: str                               # Текст пункта меню
    center: Tuple[int, int]                 # АБСОЛЮТНЫЕ координаты для клика
    bounds: Tuple[int, int, int, int]       # x, y, width, height
```

## Использование

### Базовый пример

```python
from core.sanderling.service import SanderlingService
from eve.inventory import InventoryManager
from config import INVENTORY_FILTERS, FILAMENT_NAMES

# Запустить Sanderling
service = SanderlingService()
service.start()

# Создать менеджер инвентаря
inventory = InventoryManager(service)

# Проверить что инвентарь открыт
if inventory.is_open():
    print("Инвентарь открыт")
    
    # Получить состояние
    state = service.get_state()
    print(f"Фильтров: {len(state.inventory.filters)}")
    print(f"Предметов: {len(state.inventory.items)}")
```

### Работа с фильтрами

```python
# Найти фильтр
filter_obj = inventory.get_filter(INVENTORY_FILTERS['FILAMENT'])
if filter_obj:
    print(f"Фильтр найден: {filter_obj.name}")
    print(f"Координаты: {filter_obj.center}")
    print(f"Активен: {filter_obj.is_active}")

# Активировать фильтр
inventory.activate_filter(INVENTORY_FILTERS['FILAMENT'])
```

### Поиск и использование предметов

```python
# Найти предмет
item = inventory.find_item("Calm Exotic Filament")
if item:
    print(f"Предмет найден: {item.name}")
    print(f"Координаты: {item.center}")
    
    # Правый клик по предмету
    inventory.right_click_item(item)
    
    # Кликнуть по пункту меню
    inventory.click_context_menu_item("Использовать")
```

### Использование филамента (полный автоматический цикл)

```python
from config import FILAMENT_NAMES

# Использовать филамент (автоматически открывает инвентарь, активирует фильтр и использует предмет)
success = inventory.use_filament(FILAMENT_NAMES['CALM_EXOTIC'])
if success:
    print("Филамент использован!")
```

Метод `use_filament()` выполняет полный цикл:
1. ✅ Открывает инвентарь если закрыт (клик по Inventory в Neocom)
2. ✅ Активирует фильтр !FILAMENT! если не активен
3. ✅ Складывает все филаменты в стопки (Stack All) - решает проблему с несколькими стопками одинаковых филаментов
4. ✅ Находит филамент
5. ✅ Делает правый клик
6. ✅ Кликает "Использовать"

### Складывание предметов в стопки

```python
# Сложить все предметы в стопки (полезно когда несколько стопок одинаковых предметов)
success = inventory.stack_all_items()
if success:
    print("Предметы сложены в стопки!")
```

Метод `stack_all_items()` выполняет:
1. ✅ Находит любой предмет в инвентаре
2. ✅ Делает правый клик
3. ✅ Кликает "Сложить все предметы в стопки" (Stack All)
4. ✅ Ждет завершения операции (2 секунды)

## Тестовые скрипты

### test_inventory.py

Показывает все найденные фильтры и предметы с их абсолютными координатами:

```bash
python scripts/test_inventory.py
```

Вывод:
```
[ФИЛЬТРЫ] Найдено: 7
  1. !DOCK! [НЕАКТИВЕН]
     Координаты для клика: (259, 367)
     Границы: (199, 356, 120, 22)
  2. !FILAMENT! [НЕАКТИВЕН]
     Координаты для клика: (259, 389)
     Границы: (199, 378, 120, 22)
  ...

[ПРЕДМЕТЫ] Найдено: 1
  1. Calm Exotic Filament
     Координаты для клика: (450, 520)
     Границы: (418, 488, 64, 64)
     Текстура: res:/UI/Texture/Icons/Inventory/abyssalFilamentL1.png
```

### test_use_filament.py

Демонстрирует полный цикл использования филамента:

```bash
python scripts/test_use_filament.py
```

Выполняет:
1. Проверку что инвентарь открыт
2. Активацию фильтра !FILAMENT!
3. Поиск филамента
4. Правый клик по филаменту
5. Клик по "Использовать"

## Требования

1. **EVE Online должен быть запущен**
2. **Фильтр !FILAMENT! должен быть создан** в инвентаре
3. **Филамент должен быть в инвентаре**
4. **Боковая панель Neocom должна быть видна** (слева)

**Инвентарь открывать вручную НЕ нужно** - бот откроет автоматически через кнопку Inventory в Neocom!

## Создание фильтра !FILAMENT!

1. Откройте инвентарь (Alt+C)
2. Нажмите на иконку "+" рядом с фильтрами
3. Введите название: `!FILAMENT!`
4. Настройте фильтр чтобы показывать только филаменты
5. Сохраните фильтр

## Добавление новых предметов

Чтобы добавить поддержку новых предметов, просто добавьте их в `config.py`:

```python
# В config.py
FILAMENT_NAMES = {
    'CALM_EXOTIC': 'Calm Exotic Filament',
    'MY_NEW_FILAMENT': 'My New Filament Name',  # <-- Добавить здесь
}
```

Затем используйте:

```python
inventory.use_filament(FILAMENT_NAMES['MY_NEW_FILAMENT'])
```

## Отладка

Если что-то не работает:

1. Запустите `test_inventory.py` чтобы увидеть что парсится
2. Проверьте что фильтр создан с правильным именем
3. Проверьте что предмет виден в инвентаре
4. Проверьте логи Sanderling

## API Reference

### InventoryManager

#### `__init__(sanderling: SanderlingService)`
Создает менеджер инвентаря.

#### `is_open() -> bool`
Проверяет открыт ли инвентарь.

#### `open_inventory() -> bool`
Открывает инвентарь через клик по кнопке Inventory в Neocom (боковая панель слева).

#### `get_filter(filter_name: str) -> Optional[InventoryFilter]`
Находит фильтр по имени.

#### `activate_filter(filter_name: str) -> bool`
Активирует фильтр инвентаря (кликает если не активен).

#### `find_item(item_name: str) -> Optional[InventoryItem]`
Находит предмет в инвентаре (поиск по частичному совпадению).

#### `right_click_item(item: InventoryItem) -> bool`
Делает правый клик по предмету (открывает контекстное меню).

#### `click_context_menu_item(menu_text: str) -> bool`
Кликает по пункту контекстного меню.

#### `stack_all_items() -> bool`
Складывает все предметы в стопки через контекстное меню (решает проблему с несколькими стопками одинаковых предметов).

#### `use_item(item_name: str) -> bool`
Использует предмет из инвентаря (полный цикл: поиск -> правый клик -> использовать).

#### `use_filament(filament_name: str) -> bool`
Использует филамент (полный автоматический цикл: открывает инвентарь -> активирует фильтр -> складывает в стопки -> находит -> использует).

## Примечания

- Все координаты являются **абсолютными** (относительно экрана)
- Координаты вычисляются с учетом всех родительских элементов
- Координаты указывают на **центр** элемента (оптимально для клика)
- Парсинг работает в реальном времени через Sanderling
- Поддерживается как русский так и английский клиент EVE

---

## История изменений

### v0.5.2 (2026-02-06)
- ✅ Добавлена функция `stack_all_items()` для складывания предметов в стопки
- ✅ Метод `use_filament()` теперь автоматически складывает филаменты в стопки перед использованием
- ✅ Решена проблема с несколькими стопками одинаковых филаментов
- ✅ Добавлена поддержка действия "Stack All" в контекстном меню (русский и английский)

### v0.5.1 (2026-02-04)
- ✅ Добавлено автоматическое открытие инвентаря через клик по Inventory в Neocom (боковая панель слева)
- ✅ Улучшена активация фильтров (проверка после клика)
- ✅ Метод `use_filament()` теперь полностью автоматический
- ✅ Убрана зависимость от горячих клавиш (только клики мышью)
- ✅ Новый скрипт `use_filament_auto.py` для максимально простого использования

### v0.5.0 (2026-02-03)
- ✅ Первая версия модуля инвентаря
- ✅ Парсинг фильтров и предметов с абсолютными координатами
- ✅ Высокоуровневый API для работы с инвентарем
- ✅ Поддержка контекстного меню
- ✅ Единый конфиг `config.py` для всех настроек
