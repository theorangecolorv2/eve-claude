# Работа с букмарками (локациями)

Модуль `eve/bookmarks.py` предоставляет функции для работы с букмарками (закладками локаций) в EVE Online.

## Требования

- Окно "Локации в системе" должно быть открыто в игре
- Букмарки должны быть видны в списке

## Основные функции

### get_bookmarks()

Получить список всех букмарков.

```python
from core.sanderling.service import SanderlingService
from eve.bookmarks import get_bookmarks

sanderling = SanderlingService()
sanderling.start()

bookmarks = get_bookmarks(sanderling)
for bookmark in bookmarks:
    print(f"{bookmark.name} at {bookmark.center}")
```

### find_bookmark()

Найти букмарк по имени (поддерживает частичное совпадение).

```python
from eve.bookmarks import find_bookmark

# Найти букмарк
bookmark = find_bookmark(sanderling, "1 SPOT 1")
if bookmark:
    print(f"Найден: {bookmark.name}")
    print(f"Координаты: {bookmark.center}")
    print(f"Границы: {bookmark.bounds}")
```

### click_bookmark()

Кликнуть на букмарк по имени.

```python
from eve.bookmarks import click_bookmark

# ЛКМ на букмарк
click_bookmark(sanderling, "1 SPOT 1")

# ПКМ на букмарк
click_bookmark(sanderling, "2 SPOT 2", button='right')
```

### right_click_bookmark()

ПКМ на букмарк (удобная обертка).

```python
from eve.bookmarks import right_click_bookmark

right_click_bookmark(sanderling, "3 HOME 3")
```

### double_click_bookmark()

Двойной клик на букмарк.

```python
from eve.bookmarks import double_click_bookmark

# Двойной клик обычно открывает меню действий
double_click_bookmark(sanderling, "1 SPOT 1")
```

### get_bookmark_coordinates()

Получить координаты букмарка.

```python
from eve.bookmarks import get_bookmark_coordinates

coords = get_bookmark_coordinates(sanderling, "2 SPOT 2")
if coords:
    x, y = coords
    print(f"Координаты: x={x}, y={y}")
```

## Структура данных Bookmark

```python
@dataclass
class Bookmark:
    name: str                              # Название букмарка
    hint: Optional[str] = None             # Подсказка (полное название)
    center: Optional[Tuple[int, int]] = None  # Координаты центра для клика
    bounds: Optional[Tuple[int, int, int, int]] = None  # x, y, width, height
```

## Примеры использования

### Пример 1: Список всех букмарков

```python
import time
from core.sanderling.service import SanderlingService
from eve.bookmarks import get_bookmarks

sanderling = SanderlingService()
sanderling.start()
time.sleep(3.0)

bookmarks = get_bookmarks(sanderling)
print(f"Найдено букмарков: {len(bookmarks)}")

for i, bookmark in enumerate(bookmarks, 1):
    print(f"{i}. {bookmark.name}")
    print(f"   Координаты: {bookmark.center}")
    print(f"   Границы: {bookmark.bounds}")

sanderling.stop()
```

### Пример 2: Поиск и клик на букмарк

```python
import time
from core.sanderling.service import SanderlingService
from eve.bookmarks import find_bookmark, click_bookmark

sanderling = SanderlingService()
sanderling.start()
time.sleep(3.0)

# Найти букмарк
bookmark = find_bookmark(sanderling, "SPOT 1")
if bookmark:
    print(f"Найден: {bookmark.name}")
    
    # Кликнуть на него
    click_bookmark(sanderling, "SPOT 1")
    print("Клик выполнен")

sanderling.stop()
```

### Пример 3: Работа с несколькими букмарками

```python
import time
from core.sanderling.service import SanderlingService
from eve.bookmarks import click_bookmark

sanderling = SanderlingService()
sanderling.start()
time.sleep(3.0)

# Список букмарков для обработки
bookmark_names = ["1 SPOT 1", "2 SPOT 2", "3 HOME 3"]

for name in bookmark_names:
    print(f"Обработка: {name}")
    
    # ПКМ на букмарк
    if click_bookmark(sanderling, name, button='right'):
        print(f"  ✓ Клик на {name}")
        time.sleep(1.0)
    else:
        print(f"  ✗ Не найден {name}")

sanderling.stop()
```

## Типичные сценарии

### Варп на букмарк

```python
from eve.bookmarks import right_click_bookmark
from eve.actions import select_action

# ПКМ на букмарк
right_click_bookmark(sanderling, "1 SPOT 1")
time.sleep(0.5)

# Выбрать "Warp to 0"
select_action(sanderling, "Warp")
```

### Установка destination

```python
from eve.bookmarks import right_click_bookmark
from eve.actions import select_action

# ПКМ на букмарк
right_click_bookmark(sanderling, "3 HOME 3")
time.sleep(0.5)

# Выбрать "Set Destination"
select_action(sanderling, "Set Destination")
```

## Отладка

Для отладки используйте скрипт `scripts/test_bookmarks.py`:

```bash
python scripts/test_bookmarks.py
```

Он покажет:
- Все найденные букмарки
- Их координаты
- Границы элементов

## Примечания

1. **Окно должно быть открыто**: Убедитесь что окно "Локации в системе" открыто
2. **Частичное совпадение**: Функция `find_bookmark()` ищет по частичному совпадению имени
3. **Координаты абсолютные**: Все координаты абсолютные (относительно экрана)
4. **Задержки**: После кликов рекомендуется делать задержки 0.3-0.5 секунд

## Смотрите также

- `scripts/test_bookmarks.py` - тест парсинга букмарков
- `scripts/example_bookmarks.py` - примеры использования
- `core/sanderling/parser.py` - парсер UI tree
- `core/sanderling/models.py` - модель Bookmark
