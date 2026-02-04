# Sanderling Memory Reading Module

Модуль для чтения памяти EVE Online через Sanderling.

## Компоненты

- **service.py** - Фоновый сервис для автоматического чтения памяти
- **parser.py** - Парсер UI tree для извлечения данных
- **models.py** - Модели данных (GameState, Target, OverviewEntry, etc.)
- **cache.py** - Кэширование root address для быстрого запуска
- **config.py** - Управление конфигурацией

## Использование

```python
from core.sanderling.service import SanderlingService
from core.sanderling.config import SanderlingConfig

# Загрузить конфигурацию
config = SanderlingConfig.load()

# Создать и запустить сервис
service = SanderlingService(config)
service.start()

# Получить состояние игры
state = service.get_state()
if state:
    print(f"Targets: {len(state.targets)}")
    print(f"Overview entries: {len(state.overview)}")

# Остановить сервис
service.stop()
```

## Конфигурация

Файл `resources/config/sanderling.json`:

```json
{
  "enabled": true,
  "fallback_to_cv": true,
  "cache_enabled": true,
  "read_interval_ms": 200,
  "max_retries": 3,
  "timeout_ms": 5000,
  "binary_path": "external/sanderling-bin/read-memory-64-bit.exe",
  "debug_mode": false
}
```

## Кэширование

Root address кэшируется в `output/data/sanderling_cache.json` для быстрого запуска (без 20-секундного поиска).

Кэш автоматически инвалидируется при:
- Перезапуске процесса EVE
- Ошибках чтения памяти
- Устаревании (>24 часов)

## Обработка ошибок

Сервис автоматически:
- Повторяет попытки чтения при ошибках (до 3 раз)
- Инвалидирует кэш и выполняет полный поиск при неудаче
- Переключается на CV fallback при длительной недоступности (>30 сек)
- Логирует все события и ошибки

## Логирование

Логи сохраняются в `output/logs/sanderling_YYYYMMDD_HHMMSS.log`

В debug режиме снимки UI tree сохраняются в `output/debug/`
