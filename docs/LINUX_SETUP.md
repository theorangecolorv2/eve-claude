# Запуск на Linux (EVE через Steam Proton)

## Требования

- Linux x86_64 (Ubuntu 22.04+, Arch, Fedora)
- Python 3.8+
- EVE Online через Steam Proton
- Тот же пользователь что запускает EVE (или `ptrace_scope=0`)

## Быстрый старт

### 1. Настроить доступ к памяти

```bash
# Вариант А: временно (до перезагрузки)
echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope

# Вариант Б: постоянно
echo 'kernel.yama.ptrace_scope = 0' | sudo tee /etc/sysctl.d/10-ptrace.conf
sudo sysctl -p /etc/sysctl.d/10-ptrace.conf
```

> **Зачем?** Linux по умолчанию запрещает одному процессу читать память другого.
> `ptrace_scope=0` разрешает это для процессов того же пользователя.

### 2. Запустить EVE Online через Steam

```bash
steam steam://rungameid/8500  # или через GUI
```

Дождитесь полной загрузки (экран выбора персонажа или в игре).

### 3. Проверить что EVE видна

```bash
ps aux | grep exefile.exe
```

Должно показать что-то вроде:
```
user  12345  ... /path/to/wine64-preloader .../exefile.exe ...
```

### 4. Запустить диагностику

```bash
cd /path/to/eve-claude
python scripts/test_linux_reader.py
```

Скрипт пройдёт 7 этапов:
1. Поиск процесса EVE
2. Доступ к `/proc/pid/mem`
3. Анализ карты памяти
4. Поиск Python type-объектов
5. Поиск типа UIRoot
6. Поиск экземпляров UIRoot
7. Чтение UI tree + сохранение JSON

При успехе — JSON сохранится в `output/linux_ui_tree_*.json`.

### 5. Запустить бота

```bash
python scripts/run_abyss_farmer.py
```

На Linux бот автоматически использует Python memory reader вместо C# exe.

## Как это работает

На Windows бот запускает `read-memory-64-bit.exe` (C#) как subprocess.
На Linux этот exe не работает. Вместо него используется чистый Python:

```
/proc/pid/mem  →  linux_process.py  →  linux_cpython.py  →  linux_reader.py
   (raw bytes)      (read/write)        (CPython 2.7)        (UI tree JSON)
```

EVE Online содержит встроенный CPython 2.7 (Stackless Python).
UI tree — это дерево Python-объектов в памяти процесса.
Мы читаем эти объекты напрямую, используя `/proc/pid/mem`.

Результат — JSON в том же формате что и C# exe,
поэтому `parser.py` и весь остальной бот работают без изменений.

## Отладка

### "Процесс EVE не найден"

```bash
# Проверить все процессы с .exe
ps aux | grep -i '\.exe'

# Проверить cmdline всех Wine процессов
for pid in /proc/[0-9]*/cmdline; do
    if grep -ql 'exefile' "$pid" 2>/dev/null; then
        echo "$pid: $(cat $pid | tr '\0' ' ')"
    fi
done
```

### "Нет доступа к /proc/pid/mem"

```bash
# Проверить ptrace_scope
cat /proc/sys/kernel/yama/ptrace_scope
# Должно быть 0

# Проверить владельца процесса
ps -o user= -p $(pgrep -f exefile.exe)
# Должен совпадать с текущим пользователем
```

### "UIRoot не найден"

- EVE полностью загружена? (не splash screen, а в игре)
- Попробуйте подождать 30 секунд и запустить заново
- Проверьте логи на этапе 4 — если Python типы найдены, но UIRoot нет, возможно нужно сканировать больше памяти

### "UI tree пустой / мало нод"

- Проблема с `__dict__` offset — запустите тест, он покажет brute-force диагностику
- Если `__dict__` не находится ни по одному offset — это значит что CPython struct layout отличается от ожидаемого
- Создайте issue с выводом `test_linux_reader.py`

## Известные ограничения

- **Mouse/keyboard**: `eve/mouse.py` и `eve/keyboard.py` используют Windows API (pyautogui). На Linux нужна отдельная реализация через Xdotool/python-xlib (TODO).
- **Performance**: первый поиск UIRoot может занять 1-3 минуты (сканирование всей памяти). Повторные чтения быстрые (~100ms).
- **Proton updates**: если Steam обновит Proton, структура процесса может измениться. В этом случае может потребоваться обновление кода поиска процесса.
