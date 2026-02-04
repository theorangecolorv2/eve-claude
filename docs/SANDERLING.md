# Sanderling Service - Полная документация

## 📋 СОДЕРЖАНИЕ

1. [Быстрый старт](#быстрый-старт)
2. [Архитектура](#архитектура)
3. [Модели данных](#модели-данных)
4. [API сервиса](#api-сервиса)
5. [Примеры использования](#примеры-использования)
6. [Оптимизация (RAMDisk)](#оптимизация-ramdisk)
7. [Troubleshooting](#troubleshooting)

---

## 🚀 БЫСТРЫЙ СТАРТ

### Запуск сервиса

```python
from core.sanderling import SanderlingService

# Создать и запустить сервис
service = SanderlingService()
service.start()  # Автоматически найдет EVE, root address, запустит фоновый поток

# Получить данные
state = service.get_state()
print(f"Targets: {len(state.targets)}")
print(f"Shield: {state.ship.shield * 100:.0f}%")
print(f"Speed: {state.ship.speed:.0f} м/с")

# Остановить
service.stop()
```

### Тестирование

```bash
python scripts/test_sanderling.py
```

---

## 🏗️ АРХИТЕКТУРА

### Схема работы

```
┌─────────────────────────────────────────────────────────────┐
│                      EVE Online Process                     │
│                       (exefile.exe)                         │
└──────────────────────────┬──────────────────────────────────┘
                           │ читает память
                           ▼
┌─────────────────────────────────────────────────────────────┐
│           Sanderling (read-memory-64-bit.exe)               │
│                    Внешний C# процесс                       │
│         Сохраняет JSON в temp/ или R:/temp (RAMDisk)        │
└──────────────────────────┬──────────────────────────────────┘
                           │ парсит JSON
                           ▼
┌─────────────────────────────────────────────────────────────┐
│            SanderlingService (Python, фоновый поток)        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  while True:                                         │   │
│  │    1. Запустить Sanderling                          │   │
│  │    2. Прочитать JSON из temp/                       │   │
│  │    3. Распарсить в GameState                        │   │
│  │    4. Сохранить в self.last_state (с lock)          │   │
│  │    5. time.sleep(1.0)  # 1 секунда                  │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │ get_state()
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Ваш бот (main.py)                        │
│                                                             │
│  state = service.get_state()  # Получить весь state        │
│  if state.ship.shield < 0.3:  # Использовать данные        │
│      warp_out()                                             │
└─────────────────────────────────────────────────────────────┘
```

### Ключевые особенности

**Thread Safety:**
- Фоновый поток **пишет** `last_state` каждую секунду
- Основной поток (бот) **читает** `last_state` в любой момент
- `threading.Lock` защищает от race conditions

**Один State = Один снимок:**
- Все данные из одного момента времени
- Согласованность данных гарантирована
- Быстро (1 чтение вместо N вызовов)

**Автоматическая оптимизация:**
- Использует RAMDisk (R:/temp) если доступен
- Fallback на обычный диск (temp/)
- Файлы удаляются сразу после чтения

---

## 📦 МОДЕЛИ ДАННЫХ

### GameState (главный объект)

```python
@dataclass
class GameState:
    targets: List[Target]                    # Залоченные цели
    overview: List[OverviewEntry]            # Записи в overview
    ship: ShipState                          # Состояние корабля
    selected_actions: List[SelectedAction]   # Доступные действия
    overview_tabs: List[OverviewTab]         # Вкладки overview
    neocom_buttons: List[NeocomButton]       # Кнопки боковой панели (Neocom)
    timestamp: float                         # Unix timestamp
    is_valid: bool                           # Валидность данных
    warnings: List[str]                      # Предупреждения
```

**Получение:**
```python
state = service.get_state()
```

---

### Target (залоченная цель)

```python
@dataclass
class Target:
    name: str                           # "Hornet* [GAM B]"
    type: str                           # "Guristas"
    distance: Optional[float]           # Дистанция в метрах
    is_active: bool                     # Активная цель?
    center: Tuple[int, int]             # Координаты центра (x, y)
    bounds: Tuple[int, int, int, int]   # (x, y, width, height)
    
    # Здоровье цели (0.0-1.0)
    shield: Optional[float]             # 1.0 = 100%
    armor: Optional[float]              # 0.5 = 50%
    hull: Optional[float]               # 0.1 = 10%
```

**Примеры:**
```python
# Получить все цели
for target in state.targets:
    print(f"{target.name}: S:{target.shield:.0%} A:{target.armor:.0%} H:{target.hull:.0%}")

# Найти активную цель
active = next((t for t in state.targets if t.is_active), None)
if active and active.hull < 0.1:
    print("Цель почти убита!")

# Кликнуть по цели
mouse.click(target.center[0], target.center[1])
```

---

### ShipState (состояние корабля)

```python
@dataclass
class ShipState:
    modules: List[Module]    # Модули корабля
    
    # Здоровье (0.0-1.0)
    shield: float            # 1.0 = 100%
    armor: float             # 1.0 = 100%
    hull: float              # 1.0 = 100%
    
    # Ресурсы
    capacitor: float         # 0.0-1.0 (0% - 100%)
    speed: float             # м/с
```

**Примеры:**
```python
# Проверить здоровье
if state.ship.shield < 0.3:
    print("Щиты низкие! Убегаем!")
    warp_out()

# Проверить энергию
if state.ship.capacitor < 0.2:
    print("Энергия низкая!")
    disable_modules()

# Проверить скорость
if state.ship.speed < 10:
    print("Корабль стоит")
```

---

### Module (модуль корабля)

```python
@dataclass
class Module:
    slot_type: str              # 'high', 'mid', 'low'
    slot_name: str              # 'inFlightHighSlot1'
    is_active: bool             # Модуль активен?
    ammo_count: Optional[int]   # Количество боеприпасов (не реализовано)
    center: Tuple[int, int]     # Координаты для клика
```

**Примеры:**
```python
# Включить все пушки (high slots)
for module in state.ship.modules:
    if module.slot_type == 'high' and not module.is_active:
        mouse.click(module.center[0], module.center[1])
        time.sleep(0.1)

# Выключить все активные модули
for module in state.ship.modules:
    if module.is_active:
        mouse.click(module.center[0], module.center[1])

# Подсчитать активные модули
active_count = sum(1 for m in state.ship.modules if m.is_active)
print(f"Активных модулей: {active_count}")
```

---

### OverviewEntry (запись в overview)

```python
@dataclass
class OverviewEntry:
    index: int                          # Индекс в списке (0, 1, 2...)
    name: Optional[str]                 # "Hornet* [GAM B]"
    type: Optional[str]                 # "Destroyer"
    distance: Optional[str]             # "1 189 м" или "188 км"
    center: Tuple[int, int]             # Координаты для клика
    bounds: Tuple[int, int, int, int]   # (x, y, width, height)
```

**Примеры:**
```python
# Залочить первые 3 цели из overview
for entry in state.overview[:3]:
    mouse.click(entry.center[0], entry.center[1])
    time.sleep(0.5)

# Найти ближайшую цель
closest = min(state.overview, key=lambda e: parse_distance(e.distance))
print(f"Ближайшая: {closest.name} на {closest.distance}")

# Подсчитать врагов
enemy_count = len([e for e in state.overview if e.type == "Destroyer"])
```

---

### SelectedAction (доступное действие)

```python
@dataclass
class SelectedAction:
    name: str                   # 'approach', 'warp_to', 'orbit', etc.
    center: Tuple[int, int]     # АБСОЛЮТНЫЕ координаты кнопки
    texture_path: Optional[str] # Путь к текстуре (опционально)
```

**Доступные действия:**
- `approach` - Приблизиться
- `warp_to` - Варп к объекту
- `orbit` - Орбита
- `keep_at_range` - Держать дистанцию
- `un_lock_target` - Разлочить цель
- `look_at` - Посмотреть на объект
- `set_interest` - Установить интерес
- `show_info` - Показать информацию
- `scoop_to_drone_bay` - Подобрать в дрон-бей

**Примеры:**
```python
# Варп при низких щитах
if state.ship.shield < 0.3:
    warp_action = next((a for a in state.selected_actions if a.name == 'warp_to'), None)
    if warp_action:
        mouse.click(warp_action.center[0], warp_action.center[1])

# Орбита вокруг цели
orbit_action = next((a for a in state.selected_actions if a.name == 'orbit'), None)
if orbit_action:
    mouse.click(orbit_action.center[0], orbit_action.center[1])
```

---

### OverviewTab (вкладка overview)

```python
@dataclass
class OverviewTab:
    name: str                   # 'OverviewTab_<color>✈ Jump</color>'
    label: str                  # '✈ Jump' (без HTML тегов)
    center: Tuple[int, int]     # АБСОЛЮТНЫЕ координаты для клика
```

**Примеры:**
```python
# Переключить на вкладку "PvP Foe"
pvp_tab = next((t for t in state.overview_tabs if 'PvP Foe' in t.label), None)
if pvp_tab:
    mouse.click(pvp_tab.center[0], pvp_tab.center[1])

# Переключить на вкладку "Jump"
jump_tab = next((t for t in state.overview_tabs if 'Jump' in t.label), None)
if jump_tab:
    mouse.click(jump_tab.center[0], jump_tab.center[1])

# Вывести все вкладки
for tab in state.overview_tabs:
    print(f"{tab.label} @ ({tab.center[0]}, {tab.center[1]})")
```

---

### NeocomButton (кнопка боковой панели)

```python
@dataclass
class NeocomButton:
    button_type: str            # 'cargo', 'inventory', 'tactical', etc.
    center: Tuple[int, int]     # АБСОЛЮТНЫЕ координаты для клика
```

**Доступные кнопки:**
- `cargo` - Открыть карго
- `inventory` - Открыть инвентарь
- `tactical` - Тактический оверлей
- `scanner` - Сканер
- `autopilot` - Автопилот
- `camera_tactical` - Тактическая камера
- `camera_orbit` - Орбитальная камера
- `camera_pov` - POV камера

**Примеры:**
```python
# Открыть карго
cargo_btn = next((b for b in state.neocom_buttons if b.button_type == 'cargo'), None)
if cargo_btn:
    mouse.click(cargo_btn.center[0], cargo_btn.center[1])

# Открыть инвентарь
inv_btn = next((b for b in state.neocom_buttons if b.button_type == 'inventory'), None)
if inv_btn:
    mouse.click(inv_btn.center[0], inv_btn.center[1])

# Включить тактический оверлей
tactical_btn = next((b for b in state.neocom_buttons if b.button_type == 'tactical'), None)
if tactical_btn:
    mouse.click(tactical_btn.center[0], tactical_btn.center[1])
```

---

## 🔌 API СЕРВИСА

### Основные методы

#### `start() -> bool`
Запустить сервис (автоматически находит EVE, root address, запускает фоновый поток).

```python
service = SanderlingService()
if service.start():
    print("Сервис запущен")
else:
    print("Ошибка запуска")
```

**Что происходит:**
1. Поиск процесса EVE (exefile.exe)
2. Поиск root address (может занять до 3 минут)
3. Запуск фонового потока чтения памяти

---

#### `stop() -> None`
Остановить сервис.

```python
service.stop()
```

---

#### `get_state() -> Optional[GameState]`
Получить текущий снимок игры (thread-safe).

```python
state = service.get_state()
if state:
    print(f"Targets: {len(state.targets)}")
```

**Важно:** Возвращает полный снимок игры в один момент времени.

---

### Properties (shortcuts)

Удобные shortcuts для быстрого доступа к данным:

```python
# Вместо state.targets
targets = service.targets  # List[Target]

# Вместо len(state.targets)
count = service.targets_count  # int

# Вместо state.overview
overview = service.overview  # List[OverviewEntry]

# Вместо len(state.overview)
count = service.overview_count  # int

# Вместо state.ship.modules
modules = service.modules  # List[Module]

# Количество активных модулей
active = service.active_modules_count  # int

# Статистика
reads = service.read_count  # Успешных чтений
errors = service.error_count  # Ошибок
time_ms = service.last_read_time_ms  # Время последнего чтения
```

---

## 💡 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ

### Пример 1: Базовый бот для аномалий

```python
from core.sanderling import SanderlingService
import time

class AnomalyBot:
    def __init__(self):
        self.sanderling = SanderlingService()
        self.sanderling.start()
    
    def run(self):
        while True:
            state = self.sanderling.get_state()
            
            # Проверить здоровье
            if state.ship.shield < 0.3:
                self.warp_out(state)
                break
            
            # Проверить энергию
            if state.ship.capacitor < 0.2:
                self.manage_capacitor(state)
            
            # Боевая логика
            if len(state.targets) == 0:
                self.lock_targets(state)
            else:
                self.shoot_targets(state)
            
            time.sleep(0.5)
    
    def warp_out(self, state):
        """Убежать при низких щитах."""
        warp = next((a for a in state.selected_actions if a.name == 'warp_to'), None)
        if warp:
            mouse.click(warp.center[0], warp.center[1])
            print("Варп!")
    
    def lock_targets(self, state):
        """Залочить цели из overview."""
        for entry in state.overview[:3]:
            mouse.click(entry.center[0], entry.center[1])
            time.sleep(0.5)
    
    def shoot_targets(self, state):
        """Стрелять по целям."""
        # Найти активную цель
        active = next((t for t in state.targets if t.is_active), None)
        if not active:
            return
        
        # Если цель почти убита, переключиться
        if active.hull and active.hull < 0.1:
            self.switch_target(state)
            return
        
        # Включить пушки
        for module in state.ship.modules:
            if module.slot_type == 'high' and not module.is_active:
                mouse.click(module.center[0], module.center[1])
    
    def manage_capacitor(self, state):
        """Управление энергией."""
        # Выключить mid/low слоты при низкой энергии
        for module in state.ship.modules:
            if module.slot_type in ['mid', 'low'] and module.is_active:
                mouse.click(module.center[0], module.center[1])
```

---

### Пример 2: Мониторинг здоровья

```python
def monitor_health(service):
    """Постоянный мониторинг здоровья корабля."""
    while True:
        state = service.get_state()
        
        # Проверить щиты
        if state.ship.shield < 0.5:
            print(f"⚠️ Щиты: {state.ship.shield:.0%}")
        
        # Проверить броню
        if state.ship.armor < 1.0:
            print(f"🔴 Броня повреждена: {state.ship.armor:.0%}")
        
        # Проверить структуру
        if state.ship.hull < 1.0:
            print(f"💀 СТРУКТУРА ПОВРЕЖДЕНА: {state.ship.hull:.0%}")
            break
        
        time.sleep(1)
```

---

### Пример 3: Автоматическое переключение целей

```python
def auto_target_switching(service):
    """Автоматически переключаться на следующую цель."""
    while True:
        state = service.get_state()
        
        # Найти активную цель
        active = next((t for t in state.targets if t.is_active), None)
        
        if active:
            # Если цель почти убита (hull < 10%)
            if active.hull and active.hull < 0.1:
                print(f"Цель {active.name} почти убита, переключаемся...")
                
                # Найти следующую цель с максимальным здоровьем
                next_target = max(
                    [t for t in state.targets if not t.is_active],
                    key=lambda t: (t.hull or 0),
                    default=None
                )
                
                if next_target:
                    mouse.click(next_target.center[0], next_target.center[1])
        
        time.sleep(0.5)
```

---

### Пример 4: Управление модулями

```python
def manage_modules(service):
    """Умное управление модулями."""
    state = service.get_state()
    
    # Включить все пушки
    guns = [m for m in state.ship.modules if m.slot_type == 'high']
    for gun in guns:
        if not gun.is_active:
            mouse.click(gun.center[0], gun.center[1])
            time.sleep(0.1)
    
    # Включить щит-бустер если щиты низкие
    if state.ship.shield < 0.5:
        shield_boosters = [m for m in state.ship.modules 
                          if m.slot_type == 'mid' and 'shield' in m.slot_name.lower()]
        for booster in shield_boosters:
            if not booster.is_active:
                mouse.click(booster.center[0], booster.center[1])
    
    # Выключить все если энергия низкая
    if state.ship.capacitor < 0.2:
        for module in state.ship.modules:
            if module.is_active and module.slot_type != 'high':
                mouse.click(module.center[0], module.center[1])
```

---

### Пример 5: Работа с overview

```python
def work_with_overview(service):
    """Работа с overview."""
    state = service.get_state()
    
    # Переключить на вкладку "PvP Foe"
    pvp_tab = next((t for t in state.overview_tabs if 'PvP Foe' in t.label), None)
    if pvp_tab:
        mouse.click(pvp_tab.center[0], pvp_tab.center[1])
        time.sleep(0.5)
    
    # Залочить все цели типа "Destroyer"
    destroyers = [e for e in state.overview if e.type == 'Destroyer']
    for destroyer in destroyers[:3]:  # Максимум 3
        mouse.click(destroyer.center[0], destroyer.center[1])
        time.sleep(0.5)
    
    # Найти ближайшую цель
    def parse_distance(dist_str):
        if not dist_str:
            return float('inf')
        if 'км' in dist_str:
            return float(dist_str.split()[0].replace(' ', '')) * 1000
        return float(dist_str.split()[0].replace(' ', ''))
    
    closest = min(state.overview, key=lambda e: parse_distance(e.distance))
    print(f"Ближайшая цель: {closest.name} на {closest.distance}")
```

---

## ⚡ ОПТИМИЗАЦИЯ (RAMDisk)

### Проблема износа диска

Sanderling сохраняет JSON на диск каждую секунду:
- 10 часов = 36,000 записей
- ~18 GB за 10 часов
- ~15.5 TB в год (если 24/7)

**Реальный износ SSD:**
- SSD на 300 TBW проживет **19 лет**
- SSD на 600 TBW проживет **38 лет**
- **Вывод: износ минимальный, можно не париться**

### Решение: RAMDisk

RAMDisk = виртуальный диск в оперативной памяти.

**Преимущества:**
- ✅ Нет износа SSD вообще
- ✅ Быстрее (RAM быстрее диска в 20 раз)
- ✅ Автоматическая очистка при перезагрузке

**Требования:**
- 8+ GB оперативной памяти
- 100 MB для RAMDisk

### Установка RAMDisk (Windows)

**Вариант 1: ImDisk Toolkit (рекомендуется)**
1. Скачать: https://sourceforge.net/projects/imdisk-toolkit/
2. Установить
3. Запустить "RamDisk Configuration"
4. Настройки:
   - Size: 100 MB
   - Drive letter: R:
   - File system: NTFS
   - Mount at boot: ✅
5. OK

**Код автоматически использует RAMDisk:**
```python
# В service.py уже реализовано:
if Path("R:/").exists():
    temp_dir = Path("R:/temp")  # RAMDisk
else:
    temp_dir = Path("temp")     # Обычный диск
```

**Никаких изменений в коде не требуется!**

---

## 🔧 TROUBLESHOOTING

### Сервис не запускается

**Проблема:** `service.start()` возвращает `False`

**Решения:**
1. Проверить что EVE Online запущен (exefile.exe)
2. Проверить путь к Sanderling в `resources/config/sanderling.json`
3. Проверить логи: `logging.basicConfig(level=logging.DEBUG)`

---

### Root address не найден

**Проблема:** "Failed to find root address"

**Решения:**
1. Подождать 3 минуты (первый поиск долгий)
2. Перезапустить EVE Online
3. Удалить кэш: `data/sanderling_cache.json`

---

### Данные не обновляются

**Проблема:** `state.timestamp` не меняется

**Решения:**
1. Проверить что фоновый поток работает: `service.is_running`
2. Проверить ошибки: `service.error_count`
3. Проверить логи

---

### Координаты неправильные

**Проблема:** Клики мимо кнопок

**Причины:**
- Разрешение экрана изменилось
- UI масштаб в EVE изменился
- Окно EVE не в фокусе

**Решение:**
- Координаты всегда абсолютные
- Проверить что окно EVE активно
- Проверить масштаб UI в настройках EVE

---

### Высокое использование CPU

**Проблема:** Sanderling грузит CPU

**Решения:**
1. Увеличить интервал чтения:
```python
config = SanderlingConfig.load()
config.read_interval_ms = 2000  # 2 секунды вместо 1
service = SanderlingService(config)
```

2. Использовать RAMDisk (быстрее чтение/запись)

---

### Память растет

**Проблема:** Python процесс занимает много памяти

**Причина:** Кэширование UI tree

**Решение:**
- Нормально, память стабилизируется на ~100-200 MB
- Если больше 500 MB - перезапустить сервис

---

## 📊 ПРОИЗВОДИТЕЛЬНОСТЬ

### Типичные показатели

```
Reads: 3600 (за час)
Success rate: 99.5%
Read time: 50-150ms
Memory: 100-200 MB
CPU: 5-10%
Disk writes: 1.8 GB/час (без RAMDisk)
```

### Оптимизация

**Для долгой работы (10+ часов):**
- ✅ Используй RAMDisk
- ✅ Интервал 1-2 секунды
- ✅ Мониторинг ошибок

**Для коротких сессий (1-2 часа):**
- ✅ Обычный диск (temp/)
- ✅ Интервал 1 секунда
- ✅ Без оптимизаций

---

## 📝 ВАЖНЫЕ ЗАМЕЧАНИЯ

### Thread Safety
- `get_state()` всегда thread-safe
- Используй `with self._state_lock:` если модифицируешь код
- Не храни ссылки на state - копируй данные

### Координаты
- Все координаты **АБСОЛЮТНЫЕ** (не относительные)
- `center` = центр элемента (готово для клика)
- `bounds` = (x, y, width, height)

### Здоровье
- Все значения в диапазоне **0.0-1.0**
- 1.0 = 100%, 0.5 = 50%, 0.0 = 0%
- `None` = данные недоступны

### Дистанции
- `Target.distance` в **метрах** (float)
- `OverviewEntry.distance` в **строке** ("1 189 м")
- Конвертируй строку в float если нужно

### Модули
- `slot_type`: 'high', 'mid', 'low'
- `is_active`: True = модуль включен
- `ammo_count`: не реализовано (всегда None)

---

## 🎯 ГОТОВ К РАЗРАБОТКЕ БОТА!

Теперь у тебя есть:
- ✅ Полный доступ к данным игры
- ✅ Thread-safe API
- ✅ Готовые координаты для кликов
- ✅ Примеры использования
- ✅ Оптимизация (RAMDisk)

**Следующий шаг: разработка логики бота!**

---

## 📚 ДОПОЛНИТЕЛЬНЫЕ ФАЙЛЫ

- `core/sanderling/service.py` - Основной сервис
- `core/sanderling/parser.py` - Парсер UI tree
- `core/sanderling/models.py` - Модели данных
- `core/sanderling/config.py` - Конфигурация
- `scripts/test_sanderling.py` - Тестовый скрипт
