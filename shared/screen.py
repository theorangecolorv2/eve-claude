"""
Eve Framework - Screen capture module
"""

import os
from typing import Optional, Tuple
import mss
import mss.tools
from PIL import Image


def screenshot(save_path: Optional[str] = None, region: Optional[Tuple[int, int, int, int]] = None) -> Image.Image:
    """
    Сделать скриншот экрана или области.

    Args:
        save_path: Путь для сохранения (опционально)
        region: Область (x1, y1, x2, y2) или None для всего экрана

    Returns:
        PIL Image объект
    """
    with mss.mss() as sct:
        if region:
            x1, y1, x2, y2 = region
            monitor = {
                "left": x1,
                "top": y1,
                "width": x2 - x1,
                "height": y2 - y1
            }
        else:
            monitor = sct.monitors[1]  # Primary monitor

        sct_img = sct.grab(monitor)

        # Convert to PIL Image
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

        if save_path:
            img.save(save_path)

        return img


def crop_and_save(image: Image.Image, x1: int, y1: int, x2: int, y2: int, output_path: str) -> Image.Image:
    """
    Вырезать область из изображения и сохранить.

    Args:
        image: PIL Image или путь к файлу
        x1, y1: Верхний левый угол
        x2, y2: Нижний правый угол
        output_path: Путь для сохранения

    Returns:
        Вырезанное изображение
    """
    if isinstance(image, str):
        image = Image.open(image)

    cropped = image.crop((x1, y1, x2, y2))
    cropped.save(output_path)
    return cropped
