# Shared Utilities

Общие утилиты для всех ботов.

## Базовые модули

- **actions.py** - Высокоуровневые действия (click_on_image, wait_and_click, etc.)
- **screen.py** - Работа со скриншотами
- **window.py** - Управление окнами
- **vision.py** - Базовые CV операции (find_image, wait_image, etc.)

## EVE-специфичные модули (shared/eve/)

- **overview.py** - Работа с Overview (подсчет целей, лок, убийство)
- **overview_hybrid.py** - Гибридный Overview (Sanderling + CV fallback)
- **hud.py** - Работа с HUD (проверка пушек, статусов)
- **navigation.py** - Навигация (варп, джамп, док)
- **combat.py** - Боевые действия
- **telegram_notifier.py** - Уведомления в Telegram

## Использование

```python
# Базовые действия
from shared.actions import click_on_image, wait_and_click

click_on_image("button.png")
wait_and_click("loading_complete.png", timeout=30)

# Работа с Overview
from shared.eve.overview import count_targets, lock_and_kill

targets = count_targets()
if targets > 0:
    killed = lock_and_kill()
    print(f"Killed {killed} targets")

# Гибридный режим (Sanderling + CV)
from shared.eve.overview_hybrid import OverviewManager
from core.sanderling.service import SanderlingService

service = SanderlingService()
service.start()

manager = OverviewManager(service)
targets = manager.count_targets()  # Использует Sanderling, fallback на CV
```

## Хуманизация

Все действия мыши и клавиатуры используют хуманизацию по умолчанию:
- Случайные задержки
- Плавное движение курсора
- Вариация скорости

Это делает действия бота более похожими на действия человека.
