# HUMANIZATION.md - Хуманизация бота

> **ВАЖНО**: Хуманизация теперь ВСТРОЕНА в модуль `eve/`. Не нужно писать вручную!

---

## Что уже встроено в eve/

### Движения мыши (Bezier curves)

```python
from eve import click, move_to

# Хуманизация ВКЛЮЧЕНА по умолчанию
click(500, 300)      # Bezier curve + random delays + смещение от центра
move_to(500, 300)    # Плавное движение по кривой Безье
```

**Что происходит автоматически:**
- Движение по кривой Безье (2 контрольные точки)
- Автоматическое время движения (по расстоянию)
- Смещение от центра при клике (±3px)
- Реалистичное время удержания кнопки
- Рандомные паузы до/после клика

### Высокоуровневые действия

```python
from eve import (
    click_on_image,
    double_click_on_image,
    right_click_on_image,
    right_click_menu,
    wait_and_click,
)

# Всё уже хуманизировано!
click_on_image("button.png")
double_click_on_image("anomaly.png")
right_click_menu("target.png", "orbit.png")
```

---

## Настройки хуманизации

Можно настроить через `HumanConfig`:

```python
from eve import HumanConfig

# Движение мыши
HumanConfig.MOVE_DURATION_MIN = 0.15        # Минимальное время движения (сек)
HumanConfig.MOVE_DURATION_MAX = 0.4         # Максимальное время движения
HumanConfig.MOVE_STEPS_PER_SECOND = 120     # Точек в секунду (плавность)

# Bezier curve
HumanConfig.BEZIER_CONTROL_POINTS = 2       # Контрольные точки (2-3)
HumanConfig.BEZIER_DEVIATION_MIN = 10       # Минимальное отклонение (px)
HumanConfig.BEZIER_DEVIATION_MAX = 80       # Максимальное отклонение

# Клики
HumanConfig.CLICK_OFFSET_MAX = 3            # Смещение от центра (px)
HumanConfig.CLICK_DELAY_MIN = 0.02          # Задержка перед кликом
HumanConfig.CLICK_DELAY_MAX = 0.08
HumanConfig.CLICK_DURATION_MIN = 0.05       # Время удержания кнопки
HumanConfig.CLICK_DURATION_MAX = 0.12

# Между действиями
HumanConfig.ACTION_DELAY_MIN = 0.1
HumanConfig.ACTION_DELAY_MAX = 0.25
```

---

## Паузы между действиями

Используй `random_delay()` между действиями:

```python
from eve import click_on_image, random_delay

click_on_image("button1.png")
random_delay(0.3, 0.8)  # Пауза 0.3-0.8 сек
click_on_image("button2.png")
random_delay(0.5, 1.5)  # Более длинная пауза
click_on_image("button3.png")
```

---

## Отключение хуманизации (для отладки)

```python
from eve import click, move_to

# Для быстрой отладки - без хуманизации
click(500, 300, humanize=False)
move_to(500, 300, humanize=False)
```

---

## ⚠️ Чего НЕ делать

### ❌ Не используй pyautogui напрямую

```python
# ПЛОХО - телепортация курсора
import pyautogui
pyautogui.click(500, 300)

# ХОРОШО - хуманизация встроена
from eve import click
click(500, 300)
```

### ❌ Не добавляй случайные ошибки

```python
# ПЛОХО - может сломать бота
miss_x = x + random.randint(-30, 30)
click(miss_x, y)
```

### ❌ Не добавляй рандомные действия без разрешения

```python
# ПЛОХО - только с разрешения пользователя
if random.random() < 0.1:
    check_chat()
    move_camera()
```

---

## Итог

**Хуманизация = встроена в eve/**

Просто используй функции из `eve` и всё будет хуманизировано автоматически:
- `click()`, `double_click()`, `right_click()`
- `click_on_image()`, `double_click_on_image()`
- `right_click_menu()`
- `move_to()`, `drag()`

Между действиями добавляй `random_delay()`.

**Не нужно больше:**
- Вручную писать move_to + sleep + click
- Настраивать duration для каждого движения
- Добавлять паузы внутри клика

Всё уже сделано в `eve/mouse.py` и `eve/actions.py`.
