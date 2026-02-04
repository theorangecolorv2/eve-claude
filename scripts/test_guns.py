"""
Тестовый скрипт для проверки детекта состояния пушек.
Выводит в консоль текущее состояние: ACTIVE или CALM.

Запуск: python scripts/test_guns.py
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mss
import numpy as np
import cv2

from shared.vision import find_image
from shared.eve.hud import HUDConfig


def list_monitors():
    """Показать список мониторов."""
    with mss.mss() as sct:
        print("\n=== МОНИТОРЫ ===")
        for i, m in enumerate(sct.monitors):
            print(f"  [{i}] {m}")
        print()
        return sct.monitors


def find_anchor_on_monitor(monitor_index: int = 1):
    """
    Найти anchor на конкретном мониторе.

    Args:
        monitor_index: 1 = первый монитор, 2 = второй, 0 = все мониторы
    """
    with mss.mss() as sct:
        monitor = sct.monitors[monitor_index]
        print(f"Ищу anchor на мониторе {monitor_index}: {monitor}")

        # Захватываем монитор
        img = sct.grab(monitor)
        screen = np.array(img)
        screen = cv2.cvtColor(screen, cv2.COLOR_BGRA2BGR)

        # Загружаем шаблон anchor
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "assets",
            HUDConfig.ANCHOR_TEMPLATE
        )
        template = cv2.imread(template_path)

        if template is None:
            print(f"ERROR: Не могу загрузить {template_path}")
            return None

        # Template matching
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        print(f"Match confidence: {max_val:.3f}")

        if max_val < 0.7:
            print("WARNING: Anchor не найден (confidence < 0.7)")
            return None

        # Координаты центра anchor (относительно монитора)
        h, w = template.shape[:2]
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2

        # Абсолютные координаты (с учётом позиции монитора)
        abs_x = monitor["left"] + center_x
        abs_y = monitor["top"] + center_y

        print(f"Anchor найден: относительно монитора ({center_x}, {center_y})")
        print(f"Anchor абсолютные координаты: ({abs_x}, {abs_y})")

        return (abs_x, abs_y)


def grab_gun_region(anchor_pos, gun_index=0):
    """Захватить регион пушки."""
    anchor_x, anchor_y = anchor_pos

    # Центр пушки
    gun_center_x = anchor_x + HUDConfig.GUN_OFFSET_X + (gun_index * HUDConfig.GUN_SPACING_X)
    gun_center_y = anchor_y + HUDConfig.GUN_OFFSET_Y

    # Регион
    half = HUDConfig.GUN_SIZE // 2
    region = {
        "left": gun_center_x - half,
        "top": gun_center_y - half,
        "width": HUDConfig.GUN_SIZE,
        "height": HUDConfig.GUN_SIZE
    }

    with mss.mss() as sct:
        img = sct.grab(region)
        return np.array(img)


def extract_green_mask(frame):
    """Выделить только зелёные пиксели."""
    # Конвертируем BGRA -> BGR если нужно
    if frame.shape[2] == 4:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

    # Конвертируем в HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Диапазон зелёного цвета в HSV
    lower_green = np.array([35, 50, 50])
    upper_green = np.array([85, 255, 255])

    # Маска зелёного
    mask = cv2.inRange(hsv, lower_green, upper_green)
    return mask


def get_diff_value(anchor_pos, gun_index=0, interval=0.25):
    """Получить значение diff для пушки."""
    frame1 = grab_gun_region(anchor_pos, gun_index)
    time.sleep(interval)
    frame2 = grab_gun_region(anchor_pos, gun_index)

    # Выделяем только зелёный
    green1 = extract_green_mask(frame1)
    green2 = extract_green_mask(frame2)

    # Сравниваем
    diff = cv2.absdiff(green1, green2)
    return np.sum(diff)


class SmoothDetector:
    """Детектор со скользящим средним."""

    def __init__(self, window_size=5, threshold=850):
        self.window_size = window_size
        self.threshold = threshold
        self.history = []

    def update(self, value):
        """Добавить новое значение и вернуть сглаженный результат."""
        self.history.append(value)
        if len(self.history) > self.window_size:
            self.history.pop(0)

        # Среднее по окну
        avg = sum(self.history) / len(self.history)
        # Максимум по окну (ловим пики)
        max_val = max(self.history)

        return avg, max_val

    def is_active(self, value):
        """Проверить активна ли пушка (с учётом истории)."""
        avg, max_val = self.update(value)
        # Активна если среднее выше порога ИЛИ был недавний пик
        return avg > self.threshold or max_val > self.threshold * 3


def main():
    print("=" * 50)
    print("ТЕСТ ДЕТЕКТА СОСТОЯНИЯ ПУШЕК")
    print("=" * 50)

    # Показываем мониторы
    monitors = list_monitors()

    # Ищем anchor на первом мониторе (monitor_index=1)
    # monitor[0] = все мониторы вместе
    # monitor[1] = первый монитор
    # monitor[2] = второй монитор

    monitor_index = 1  # Первый монитор где EVE

    print(f"Ищу anchor на мониторе {monitor_index}...")
    anchor = find_anchor_on_monitor(monitor_index)

    if not anchor:
        print("\nERROR: Anchor не найден! Убедись что EVE открыта и HUD виден.")
        return

    # Показываем позицию пушки
    gun_x = anchor[0] + HUDConfig.GUN_OFFSET_X
    gun_y = anchor[1] + HUDConfig.GUN_OFFSET_Y
    print(f"\nПозиция пушки 0: ({gun_x}, {gun_y})")
    print(f"Регион: {HUDConfig.GUN_SIZE}x{HUDConfig.GUN_SIZE} px")

    print("\n" + "=" * 50)
    print("МОНИТОРИНГ СОСТОЯНИЯ ПУШКИ (со сглаживанием)")
    print("Нажми Ctrl+C для выхода")
    print("=" * 50 + "\n")

    # Параметры
    check_interval = 0.1  # Как часто проверять (чаще для лучшего сглаживания)
    sample_interval = 0.15  # Интервал между кадрами для сравнения
    threshold = 850  # Порог различия
    window_size = 5  # Размер окна сглаживания

    detector = SmoothDetector(window_size=window_size, threshold=threshold)

    try:
        while True:
            diff_value = get_diff_value(anchor, gun_index=0, interval=sample_interval)
            avg, max_val = detector.update(diff_value)
            is_active = detector.is_active(diff_value)

            status = "ACTIVE (стреляет)" if is_active else "CALM (неактивна)"
            bar = "#" * min(50, int(avg / 200))

            print(f"\r[{time.strftime('%H:%M:%S')}] {status:20} | raw={diff_value:6.0f} avg={avg:6.0f} max={max_val:6.0f} | {bar}", end="", flush=True)

            time.sleep(check_interval)

    except KeyboardInterrupt:
        print("\n\nВыход.")


if __name__ == "__main__":
    main()
