"""
Eve Framework - Visual Windows Automation
Автоматизация Windows приложений через распознавание изображений.
"""

from eve.screen import screenshot, crop_and_save
from eve.vision import find_image, find_all_images, wait_image, wait_image_disappear
from eve.mouse import click, double_click, right_click, click_on_image, move_to
from eve.keyboard import type_text, press_key, hotkey
from eve.window import activate_window, list_windows, get_active_window

__version__ = "0.1.0"
__all__ = [
    # Screen
    "screenshot",
    "crop_and_save",
    # Vision
    "find_image",
    "find_all_images",
    "wait_image",
    "wait_image_disappear",
    # Mouse
    "click",
    "double_click",
    "right_click",
    "click_on_image",
    "move_to",
    # Keyboard
    "type_text",
    "press_key",
    "hotkey",
    # Window
    "activate_window",
    "list_windows",
    "get_active_window",
]
