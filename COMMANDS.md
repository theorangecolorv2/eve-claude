# Eve Framework - Команды для разработки

## Наш рабочий процесс

1. Ты описываешь задачу: "нужно открыть Excel, нажать File → Save As"
2. Я активирую нужное окно и делаю скриншот
3. Смотрю скриншот, нахожу нужные элементы
4. Вырезаю их в assets/ (кнопки, иконки, меню)
5. Пишу сценарий автоматизации

---

## Команды для скриншотов (dev_tools/capture.py)

```bash
# Скриншот всего экрана
python dev_tools/capture.py full --name имя_файла

# Скриншот конкретного монитора
python dev_tools/capture.py monitor --monitor 1 --name имя

# Скриншот области
python dev_tools/capture.py region --region X1 Y1 X2 Y2 --name имя

# Скриншот с задержкой (чтобы успеть открыть меню)
python dev_tools/capture.py delayed --delay 3 --name имя

# Показать мониторы
python dev_tools/capture.py monitors
```

---

## Команды для обрезки (dev_tools/crop.py)

```bash
# Вырезать элемент и сохранить в assets/
python dev_tools/crop.py crop имя_скриншота X1 Y1 X2 Y2 --name имя_элемента

# Вырезать во временную папку
python dev_tools/crop.py crop имя_скриншота X1 Y1 X2 Y2 --name имя --temp

# Информация об изображении
python dev_tools/crop.py info имя_файла

# Список assets
python dev_tools/crop.py assets

# Список temp файлов
python dev_tools/crop.py temp
```

---

## Команды для окон (dev_tools/windows.py)

```bash
# Список всех окон
python dev_tools/windows.py list

# Фильтр по имени
python dev_tools/windows.py list --filter "Excel"

# Активировать окно
python dev_tools/windows.py activate "Excel"

# Информация об активном окне
python dev_tools/windows.py active

# Подробная информация об окне
python dev_tools/windows.py info "Excel"
```

---

## Структура проекта

```
eve-claude/
├── eve/                    # Основной фреймворк
│   ├── screen.py          # screenshot(), crop_and_save()
│   ├── vision.py          # find_image(), wait_image()
│   ├── mouse.py           # click(), click_on_image()
│   ├── keyboard.py        # type_text(), hotkey()
│   └── window.py          # activate_window()
├── assets/                 # Шаблоны UI элементов (.png)
├── scripts/                # Сценарии автоматизации
├── dev_tools/              # Утилиты для разработки
│   ├── capture.py         # Скриншоты
│   ├── crop.py            # Обрезка изображений
│   └── windows.py         # Управление окнами
└── temp/                   # Временные файлы
```

---

## Пример сценария автоматизации

```python
from eve import (
    activate_window,
    click_on_image,
    wait_image,
    type_text,
    hotkey
)

# Активировать Notepad
activate_window("Notepad")

# Кликнуть на меню File
click_on_image("assets/notepad_file_menu.png")

# Ждать появления меню, кликнуть Save As
wait_image("assets/menu_save_as.png", timeout=5)
click_on_image("assets/menu_save_as.png")

# Ввести имя файла
type_text("my_document.txt")
hotkey("enter")
```
