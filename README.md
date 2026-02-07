# EVE Online Bot Research Project

Исследовательский проект по автоматизации EVE Online для улучшения анти-бот системы.

## Легальность

- Работа ТОЛЬКО на тестовом сервере (Singularity/Duality)
- Одобрено CCP Alpha (сотрудник CCP Games)
- Open source — весь код публичен для анализа
- Цель: помочь CCP улучшить защиту от ботов

## Текущий бот: Abyss Farmer

Автоматический фарм абисса (Бездны) через Sanderling (чтение памяти).

**Запуск:**
```bash
python scripts/run_abyss_farmer.py
```

**Подробнее:** [bots/abyss_farmer/README.md](bots/abyss_farmer/README.md)

## Архитектура

```
┌─────────────────────┐     JSON      ┌──────────────────┐
│  EVE Online Process │ ───────────→  │  core/sanderling/ │
│  (UI Tree в памяти) │ read-memory   │  (Python парсер)  │
└─────────────────────┘  -64-bit.exe  └────────┬─────────┘
                                               │ GameState
                                    ┌──────────▼──────────┐
                                    │  bots/abyss_farmer/ │
                                    │  (логика бота)      │
                                    └──────────┬──────────┘
                                               │ click/keypress
                                    ┌──────────▼──────────┐
                                    │  eve/mouse.py       │
                                    │  eve/keyboard.py    │
                                    │  (хуманизация)      │
                                    └─────────────────────┘
```

### Ключевые модули

| Модуль | Назначение |
|--------|-----------|
| `core/sanderling/` | Чтение UI tree из памяти EVE Online |
| `bots/abyss_farmer/` | Основной бот (варп → вход → зачистка → выход) |
| `eve/mouse.py` | Мышь с хуманизацией (Bezier curves) |
| `eve/keyboard.py` | Клавиатура |
| `eve/inventory.py` | Управление инвентарём |
| `eve/bookmarks.py` | Работа с букмарками |
| `config.py` | Все константы и настройки |

## Технологии

- **Python 3.8+**
- **Sanderling** (C#) — чтение памяти EVE Online
- **OpenCV** — template matching (fallback)
- **PyAutoGUI** — эмуляция ввода (через обёртку с хуманизацией)

## Документация

| Документ | Описание |
|----------|---------|
| [CLAUDE.md](CLAUDE.md) | Инструкции для Claude Code агентов |
| [HUMANIZATION.md](HUMANIZATION.md) | Хуманизация бота |
| [docs/SANDERLING.md](docs/SANDERLING.md) | API Sanderling |
| [docs/INVENTORY.md](docs/INVENTORY.md) | Модуль инвентаря |
| [docs/BOOKMARKS.md](docs/BOOKMARKS.md) | Модуль букмарок |
| [docs/DRONES.md](docs/DRONES.md) | Модуль дронов |

## Для Claude Code агентов

Прочитайте [CLAUDE.md](CLAUDE.md) — там всё, что нужно знать о проекте, структуре и требованиях к коду.
