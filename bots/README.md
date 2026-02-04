# EVE Online Bots

Готовые боты для автоматизации в EVE Online.

## Доступные боты

### Anomaly Farmer (bots/anomaly_farmer/)
Бот для фарма аномалий (убежища/укрытия).

Функции:
- Автоматический поиск аномалий
- Варп к аномалии
- Зачистка всех целей
- Лут и возврат на станцию

### Abyss Farmer (bots/abyss_farmer/)
Бот для фарма абиссов (в разработке).

## Запуск бота

```bash
# Anomaly Farmer
python bots/anomaly_farmer/main.py

# Abyss Farmer
python bots/abyss_farmer/main.py
```

## Конфигурация

Каждый бот имеет свой файл конфигурации `config.json`:

```json
{
  "bot_name": "Anomaly Farmer",
  "check_interval": 1.0,
  "use_sanderling": true,
  "use_telegram": false
}
```

## Создание своего бота

1. Создайте папку в `bots/your_bot_name/`
2. Создайте `main.py` с основной логикой
3. Создайте `config.json` с настройками
4. Используйте модули из `shared/` и `core/`

Пример структуры:

```python
from shared.eve.overview import count_targets, lock_and_kill
from shared.eve.navigation import warp_to
from core.sanderling.service import SanderlingService

def main():
    # Ваша логика бота
    service = SanderlingService()
    service.start()
    
    # ... логика бота ...
    
    service.stop()

if __name__ == "__main__":
    main()
```

## Безопасность

- Всегда тестируйте бота в безопасной среде
- Используйте хуманизацию для снижения риска детекта
- Не оставляйте бота без присмотра надолго
- Следите за логами и уведомлениями
