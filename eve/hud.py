"""
Eve Framework - HUD module (guns status detection)

Детекция активности пушек через поиск модуля и анализ анимации.
"""

import os
import time
import logging
from typing import Optional, Tuple
import numpy as np
import cv2
import mss

from eve.vision import find_image

logger = logging.getLogger(__name__)

# Флаг для debug-скриншота (один раз при старте)
_guns_debug_saved = False


# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

class HUDConfig:
    """Настройки детекции пушек."""

    # Шаблон модуля пушки
    GUN_TEMPLATE = "eve_gun_module.png"

    # Размер региона вокруг центра пушки для анализа
    GUN_REGION_SIZE = 54  # 54x54 px

    # Template matching confidence (ниже = более толерантно к изменениям патронов)
    GUN_CONFIDENCE = 0.65

    # Порог для определения анимации (изменения между кадрами)
    ANIMATION_THRESHOLD = 500


def _get_assets_path() -> str:
    """Получить путь к папке assets."""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")


# ============================================================================
# ПОИСК ПУШКИ
# ============================================================================

def find_gun() -> Optional[Tuple[int, int]]:
    """
    Найти модуль пушки на экране через template matching.

    Returns:
        (x, y) - центр модуля пушки, или None если не найден
    """
    template_path = os.path.join(_get_assets_path(), HUDConfig.GUN_TEMPLATE)

    coords = find_image(template_path, confidence=HUDConfig.GUN_CONFIDENCE)
    if coords:
        logger.debug(f"Пушка найдена: {coords}")
        return coords

    logger.warning("Модуль пушки не найден на экране")
    return None


def get_gun_region() -> Optional[Tuple[int, int, int, int]]:
    """
    Получить регион модуля пушки на экране.

    Returns:
        (x1, y1, x2, y2) - регион для анализа, или None
    """
    gun_center = find_gun()
    if not gun_center:
        return None

    cx, cy = gun_center
    half = HUDConfig.GUN_REGION_SIZE // 2

    region = (
        cx - half,
        cy - half,
        cx + half,
        cy + half
    )

    logger.debug(f"Gun region: {region}")
    return region


# ============================================================================
# АНАЛИЗ АНИМАЦИИ
# ============================================================================

def _grab_region(region: Tuple[int, int, int, int]) -> np.ndarray:
    """Захватить регион экрана как numpy array."""
    x1, y1, x2, y2 = region
    with mss.mss() as sct:
        monitor = {
            "left": x1,
            "top": y1,
            "width": x2 - x1,
            "height": y2 - y1
        }
        img = sct.grab(monitor)
        return np.array(img)


def _compare_frames(frame1: np.ndarray, frame2: np.ndarray) -> float:
    """
    Сравнить два кадра по общему изменению пикселей.

    Returns:
        Сумма абсолютных различий
    """
    # Конвертируем в grayscale для сравнения
    if len(frame1.shape) == 3:
        if frame1.shape[2] == 4:
            gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGRA2GRAY)
            gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGRA2GRAY)
        else:
            gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    else:
        gray1 = frame1
        gray2 = frame2

    # Сравниваем
    diff = cv2.absdiff(gray1, gray2)
    return np.sum(diff)


def _save_guns_debug(region: Tuple[int, int, int, int], frame1: np.ndarray, frame2: np.ndarray, diff: float) -> str:
    """
    Сохранить debug-скриншот пушек.

    Returns:
        Путь к сохранённому файлу
    """
    x1, y1, x2, y2 = region

    # Конвертируем кадры в BGR для отображения
    if len(frame1.shape) == 3 and frame1.shape[2] == 4:
        frame1_bgr = cv2.cvtColor(frame1, cv2.COLOR_BGRA2BGR)
        frame2_bgr = cv2.cvtColor(frame2, cv2.COLOR_BGRA2BGR)
    else:
        frame1_bgr = frame1.copy()
        frame2_bgr = frame2.copy()

    # Diff визуализация
    if len(frame1.shape) == 3:
        if frame1.shape[2] == 4:
            gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGRA2GRAY)
            gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGRA2GRAY)
        else:
            gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    else:
        gray1 = frame1
        gray2 = frame2

    diff_img = cv2.absdiff(gray1, gray2)
    diff_bgr = cv2.cvtColor(diff_img, cv2.COLOR_GRAY2BGR)

    # Увеличиваем для лучшей видимости (x3)
    scale = 3
    frame1_big = cv2.resize(frame1_bgr, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
    frame2_big = cv2.resize(frame2_bgr, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
    diff_big = cv2.resize(diff_bgr, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)

    # Собираем в одну картинку: 3 изображения в ряд
    combined = np.hstack([frame1_big, frame2_big, diff_big])

    # Добавляем текст
    is_active = diff > HUDConfig.ANIMATION_THRESHOLD
    status = "ACTIVE" if is_active else "CALM"
    color = (0, 255, 0) if is_active else (0, 0, 255)

    cv2.putText(combined, "Frame 1", (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(combined, "Frame 2", (frame1_big.shape[1] + 5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(combined, "Diff", (frame1_big.shape[1] * 2 + 5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Статус внизу
    h = combined.shape[0]
    cv2.putText(combined, f"Region: ({x1}, {y1}) - ({x2}, {y2})", (5, h - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(combined, f"Diff: {diff:.0f} (threshold: {HUDConfig.ANIMATION_THRESHOLD})", (5, h - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(combined, f"Status: {status}", (5, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # Сохраняем в inbox/
    inbox_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "inbox")
    os.makedirs(inbox_path, exist_ok=True)
    timestamp = time.strftime("%H%M%S")
    filename = f"debug_guns_{timestamp}.png"
    filepath = os.path.join(inbox_path, filename)

    cv2.imwrite(filepath, combined)
    logger.info(f"[DEBUG] Guns debug saved: {filepath}")
    return filepath


# ============================================================================
# ОСНОВНЫЕ ФУНКЦИИ
# ============================================================================

def is_gun_active(sample_interval: float = 0.25) -> bool:
    """
    Проверить активна ли пушка (идёт ли анимация).

    Делает 2 снимка с интервалом и сравнивает.
    Если картинка меняется = пушка активна (стреляет).
    Если статична = пушка спокойна (не стреляет).

    Args:
        sample_interval: Интервал между снимками (сек)

    Returns:
        True если пушка активна, False если спокойна
    """
    global _guns_debug_saved

    region = get_gun_region()
    if not region:
        logger.error("Не удалось найти регион пушки")
        return False

    # Первый снимок
    frame1 = _grab_region(region)

    # Ждём
    time.sleep(sample_interval)

    # Второй снимок
    frame2 = _grab_region(region)

    # Сравниваем
    diff = _compare_frames(frame1, frame2)

    is_active = diff > HUDConfig.ANIMATION_THRESHOLD
    logger.debug(f"Gun diff={diff}, threshold={HUDConfig.ANIMATION_THRESHOLD}, active={is_active}")

    # Debug-скриншот при первом вызове
    if not _guns_debug_saved:
        _save_guns_debug(region, frame1, frame2, diff)
        _guns_debug_saved = True

    return is_active


def are_guns_active() -> bool:
    """Проверить активны ли пушки (алиас для is_gun_active)."""
    return is_gun_active()


def are_guns_calm() -> bool:
    """Проверить что пушки неактивны (спокойны)."""
    return not is_gun_active()


def wait_guns_deactivate(
    timeout: float = 60,
    check_interval: float = 0.3,
    confirmation_checks: int = 2
) -> bool:
    """
    Ждать пока пушки деактивируются (цель умерла).

    Args:
        timeout: Максимальное ожидание (сек)
        check_interval: Интервал проверки
        confirmation_checks: Сколько раз подряд должно быть calm для подтверждения

    Returns:
        True если пушки деактивировались, False при таймауте
    """
    logger.info("Жду деактивации пушек...")

    start = time.time()
    calm_count = 0

    while time.time() - start < timeout:
        if not is_gun_active():
            calm_count += 1
            logger.debug(f"Calm detected ({calm_count}/{confirmation_checks})")

            if calm_count >= confirmation_checks:
                logger.info("Пушки деактивированы - цель мертва!")
                return True
        else:
            calm_count = 0  # Сброс если снова активна

        time.sleep(check_interval)

    logger.warning("Таймаут ожидания деактивации пушек")
    return False
