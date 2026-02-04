"""
Тестовый скрипт для проверки детекта целей в overview.
Выводит в консоль количество целей в реальном времени.
При 2+ целях сохраняет отладочный скриншот с разметкой строк.

Запуск: python scripts/test_overview.py
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import cv2
import mss

from shared.eve.overview import (
    OverviewDetectConfig,
    is_overview_empty,
    find_header_position,
    count_targets,
    count_targets_detailed
)


def save_debug_screenshot(header_pos, rows_info):
    """
    Сохранить отладочный скриншот с разметкой строк overview.

    Args:
        header_pos: Позиция заголовка (x, y)
        rows_info: Информация о строках из count_targets_detailed
    """
    header_x, header_y = header_pos

    # Определяем область для захвата (overview + немного вокруг)
    margin = 50
    region_left = header_x + OverviewDetectConfig.ROW_AREA_X_OFFSET - margin
    region_top = header_y - margin
    region_width = 400
    region_height = margin + OverviewDetectConfig.HEADER_TO_FIRST_ROW + (OverviewDetectConfig.MAX_TARGETS * OverviewDetectConfig.ROW_HEIGHT) + margin

    region = {
        "left": region_left,
        "top": region_top,
        "width": region_width,
        "height": region_height
    }

    with mss.mss() as sct:
        img = sct.grab(region)
        screenshot = np.array(img)
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)

    # Рисуем разметку
    # Позиция заголовка относительно скриншота
    rel_header_x = header_x - region_left
    rel_header_y = header_y - region_top

    # Крестик на заголовке (anchor)
    cv2.drawMarker(screenshot, (rel_header_x, rel_header_y), (0, 255, 255), cv2.MARKER_CROSS, 20, 2)
    cv2.putText(screenshot, "ANCHOR", (rel_header_x + 10, rel_header_y - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

    # Рисуем строки
    for row in rows_info:
        row_idx = row["index"]
        is_occupied = row["is_occupied"]
        bright_pct = row["bright_percent"]

        # Центр строки
        row_center_y = rel_header_y + OverviewDetectConfig.HEADER_TO_FIRST_ROW + (row_idx * OverviewDetectConfig.ROW_HEIGHT)

        # Область строки
        row_left = rel_header_x + OverviewDetectConfig.ROW_AREA_X_OFFSET
        row_top = row_center_y - OverviewDetectConfig.ROW_HEIGHT // 2
        row_right = row_left + OverviewDetectConfig.ROW_AREA_WIDTH
        row_bottom = row_top + OverviewDetectConfig.ROW_HEIGHT

        # Цвет: зелёный если занята, красный если пустая
        color = (0, 255, 0) if is_occupied else (0, 0, 255)

        # Прямоугольник области строки
        cv2.rectangle(screenshot, (row_left, row_top), (row_right, row_bottom), color, 2)

        # Номер строки и процент
        label = f"R{row_idx}: {bright_pct:.1f}%"
        cv2.putText(screenshot, label, (row_right + 5, row_center_y + 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

    # Сохраняем
    inbox_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "inbox")
    timestamp = time.strftime("%H%M%S")
    filename = f"debug_overview_{timestamp}.png"
    filepath = os.path.join(inbox_path, filename)

    cv2.imwrite(filepath, screenshot)
    return filepath


def main():
    print("=" * 60)
    print("ТЕСТ ДЕТЕКТА ЦЕЛЕЙ В OVERVIEW")
    print("=" * 60)

    print(f"\nВысота строки: {OverviewDetectConfig.ROW_HEIGHT}px")
    print(f"Порог яркости: {OverviewDetectConfig.NON_BLACK_THRESHOLD}")
    print(f"Мин. ярких %: {OverviewDetectConfig.MIN_BRIGHT_PERCENT}%")

    # Сначала проверим что находим заголовок
    print("\n--- Поиск заголовка 'Название' ---")
    header_pos = find_header_position()

    if not header_pos:
        print("ERROR: Заголовок не найден!")
        print("Убедись что:")
        print("  1. EVE открыта на первом мониторе")
        print("  2. Overview виден")
        print("  3. Колонка 'Название' видна")
        return

    print(f"Заголовок найден: {header_pos}")

    print("\n" + "=" * 60)
    print("МОНИТОРИНГ ЦЕЛЕЙ")
    print("При 2+ целях сохраняю отладочный скриншот в inbox/")
    print("Нажми Ctrl+C для выхода")
    print("=" * 60 + "\n")

    debug_saved = False  # Флаг чтобы не спамить скриншотами

    try:
        while True:
            # Получаем детальную информацию
            info = count_targets_detailed()

            if info["is_empty"]:
                status = "OVERVIEW ПУСТОЙ"
                count = 0
                details = "Ничего не найдено"
                debug_saved = False  # Сбрасываем флаг
            else:
                count = info["count"]
                status = f"ЦЕЛЕЙ: {count}"

                # Формируем детали по строкам
                row_details = []
                for row in info["rows"]:
                    mark = "+" if row["is_occupied"] else "-"
                    row_details.append(f"{mark}{row['bright_percent']:5.1f}%")
                details = " | ".join(row_details)

                # Сохраняем отладочный скриншот при 2+ целях (один раз)
                if count >= 2 and not debug_saved and info["header_pos"]:
                    filepath = save_debug_screenshot(info["header_pos"], info["rows"])
                    print(f"\n[DEBUG] Сохранён скриншот: {filepath}")
                    debug_saved = True

            # Визуализация
            bar = "#" * count + "." * (6 - count)

            print(f"\r[{time.strftime('%H:%M:%S')}] {status:15} [{bar}] | {details}", end="", flush=True)

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\nВыход.")


if __name__ == "__main__":
    main()
