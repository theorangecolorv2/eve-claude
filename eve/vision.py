"""
Eve Framework - Computer vision module (OpenCV template matching)
"""

import os
import time
from typing import Optional, Tuple, List
import cv2
import numpy as np
from PIL import Image
import mss


# Default assets directory
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")


def _get_template_path(template: str) -> str:
    """Resolve template path - check assets/ if not absolute."""
    if os.path.isabs(template):
        return template
    if os.path.exists(template):
        return template

    # Check in assets
    assets_path = os.path.join(ASSETS_DIR, template)
    if os.path.exists(assets_path):
        return assets_path
    if os.path.exists(assets_path + ".png"):
        return assets_path + ".png"

    return template  # Return as-is, let OpenCV handle the error


def _grab_screen() -> np.ndarray:
    """Capture screen and return as OpenCV BGR image."""
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # Primary monitor
        sct_img = sct.grab(monitor)
        # Convert to numpy array (BGRA -> BGR)
        img = np.array(sct_img)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)


def find_image(template: str, confidence: float = 0.9, region: Optional[Tuple[int, int, int, int]] = None) -> Optional[Tuple[int, int]]:
    """
    Найти изображение на экране.

    Args:
        template: Путь к изображению-шаблону или имя файла в assets/
        confidence: Порог совпадения (0.0 - 1.0)
        region: Область поиска (x1, y1, x2, y2) или None для всего экрана

    Returns:
        (x, y) центр найденного изображения или None
    """
    template_path = _get_template_path(template)
    template_img = cv2.imread(template_path)

    if template_img is None:
        raise FileNotFoundError(f"Template not found: {template_path}")

    screen = _grab_screen()

    if region:
        x1, y1, x2, y2 = region
        screen = screen[y1:y2, x1:x2]
        offset_x, offset_y = x1, y1
    else:
        offset_x, offset_y = 0, 0

    # Template matching
    result = cv2.matchTemplate(screen, template_img, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    if max_val >= confidence:
        # Return center of found region
        h, w = template_img.shape[:2]
        center_x = max_loc[0] + w // 2 + offset_x
        center_y = max_loc[1] + h // 2 + offset_y
        return (center_x, center_y)

    return None


def find_all_images(template: str, confidence: float = 0.9, region: Optional[Tuple[int, int, int, int]] = None) -> List[Tuple[int, int]]:
    """
    Найти все вхождения изображения на экране.

    Args:
        template: Путь к изображению-шаблону
        confidence: Порог совпадения
        region: Область поиска или None

    Returns:
        Список координат (x, y) центров найденных изображений
    """
    template_path = _get_template_path(template)
    template_img = cv2.imread(template_path)

    if template_img is None:
        raise FileNotFoundError(f"Template not found: {template_path}")

    screen = _grab_screen()

    if region:
        x1, y1, x2, y2 = region
        screen = screen[y1:y2, x1:x2]
        offset_x, offset_y = x1, y1
    else:
        offset_x, offset_y = 0, 0

    h, w = template_img.shape[:2]
    result = cv2.matchTemplate(screen, template_img, cv2.TM_CCOEFF_NORMED)

    # Find all locations above threshold
    locations = np.where(result >= confidence)
    points = list(zip(*locations[::-1]))  # (x, y) format

    # Remove duplicates (points too close to each other)
    filtered = []
    for pt in points:
        is_duplicate = False
        for existing in filtered:
            if abs(pt[0] - existing[0]) < w // 2 and abs(pt[1] - existing[1]) < h // 2:
                is_duplicate = True
                break
        if not is_duplicate:
            center_x = pt[0] + w // 2 + offset_x
            center_y = pt[1] + h // 2 + offset_y
            filtered.append((center_x, center_y))

    return filtered


def wait_image(template: str, timeout: float = 30, confidence: float = 0.9, interval: float = 0.5) -> Optional[Tuple[int, int]]:
    """
    Ждать появления изображения на экране.

    Args:
        template: Путь к изображению-шаблону
        timeout: Максимальное время ожидания (секунды)
        confidence: Порог совпадения
        interval: Интервал между проверками

    Returns:
        (x, y) центр найденного изображения или None при таймауте
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        result = find_image(template, confidence)
        if result:
            return result
        time.sleep(interval)

    return None


def wait_image_disappear(template: str, timeout: float = 30, confidence: float = 0.9, interval: float = 0.5) -> bool:
    """
    Ждать исчезновения изображения с экрана.

    Args:
        template: Путь к изображению-шаблону
        timeout: Максимальное время ожидания
        confidence: Порог совпадения
        interval: Интервал между проверками

    Returns:
        True если изображение исчезло, False при таймауте
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        result = find_image(template, confidence)
        if result is None:
            return True
        time.sleep(interval)

    return False
