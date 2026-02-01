"""
Dev Tools: Image Cropping Utility
Утилита для вырезания элементов UI из скриншотов и сохранения в assets.
"""

import sys
import os
from datetime import datetime

try:
    from PIL import Image
except ImportError:
    print("ERROR: pillow not installed. Run: pip install pillow")
    sys.exit(1)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = os.path.join(PROJECT_ROOT, "temp")
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")

os.makedirs(ASSETS_DIR, exist_ok=True)


def crop_image(source: str, x1: int, y1: int, x2: int, y2: int, output_name: str = None, to_assets: bool = True) -> str:
    """
    Вырезать область из изображения.

    Args:
        source: Путь к исходному изображению (или имя файла в temp/)
        x1, y1: Верхний левый угол
        x2, y2: Нижний правый угол
        output_name: Имя выходного файла (без расширения)
        to_assets: True = сохранить в assets/, False = в temp/

    Returns:
        Путь к сохраненному файлу
    """
    # Определяем полный путь к source
    if not os.path.isabs(source):
        # Проверяем сначала в temp, потом в assets
        temp_path = os.path.join(TEMP_DIR, source)
        assets_path = os.path.join(ASSETS_DIR, source)

        if os.path.exists(temp_path):
            source = temp_path
        elif os.path.exists(assets_path):
            source = assets_path
        elif os.path.exists(source + ".png"):
            source = source + ".png"
        elif os.path.exists(os.path.join(TEMP_DIR, source + ".png")):
            source = os.path.join(TEMP_DIR, source + ".png")
        else:
            print(f"ERROR: Source file not found: {source}")
            return None

    # Генерируем имя если не указано
    if output_name is None:
        output_name = f"crop_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Определяем выходной путь
    output_dir = ASSETS_DIR if to_assets else TEMP_DIR
    output_path = os.path.join(output_dir, f"{output_name}.png")

    # Открываем и обрезаем
    try:
        img = Image.open(source)
        cropped = img.crop((x1, y1, x2, y2))
        cropped.save(output_path)

        print(f"Cropped: {output_path}")
        print(f"  Source: {source}")
        print(f"  Region: ({x1}, {y1}) to ({x2}, {y2})")
        print(f"  Size: {cropped.width}x{cropped.height}")

        return output_path
    except Exception as e:
        print(f"ERROR: {e}")
        return None


def image_info(source: str):
    """Показать информацию об изображении."""
    if not os.path.isabs(source):
        for base in [TEMP_DIR, ASSETS_DIR, "."]:
            for ext in ["", ".png", ".jpg", ".jpeg"]:
                path = os.path.join(base, source + ext)
                if os.path.exists(path):
                    source = path
                    break
            else:
                continue
            break

    if not os.path.exists(source):
        print(f"ERROR: File not found: {source}")
        return

    img = Image.open(source)
    print(f"Image: {source}")
    print(f"  Size: {img.width}x{img.height}")
    print(f"  Mode: {img.mode}")
    print(f"  Format: {img.format}")


def list_assets():
    """Показать все файлы в assets/."""
    print(f"Assets in {ASSETS_DIR}:")
    if not os.path.exists(ASSETS_DIR):
        print("  (empty)")
        return

    files = sorted(os.listdir(ASSETS_DIR))
    if not files:
        print("  (empty)")
        return

    for f in files:
        path = os.path.join(ASSETS_DIR, f)
        if os.path.isfile(path):
            try:
                img = Image.open(path)
                print(f"  {f}: {img.width}x{img.height}")
            except:
                print(f"  {f}: (not an image)")


def list_temp():
    """Показать все файлы в temp/."""
    print(f"Temp files in {TEMP_DIR}:")
    if not os.path.exists(TEMP_DIR):
        print("  (empty)")
        return

    files = sorted(os.listdir(TEMP_DIR))
    if not files:
        print("  (empty)")
        return

    for f in files:
        path = os.path.join(TEMP_DIR, f)
        if os.path.isfile(path):
            try:
                img = Image.open(path)
                print(f"  {f}: {img.width}x{img.height}")
            except:
                print(f"  {f}: (not an image)")


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Image cropping utility")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # crop command
    crop_parser = subparsers.add_parser("crop", help="Crop region from image")
    crop_parser.add_argument("source", help="Source image path or name")
    crop_parser.add_argument("x1", type=int, help="Left X coordinate")
    crop_parser.add_argument("y1", type=int, help="Top Y coordinate")
    crop_parser.add_argument("x2", type=int, help="Right X coordinate")
    crop_parser.add_argument("y2", type=int, help="Bottom Y coordinate")
    crop_parser.add_argument("--name", "-n", help="Output filename")
    crop_parser.add_argument("--temp", "-t", action="store_true", help="Save to temp/ instead of assets/")

    # info command
    info_parser = subparsers.add_parser("info", help="Show image info")
    info_parser.add_argument("source", help="Image path or name")

    # list commands
    subparsers.add_parser("assets", help="List assets")
    subparsers.add_parser("temp", help="List temp files")

    args = parser.parse_args()

    if args.command == "crop":
        crop_image(args.source, args.x1, args.y1, args.x2, args.y2,
                   output_name=args.name, to_assets=not args.temp)
    elif args.command == "info":
        image_info(args.source)
    elif args.command == "assets":
        list_assets()
    elif args.command == "temp":
        list_temp()
    else:
        parser.print_help()
