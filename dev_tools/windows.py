"""
Dev Tools: Window Management Utility
Утилита для работы с окнами - список, активация, информация.
"""

import sys
import os

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    import pygetwindow as gw
except ImportError:
    print("ERROR: pygetwindow not installed. Run: pip install pygetwindow")
    sys.exit(1)


def list_windows(filter_text: str = None):
    """
    Показать список всех окон.
    filter_text: опциональный фильтр по заголовку (case-insensitive)
    """
    windows = gw.getAllWindows()

    # Фильтруем пустые заголовки и применяем текстовый фильтр
    windows = [w for w in windows if w.title.strip()]

    if filter_text:
        filter_lower = filter_text.lower()
        windows = [w for w in windows if filter_lower in w.title.lower()]

    print(f"Found {len(windows)} window(s):")
    for i, w in enumerate(windows):
        status = []
        if w.isMinimized:
            status.append("minimized")
        if w.isMaximized:
            status.append("maximized")
        if w.isActive:
            status.append("ACTIVE")

        status_str = f" [{', '.join(status)}]" if status else ""
        pos = f"({w.left}, {w.top})" if w.left is not None else "(?, ?)"
        size = f"{w.width}x{w.height}" if w.width is not None else "?x?"

        print(f"  [{i}] {w.title[:60]}{status_str}")
        print(f"      Position: {pos}, Size: {size}")


def activate_window(title_filter: str):
    """
    Активировать окно по части заголовка.
    Если найдено несколько - активирует первое.
    """
    windows = gw.getWindowsWithTitle(title_filter)

    if not windows:
        print(f"ERROR: No window found matching '{title_filter}'")
        return False

    if len(windows) > 1:
        print(f"Found {len(windows)} windows matching '{title_filter}':")
        for i, w in enumerate(windows):
            print(f"  [{i}] {w.title}")
        print(f"Activating first one...")

    win = windows[0]

    try:
        # Restore if minimized
        if win.isMinimized:
            win.restore()

        # Activate
        win.activate()
        print(f"Activated: {win.title}")
        return True
    except Exception as e:
        print(f"ERROR activating window: {e}")
        return False


def get_active_window():
    """Показать информацию об активном окне."""
    try:
        win = gw.getActiveWindow()
        if win:
            print(f"Active window: {win.title}")
            print(f"  Position: ({win.left}, {win.top})")
            print(f"  Size: {win.width}x{win.height}")
            print(f"  Maximized: {win.isMaximized}")
            return win
        else:
            print("No active window")
            return None
    except Exception as e:
        print(f"ERROR: {e}")
        return None


def window_info(title_filter: str):
    """Подробная информация об окне."""
    windows = gw.getWindowsWithTitle(title_filter)

    if not windows:
        print(f"ERROR: No window found matching '{title_filter}'")
        return

    for win in windows:
        print(f"Window: {win.title}")
        print(f"  Position: ({win.left}, {win.top})")
        print(f"  Size: {win.width}x{win.height}")
        print(f"  Client area: ({win.left}, {win.top}) to ({win.left + win.width}, {win.top + win.height})")
        print(f"  Minimized: {win.isMinimized}")
        print(f"  Maximized: {win.isMaximized}")
        print(f"  Active: {win.isActive}")
        print()


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Window management utility")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # list command
    list_parser = subparsers.add_parser("list", help="List all windows")
    list_parser.add_argument("--filter", "-f", help="Filter by title (case-insensitive)")

    # activate command
    activate_parser = subparsers.add_parser("activate", help="Activate window by title")
    activate_parser.add_argument("title", help="Part of window title to match")

    # active command
    subparsers.add_parser("active", help="Show active window info")

    # info command
    info_parser = subparsers.add_parser("info", help="Show detailed window info")
    info_parser.add_argument("title", help="Part of window title to match")

    args = parser.parse_args()

    if args.command == "list":
        list_windows(args.filter)
    elif args.command == "activate":
        activate_window(args.title)
    elif args.command == "active":
        get_active_window()
    elif args.command == "info":
        window_info(args.title)
    else:
        parser.print_help()
