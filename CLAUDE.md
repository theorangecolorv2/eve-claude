# CLAUDE.md — Инструкция для Claude Code агентов

> Прочитай этот документ ПОЛНОСТЬЮ перед началом работы.

## О проекте

Исследовательский проект по созданию бота для EVE Online.
Цель — помочь CCP Games улучшить анти-бот защиту через демонстрацию реальных техник.

**Разрешено**: работа ТОЛЬКО на тестовом сервере (Singularity/Duality), разрешение от CCP Alpha.
**Запрещено**: подключение к live серверу (Tranquility), изменение настроек подключения.

## Структура проекта

```
eve-claude/
├── CLAUDE.md               # Инструкция для агентов (этот файл)
├── README.md               # Обзор проекта
├── HUMANIZATION.md         # Хуманизация (Bezier, delays)
├── CHANGELOG.md            # История изменений
├── config.py               # Конфигурация (константы, ключи, пороги)
│
├── bots/
│   └── abyss_farmer/       # ★ ОСНОВНОЙ БОТ
│       ├── main.py          # AbyssFarmer — главный цикл
│       ├── enter.py         # Вход в абисс (инвентарь, филамент)
│       ├── room_new.py      # Зачистка комнаты (default_room)
│       ├── room_detector.py # Определение типа комнаты
│       ├── room_knight.py   # Обработчик Knight
│       ├── room_tessera.py  # Обработчик Tessera
│       ├── room_vila.py     # Обработчик Vila
│       ├── room_overmind.py # Обработчик Overmind
│       └── cache.py         # Контейнеры (аппроч, лут)
│
├── core/
│   └── sanderling/          # ★ ЧТЕНИЕ ПАМЯТИ (основной модуль)
│       ├── service.py       # SanderlingService — фоновый сервис
│       ├── parser.py        # UITreeParser — парсер UI tree
│       ├── models.py        # Модели данных (GameState, Target, etc.)
│       ├── cache.py         # Кэширование root address
│       └── config.py        # Конфигурация Sanderling
│
├── eve/                     # Модули автоматизации
│   ├── mouse.py             # Мышь с хуманизацией (Bezier curves)
│   ├── keyboard.py          # Клавиатура
│   ├── screen.py            # Скриншоты
│   ├── vision.py            # Template matching (OpenCV)
│   ├── window.py            # Управление окнами
│   ├── actions.py           # Высокоуровневые действия
│   ├── overview.py          # Overview (CV-режим)
│   ├── inventory.py         # Инвентарь
│   ├── bookmarks.py         # Букмарки
│   ├── modules.py           # Модули корабля
│   ├── combat.py            # Дроны
│   ├── hud.py               # HUD
│   ├── navigation.py        # Навигация
│   └── abyss.py             # Абисс-функции
│
├── external/
│   ├── Sanderling/          # Исходники C# (read-memory-64-bit)
│   └── sanderling-bin/      # Скомпилированный .exe
│
├── scripts/                 # Точки входа и тесты
│   ├── run_abyss_farmer.py  # ★ ЗАПУСК БОТА
│   ├── telegram_bot.py      # Telegram бот
│   ├── test_sanderling.py   # Мониторинг Sanderling
│   └── test_*.py            # Тесты отдельных модулей
│
├── docs/                    # Документация модулей
│   ├── SANDERLING.md        # Полная документация Sanderling API
│   ├── INVENTORY.md         # Модуль инвентаря
│   ├── BOOKMARKS.md         # Модуль букмарок
│   ├── DRONES.md            # Модуль дронов
│   └── QUICK_START.md       # Быстрый старт Sanderling
│
├── resources/
│   ├── assets/              # Изображения для CV (template matching)
│   └── config/              # sanderling.json
│
├── output/                  # Логи, данные, временные файлы
│
│ # DEPRECATED (не используется активным ботом):
├── shared/                  # Legacy CV-модули
├── bots/anomaly_farmer/     # Старый CV-бот
└── eve/sanderling/          # Упрощённая копия core/sanderling (не используется)
```

## Как работает бот

Бот использует **Sanderling** для чтения UI tree из памяти EVE Online:
- `core/sanderling/service.py` запускает `read-memory-64-bit.exe` как subprocess
- Результат (JSON) парсится в `parser.py` → структурированные модели в `models.py`
- Бот (`bots/abyss_farmer/`) получает состояние игры через `service.get_state()`
- Для кликов и ввода используются модули `eve/mouse.py`, `eve/keyboard.py` с хуманизацией

### Ключевые импорты в коде бота

```python
from core.sanderling.service import SanderlingService
from core.sanderling.models import OverviewEntry, GameState
from eve.mouse import click, random_delay
from eve.keyboard import press_key
from eve.bookmarks import right_click_bookmark
from eve.inventory import InventoryManager
from eve.modules import activate_module
```

## Требования к коду

### Обязательно:
- Логирование через `logging` (logger.info/debug/error)
- Обработка ошибок (try/except с логами)
- Хуманизация (используй `eve/mouse.py`, не pyautogui напрямую)
- Комментарии на русском

### Запрещено:
- Прямые вызовы `pyautogui` (используй `eve/mouse.py`)
- Изменение настроек подключения к серверам
- Подключение к Tranquility

### Шаблон нового модуля

```python
"""Описание модуля."""

import logging
from core.sanderling.service import SanderlingService
from eve.mouse import click, random_delay

logger = logging.getLogger(__name__)


def my_function(sanderling: SanderlingService) -> bool:
    """Описание функции."""
    logger.info("Начало действия...")

    state = sanderling.get_state()
    if not state:
        logger.error("Нет данных от Sanderling")
        return False

    # Логика...

    random_delay(0.3, 0.7)
    logger.info("Действие завершено")
    return True
```

## Документация

**Правила:**
- Один модуль = один MD файл в `docs/`
- Обновляй существующие файлы, НЕ создавай новые
- Не создавай CHANGELOG для каждой фичи — используй git commits
- README.md в корне — общий обзор проекта

**Структура:**
| Файл | Назначение |
|------|-----------|
| `README.md` | Обзор проекта |
| `CLAUDE.md` | Инструкции для агентов |
| `HUMANIZATION.md` | Хуманизация бота |
| `CHANGELOG.md` | История изменений |
| `docs/SANDERLING.md` | API Sanderling |
| `docs/INVENTORY.md` | Модуль инвентаря |
| `docs/BOOKMARKS.md` | Модуль букмарок |
| `docs/DRONES.md` | Модуль дронов |
| `bots/abyss_farmer/README.md` | Документация бота |

## Безопасность

- Никогда не изменяй настройки подключения к серверам
- Никогда не подключайся к Tranquility
- Весь код публичный — пиши так, будто его читают разработчики CCP
