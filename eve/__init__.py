"""
Eve Framework - Visual Windows Automation
Автоматизация Windows приложений через распознавание изображений.

Модули:
- mouse: Хуманизированное управление мышью (Bezier curves)
- keyboard: Управление клавиатурой
- vision: Template matching (OpenCV)
- screen: Захват экрана
- window: Управление окнами
- actions: Высокоуровневые действия (click_on_image и т.д.)

EVE-специфичные модули:
- overview: Работа с Overview (подсчёт целей, лок, убийство)
- hud: Работа с HUD (пушки, модули)
- combat: Управление дронами
"""

# Screen
from eve.screen import screenshot, crop_and_save

# Vision (template matching)
from eve.vision import (
    find_image,
    find_all_images,
    wait_image,
    wait_image_disappear,
)

# Mouse (с хуманизацией)
from eve.mouse import (
    click,
    double_click,
    right_click,
    middle_click,
    move_to,
    drag,
    scroll,
    get_position,
    random_delay,
    HumanConfig,
)

# Keyboard
from eve.keyboard import (
    type_text,
    type_unicode,
    press_key,
    hotkey,
    key_down,
    key_up,
)

# Window
from eve.window import (
    activate_window,
    list_windows,
    get_active_window,
    minimize_window,
    maximize_window,
    close_window,
    move_window,
    resize_window,
)

# Actions (высокоуровневые действия)
from eve.actions import (
    click_on_image,
    double_click_on_image,
    right_click_on_image,
    right_click_menu,
    wait_and_click,
    wait_and_double_click,
    is_visible,
    find_on_screen,
    wait_until_visible,
    wait_until_gone,
    click_sequence,
    hover_on_image,
)

# === EVE-СПЕЦИФИЧНЫЕ МОДУЛИ ===

# HUD (пушки, модули)
from eve.hud import (
    HUDConfig,
    find_gun,
    get_gun_region,
    is_gun_active,
    are_guns_active,
    are_guns_calm,
    wait_guns_deactivate,
)

# Overview (подсчёт целей, лок, убийство)
from eve.overview import (
    OverviewDetectConfig,
    is_overview_empty,
    has_locked_targets,
    find_header_position,
    get_row_position,
    count_targets,
    count_targets_detailed,
    lock_all_targets,
    kill_locked_targets,
    lock_and_kill,
    clear_anomaly,
)

# Combat (дроны)
from eve.combat import (
    launch_drones,
    engage_drones,
    recall_drones,
)

# Navigation (навигация по маршруту)
from eve.navigation import (
    NavigationConfig,
    has_anomaly_ubejishe,
    has_anomaly_ukrytie,
    has_anomalies,
    find_anomaly,
    find_anomaly_ukrytie,
    find_anomaly_ubejishe,
    warp_to_ukrytie,
    warp_to_ubejishe,
    warp_to_anomaly,
    click_tab_jump,
    click_tab_pvp_foe,
    click_yellow_gate,
    click_jump_button,
    wait_jump_complete,
    wait_for_targets,
    jump_to_next_system,
    farm_anomaly,
    farm_system,
)


__version__ = "0.3.0"

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
    "middle_click",
    "move_to",
    "drag",
    "scroll",
    "get_position",
    "random_delay",
    "HumanConfig",
    # Keyboard
    "type_text",
    "type_unicode",
    "press_key",
    "hotkey",
    "key_down",
    "key_up",
    # Window
    "activate_window",
    "list_windows",
    "get_active_window",
    "minimize_window",
    "maximize_window",
    "close_window",
    "move_window",
    "resize_window",
    # Actions
    "click_on_image",
    "double_click_on_image",
    "right_click_on_image",
    "right_click_menu",
    "wait_and_click",
    "wait_and_double_click",
    "is_visible",
    "find_on_screen",
    "wait_until_visible",
    "wait_until_gone",
    "click_sequence",
    "hover_on_image",
    # HUD
    "HUDConfig",
    "find_gun",
    "get_gun_region",
    "is_gun_active",
    "are_guns_active",
    "are_guns_calm",
    "wait_guns_deactivate",
    # Overview
    "OverviewDetectConfig",
    "is_overview_empty",
    "has_locked_targets",
    "find_header_position",
    "get_row_position",
    "count_targets",
    "count_targets_detailed",
    "lock_all_targets",
    "kill_locked_targets",
    "lock_and_kill",
    "clear_anomaly",
    # Combat (drones)
    "launch_drones",
    "engage_drones",
    "recall_drones",
    # Navigation
    "NavigationConfig",
    "has_anomaly_ubejishe",
    "has_anomaly_ukrytie",
    "has_anomalies",
    "find_anomaly",
    "find_anomaly_ukrytie",
    "find_anomaly_ubejishe",
    "warp_to_ukrytie",
    "warp_to_ubejishe",
    "warp_to_anomaly",
    "click_tab_jump",
    "click_tab_pvp_foe",
    "click_yellow_gate",
    "click_jump_button",
    "wait_jump_complete",
    "wait_for_targets",
    "jump_to_next_system",
    "farm_anomaly",
    "farm_system",
]
