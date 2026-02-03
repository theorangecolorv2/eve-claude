# Telegram Bot - Инструкция

## 📱 О боте

Telegram бот для уведомлений о работе фарм-бота EVE Online.

**Токен:** `8348805684:AAH8P4STd4-TP6nzGa-C5X7Z6_hjlFk9OAk`

---

## 🚀 Установка

### 1. Установить зависимости

```bash
pip install python-telegram-bot
```

Или установить все зависимости:

```bash
pip install -r requirements.txt
```

---

## 🎮 Запуск

### Запустить фарм-бота (всё в одном!)

```bash
python scripts/eve_farm_bot.py
```

**Telegram бот запустится автоматически в фоне!**

- Фарм бот стартует и начинает работу
- Telegram бот запускается в отдельном потоке
- Оба работают параллельно
- Остановка Ctrl+C останавливает оба бота

---

## 📢 Как использовать

### Подписаться на уведомления

1. Найти бота в Telegram по токену (попросите @BotFather показать бота)
2. Отправить боту команду `/start` или любое сообщение
3. Готово! Вы подписаны на уведомления

### Команды бота

- `/start` - Подписаться + получить текущую статистику
- `/stats` - Получить текущую статистику бота
- `/users` - Количество подписчиков
- Любое сообщение - Подписаться на уведомления

---

## 🎉 Уведомления

### 1. Экспедиция найдена

Когда бот находит экспедицию, всем подписчикам приходит:

```
🎉 ЭКСПЕДИЦИЯ!

⏰ Время: 14:32:15
📦 Всего найдено: 3
```

### 2. Ошибка бота

Когда бот падает с ошибкой, всем подписчикам приходит:

```
❌ ОШИБКА БОТА

⏰ Время: 14:32:15

KeyError: 'some_key'
```

+ **Скриншот экрана** в момент ошибки

### 3. Статистика бота

По команде `/start` или `/stats`:

```
📊 СТАТИСТИКА БОТА

⏱ Время работы: 2ч 15м 30с
🌟 Систем посещено: 45
💥 Аномалий зачищено: 89
🎉 Экспедиций найдено: 3
🚀 Прыжков сделано: 44

Метрики:
📈 Аномалий/час: 39.5
🎲 Шанс экспедиции: 3.4%
```

---

## 📁 Файлы данных

Бот создает папку `data/` для хранения:

- `telegram_users.json` - Список chat_id подписчиков
- `bot_stats.json` - Текущая статистика фарм-бота

**ВАЖНО:** Не удаляйте эти файлы - в них хранятся подписчики!

---

## 🔧 Как это работает

### Архитектура

```
python scripts/eve_farm_bot.py
         │
         ├─> Главный поток (Main Thread)
         │   └─> Фарм бот (фармит аномалии)
         │
         └─> Фоновый поток (Background Thread)
             └─> Telegram бот (обрабатывает команды)

Оба потока используют:
         ↓
┌─────────────────────┐
│  data/              │
│  ├─ users.json      │ ← Список подписчиков
│  └─ bot_stats.json  │ ← Статистика
└─────────────────────┘
         ↑
┌─────────────────────┐
│  Telegram Notifier  │ ← Функции для отправки
│  (eve/              │   уведомлений
│   telegram_notifier │
│   .py)              │
└─────────────────────┘
```

**Telegram бот запускается автоматически!**

- Не нужно запускать `scripts/telegram_bot.py` отдельно
- Всё работает из одной команды
- При остановке фарм бота (Ctrl+C) Telegram бот тоже останавливается

### Интеграция в фарм-бот

**1. Уведомление об экспедиции**

В `check_and_close_expedition_popup()`:

```python
if stats:
    stats.expeditions_found += 1
    notify_expedition(stats.expeditions_found)  # ← Уведомление
```

**2. Уведомление об ошибке**

В `except Exception as e`:

```python
except Exception as e:
    logger.exception(f"Критическая ошибка: {e}")
    notify_error(str(e), send_screenshot=True)  # ← Уведомление + скриншот
```

**3. Сохранение статистики**

В `BotStats.log_stats()`:

```python
def log_stats(self, logger):
    # ... вывод в лог ...
    self.save_to_file()  # ← Сохранение в data/bot_stats.json
```

---

## ⚙️ Настройки

### Изменить токен бота

В `eve/telegram_notifier.py`:

```python
BOT_TOKEN = "ВАШ_ТОКЕН_ЗДЕСЬ"
```

### Отключить уведомления

Закомментировать вызовы в `eve_farm_bot.py`:

```python
# notify_expedition(stats.expeditions_found)  # Отключено
```

---

## 🐛 Отладка

### Логи Telegram бота

Смотреть в консоль, где запущен `telegram_bot.py`.

### Проверить подписчиков

```python
from eve.telegram_notifier import load_users
print(load_users())  # Список chat_id
```

### Проверить статистику

```python
import json
with open('data/bot_stats.json') as f:
    print(json.load(f))
```

### Тестовое уведомление

```python
from eve.telegram_notifier import notify_all_users
notify_all_users("🧪 Тест уведомления")
```

---

## ✅ Checklist запуска

- [ ] Установлен `python-telegram-bot` (`pip install python-telegram-bot`)
- [ ] Запущен `python scripts/telegram_bot.py` (первое окно)
- [ ] Запущен `python scripts/eve_farm_bot.py` (второе окно)
- [ ] Отправлен `/start` боту в Telegram
- [ ] Подписка подтверждена ✅

---

**Удачного фарма! 🚀**
