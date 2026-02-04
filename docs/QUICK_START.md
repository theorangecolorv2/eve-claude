# Sanderling - Быстрый старт

## 🚀 За 30 секунд

```python
from core.sanderling import SanderlingService

# Запустить
service = SanderlingService()
service.start()  # Автоматически найдет EVE и root address

# Получить данные
state = service.get_state()
print(f"Щиты: {state.ship.shield:.0%}")
print(f"Целей: {len(state.targets)}")

# Остановить
service.stop()
```

## 📖 Полная документация

См. **[docs/SANDERLING.md](SANDERLING.md)** - полное руководство с примерами.

## 🎯 Основные возможности

### Данные корабля
```python
state.ship.shield      # 0.0-1.0 (щиты)
state.ship.armor       # 0.0-1.0 (броня)
state.ship.hull        # 0.0-1.0 (структура)
state.ship.capacitor   # 0.0-1.0 (энергия)
state.ship.speed       # м/с
```

### Цели
```python
for target in state.targets:
    print(f"{target.name}")
    print(f"  Активная: {target.is_active}")
    print(f"  Здоровье: S:{target.shield:.0%} A:{target.armor:.0%} H:{target.hull:.0%}")
    print(f"  Координаты: {target.center}")
```

### Модули
```python
for module in state.ship.modules:
    if module.slot_type == 'high' and not module.is_active:
        mouse.click(module.center[0], module.center[1])
```

### Действия
```python
# Варп при низких щитах
if state.ship.shield < 0.3:
    warp = next((a for a in state.selected_actions if a.name == 'warp_to'), None)
    if warp:
        mouse.click(warp.center[0], warp.center[1])
```

## 🔧 Тестирование

```bash
python scripts/test_sanderling.py
```

## 📚 Что дальше?

1. Прочитай **[docs/SANDERLING.md](SANDERLING.md)** - полная документация
2. Посмотри примеры в разделе "Примеры использования"
3. Начни разработку своего бота!
