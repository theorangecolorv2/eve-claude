"""
Dev Tools: Screen Capture Utilities
Утилиты для захвата экрана во время разработки автоматизаций.
Запускай эти команды, а я (Claude) буду смотреть результаты через Read tool.
"""

import sys
import os
import time
from datetime import datetime

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import mss
    import mss.tools
except ImportError:
    print("ERROR: mss not installed. Run: pip install mss")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("ERROR: pillow not installed. Run: pip install pillow")
    sys.exit(1)

# Пути
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = os.path.join(PROJECT_ROOT, "temp")
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)


def screenshot_full(name: str = None) -> str:
    """
    Скриншот всего экрана.
    Сохраняет в temp/screen_YYYYMMDD_HHMMSS.png или temp/{name}.png
    """
    if name is None:
        name = f"screen_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    output_path = os.path.join(TEMP_DIR, f"{name}.png")

    with mss.mss() as sct:
        # Захватываем весь экран (все мониторы)
        monitor = sct.monitors[0]  # 0 = все мониторы, 1 = первый монитор
        screenshot = sct.grab(monitor)
        mss.tools.to_png(screenshot.rgb, screenshot.size, output=output_path)

    print(f"Screenshot saved: {output_path}")
    print(f"Size: {screenshot.width}x{screenshot.height}")
    return output_path


def screenshot_monitor(monitor_num: int = 1, name: str = None) -> str:
    """
    Скриншот конкретного монитора.
    monitor_num: 1 = первый монитор, 2 = второй, и т.д.
    """
    if name is None:
        name = f"monitor{monitor_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    output_path = os.path.join(TEMP_DIR, f"{name}.png")

    with mss.mss() as sct:
        if monitor_num >= len(sct.monitors):
            print(f"ERROR: Monitor {monitor_num} not found. Available: {len(sct.monitors)-1}")
            return None

        monitor = sct.monitors[monitor_num]
        screenshot = sct.grab(monitor)
        mss.tools.to_png(screenshot.rgb, screenshot.size, output=output_path)

    print(f"Screenshot saved: {output_path}")
    print(f"Monitor {monitor_num}: {screenshot.width}x{screenshot.height}")
    return output_path


def screenshot_region(x1: int, y1: int, x2: int, y2: int, name: str = None) -> str:
    """
    Скриншот области экрана.
    Координаты: (x1, y1) - верхний левый угол, (x2, y2) - нижний правый.
    """
    if name is None:
        name = f"region_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    output_path = os.path.join(TEMP_DIR, f"{name}.png")

    region = {
        "left": x1,
        "top": y1,
        "width": x2 - x1,
        "height": y2 - y1
    }

    with mss.mss() as sct:
        screenshot = sct.grab(region)
        mss.tools.to_png(screenshot.rgb, screenshot.size, output=output_path)

    print(f"Screenshot saved: {output_path}")
    print(f"Region: ({x1}, {y1}) to ({x2}, {y2}) = {region['width']}x{region['height']}")
    return output_path


def screenshot_delayed(delay: float = 3.0, name: str = None) -> str:
    """
    Скриншот с задержкой (чтобы успеть переключить окно/открыть меню).
    """
    print(f"Taking screenshot in {delay} seconds...")
    for i in range(int(delay), 0, -1):
        print(f"  {i}...")
        time.sleep(1)
    if delay % 1 > 0:
        time.sleep(delay % 1)

    return screenshot_full(name)


def list_monitors():
    """Показать информацию о мониторах."""
    with mss.mss() as sct:
        print(f"Found {len(sct.monitors) - 1} monitor(s):")
        for i, m in enumerate(sct.monitors):
            if i == 0:
                print(f"  [0] ALL: {m['width']}x{m['height']} (virtual screen)")
            else:
                print(f"  [{i}] Monitor {i}: {m['width']}x{m['height']} at ({m['left']}, {m['top']})")


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Screen capture utility")
    parser.add_argument("command", choices=["full", "monitor", "region", "delayed", "monitors"],
                        help="Command to execute")
    parser.add_argument("--name", "-n", help="Output filename (without extension)")
    parser.add_argument("--monitor", "-m", type=int, default=1, help="Monitor number (for 'monitor' command)")
    parser.add_argument("--region", "-r", nargs=4, type=int, metavar=("X1", "Y1", "X2", "Y2"),
                        help="Region coordinates (for 'region' command)")
    parser.add_argument("--delay", "-d", type=float, default=3.0, help="Delay in seconds (for 'delayed' command)")

    args = parser.parse_args()

    if args.command == "full":
        screenshot_full(args.name)
    elif args.command == "monitor":
        screenshot_monitor(args.monitor, args.name)
    elif args.command == "region":
        if not args.region:
            print("ERROR: --region X1 Y1 X2 Y2 required")
        else:
            screenshot_region(*args.region, name=args.name)
    elif args.command == "delayed":
        screenshot_delayed(args.delay, args.name)
    elif args.command == "monitors":
        list_monitors()
