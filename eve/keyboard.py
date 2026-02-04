"""
Eve Framework - Keyboard control module
"""

import pyautogui

# Set typing interval (delay between keystrokes)
pyautogui.PAUSE = 0.05


def type_text(text: str, interval: float = 0.05):
    """
    Ввести текст с клавиатуры.

    Args:
        text: Текст для ввода
        interval: Задержка между символами (секунды)
    """
    pyautogui.typewrite(text, interval=interval) if text.isascii() else pyautogui.write(text, interval=interval)


def type_unicode(text: str, interval: float = 0.05):
    """
    Ввести Unicode текст (включая кириллицу).
    Использует буфер обмена для надежного ввода.

    Args:
        text: Текст для ввода
        interval: Задержка (не используется напрямую)
    """
    import pyperclip

    # Save current clipboard
    try:
        old_clipboard = pyperclip.paste()
    except:
        old_clipboard = ""

    # Copy text to clipboard and paste
    pyperclip.copy(text)
    pyautogui.hotkey("ctrl", "v")

    # Restore clipboard
    try:
        pyperclip.copy(old_clipboard)
    except:
        pass


def press_key(key: str):
    """
    Нажать клавишу или комбинацию клавиш.

    Args:
        key: Имя клавиши (enter, tab, escape, space, backspace, delete,
             up, down, left, right, home, end, pageup, pagedown,
             f1-f12, и т.д.)
             Или комбинация через + (например: 'alt+c', 'ctrl+shift+s')
    
    Examples:
        press_key('enter')
        press_key('alt+c')
        press_key('ctrl+shift+s')
    """
    if '+' in key:
        # Комбинация клавиш
        keys = key.split('+')
        pyautogui.hotkey(*keys)
    else:
        # Одна клавиша
        pyautogui.press(key)


def hotkey(*keys: str):
    """
    Нажать комбинацию клавиш.

    Args:
        *keys: Клавиши для комбинации (например: 'ctrl', 'c')

    Examples:
        hotkey('ctrl', 'c')  # Copy
        hotkey('ctrl', 'v')  # Paste
        hotkey('alt', 'tab') # Switch window
        hotkey('ctrl', 'shift', 's')  # Save As
    """
    pyautogui.hotkey(*keys)


def key_down(key: str):
    """Зажать клавишу."""
    pyautogui.keyDown(key)


def key_up(key: str):
    """Отпустить клавишу."""
    pyautogui.keyUp(key)
