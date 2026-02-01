"""
Автоматизация Блокнота: File -> Save As
"""

import sys
import os
import time

# Добавляем путь к eve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eve import (
    activate_window,
    click_on_image,
    wait_image,
    type_text,
    hotkey,
    press_key
)


def notepad_save_as(filename: str):
    """
    Открыть диалог Save As в Блокноте и ввести имя файла.

    Args:
        filename: Имя файла для сохранения
    """
    print("Активирую Блокнот...")
    if not activate_window("Блокнот"):
        print("ERROR: Блокнот не найден")
        return False

    time.sleep(0.5)

    print("Кликаю на меню 'Файл'...")
    if not click_on_image("notepad_file_menu.png", timeout=5):
        print("ERROR: Кнопка 'Файл' не найдена")
        return False

    time.sleep(0.3)

    print("Кликаю 'Сохранить как...'")
    if not click_on_image("notepad_save_as.png", timeout=5):
        print("ERROR: Пункт 'Сохранить как' не найден")
        return False

    time.sleep(1)  # Ждем открытия диалога

    print(f"Ввожу имя файла: {filename}")
    type_text(filename)

    time.sleep(0.3)

    print("Нажимаю Enter для сохранения...")
    press_key("enter")

    print("Готово!")
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Сохранить файл в Блокноте через File -> Save As")
    parser.add_argument("filename", help="Имя файла для сохранения")

    args = parser.parse_args()

    notepad_save_as(args.filename)
