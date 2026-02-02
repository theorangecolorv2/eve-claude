"""
Eve Framework - Overview module

Работа с Overview в EVE Online:
- is_overview_empty() - проверка пустого Overview
- has_locked_targets() - есть ли залоченные цели
- count_targets() - подсчёт целей
- lock_all_targets() - залочить все цели (Ctrl+Click)
- kill_locked_targets() - убить залоченные цели
- lock_and_kill() - залочить и убить пачку
- clear_anomaly() - полная зачистка аномалии
"""

import os
import time
import logging
from typing import Optional, Tuple, Dict, List

import numpy as np
import cv2
import mss

from .vision import find_image

logger = logging.getLogger(__name__)

# Флаг для debug-скриншота (один раз при старте)
_overview_debug_saved = False


class OverviewDetectConfig:
    """Конфигурация overview."""

    # Шаблоны
    HEADER_NAME_TEMPLATE = "eve_overview_header_name.png"  # Заголовок "Название"
    EMPTY_TEMPLATE = "eve_overview_empty.png"  # "Ничего не найдено"
    LOCK_ANCHOR_TEMPLATE = "eve_lock_anchor.png"  # Анчор залоченной цели
    OVERVIEW_TITLE_TEMPLATE = "eve_overview_title.png"  # "Обзорная панель" для safe hover

    # Геометрия строк
    ROW_HEIGHT = 23  # Высота одной строки в пикселях
    HEADER_TO_FIRST_ROW = 26  # От центра заголовка до центра первой строки

    # Область проверки строки (относительно "Название")
    ROW_AREA_X_OFFSET = -70  # Смещение влево от "Название"
    ROW_AREA_WIDTH = 120  # Ширина области (захватывает иконку + часть текста)

    # Порог для детекта непустой строки
    NON_BLACK_THRESHOLD = 30  # Пиксель считается "не чёрным" если яркость > этого
    MIN_BRIGHT_PERCENT = 10.0  # Минимум % ярких пикселей для непустой строки

    # Максимум целей
    MAX_TARGETS = 7  # Максимум строк для проверки


def _get_assets_path() -> str:
    """Получить путь к папке assets."""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")


def _move_mouse_to_safe_area() -> bool:
    """
    Отвести мышку в безопасную зону (на заголовок "Обзорная панель").

    Это нужно чтобы тултип от наведения на цели не закрывал анкор "Название".

    Returns:
        True если успешно, False если не нашли заголовок
    """
    from .mouse import move_to

    template_path = os.path.join(_get_assets_path(), OverviewDetectConfig.OVERVIEW_TITLE_TEMPLATE)

    result = find_image(template_path, confidence=0.8)

    if result:
        logger.debug(f"Отвожу мышку на 'Обзорная панель': {result}")
        move_to(result[0], result[1], duration=0.15, humanize=True)  # Быстро но плавно
        return True

    logger.debug("'Обзорная панель' не найдена для safe hover")
    return False


def _save_overview_debug(header_pos: Tuple[int, int], rows_info: List[dict]) -> str:
    """
    Сохранить debug-скриншот overview с разметкой строк.

    Args:
        header_pos: Позиция заголовка (x, y)
        rows_info: Информация о строках [{index, bright_percent, is_occupied}, ...]

    Returns:
        Путь к сохранённому файлу
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
    occupied_count = 0
    for row in rows_info:
        row_idx = row["index"]
        is_occupied = row["is_occupied"]
        bright_pct = row["bright_percent"]

        if is_occupied:
            occupied_count += 1

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

    # Итог внизу
    cv2.putText(screenshot, f"Targets: {occupied_count}", (5, screenshot.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Сохраняем в inbox/
    inbox_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "inbox")
    os.makedirs(inbox_path, exist_ok=True)
    timestamp = time.strftime("%H%M%S")
    filename = f"debug_overview_{timestamp}.png"
    filepath = os.path.join(inbox_path, filename)

    cv2.imwrite(filepath, screenshot)
    logger.info(f"[DEBUG] Overview debug saved: {filepath}")
    return filepath


def is_overview_empty() -> bool:
    """
    Проверить пустой ли overview.

    Returns:
        True если overview пустой ("Ничего не найдено")
    """
    template_path = os.path.join(_get_assets_path(), OverviewDetectConfig.EMPTY_TEMPLATE)

    # Ищем надпись "Ничего не найдено"
    result = find_image(template_path, confidence=0.8)

    if result:
        logger.debug("Overview пустой - найдена надпись 'Ничего не найдено'")
        return True

    return False


def has_locked_targets() -> bool:
    """
    Проверить есть ли залоченные цели.

    Returns:
        True если есть хотя бы одна залоченная цель
    """
    template_path = os.path.join(_get_assets_path(), OverviewDetectConfig.LOCK_ANCHOR_TEMPLATE)

    result = find_image(template_path, confidence=0.8)

    if result:
        logger.debug("Есть залоченные цели (найден анчор лока)")
        return True

    logger.debug("Нет залоченных целей")
    return False


def find_header_position() -> Optional[Tuple[int, int]]:
    """
    Найти позицию заголовка "Название" в overview.

    Ищет только в ПРАВОЙ половине экрана (overview всегда справа,
    а "Название" может быть и на панели аномалий слева).

    Returns:
        (x, y) центра заголовка или None если не найден
    """
    template_path = os.path.join(_get_assets_path(), OverviewDetectConfig.HEADER_NAME_TEMPLATE)

    # Получаем размер экрана и ищем только в правой половине
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # Основной монитор
        screen_width = monitor["width"]
        screen_height = monitor["height"]

    # Правая половина экрана (от середины до правого края)
    right_half_region = (screen_width // 2, 0, screen_width, screen_height)

    result = find_image(template_path, confidence=0.8, region=right_half_region)

    if result:
        logger.debug(f"Заголовок 'Название' найден: {result}")
        return result

    logger.warning("Заголовок 'Название' не найден в правой части экрана")
    return None


def _grab_row_region(header_pos: Tuple[int, int], row_index: int) -> np.ndarray:
    """
    Захватить область строки overview.

    Args:
        header_pos: Позиция заголовка (x, y)
        row_index: Индекс строки (0 = первая)

    Returns:
        Изображение области строки
    """
    header_x, header_y = header_pos

    # Центр строки по Y
    row_center_y = header_y + OverviewDetectConfig.HEADER_TO_FIRST_ROW + (row_index * OverviewDetectConfig.ROW_HEIGHT)

    # Область строки
    region = {
        "left": header_x + OverviewDetectConfig.ROW_AREA_X_OFFSET,
        "top": row_center_y - OverviewDetectConfig.ROW_HEIGHT // 2,
        "width": OverviewDetectConfig.ROW_AREA_WIDTH,
        "height": OverviewDetectConfig.ROW_HEIGHT
    }

    with mss.mss() as sct:
        img = sct.grab(region)
        return np.array(img)


def _is_row_occupied(row_image: np.ndarray) -> Tuple[bool, float]:
    """
    Проверить занята ли строка (есть ли в ней цель).

    Args:
        row_image: Изображение области строки

    Returns:
        (is_occupied, bright_percent) - занята ли строка и % ярких пикселей
    """
    # Конвертируем в grayscale
    if len(row_image.shape) == 3:
        if row_image.shape[2] == 4:
            gray = cv2.cvtColor(row_image, cv2.COLOR_BGRA2GRAY)
        else:
            gray = cv2.cvtColor(row_image, cv2.COLOR_BGR2GRAY)
    else:
        gray = row_image

    # Считаем яркие пиксели (не чёрные)
    total_pixels = gray.size
    bright_pixels = np.sum(gray > OverviewDetectConfig.NON_BLACK_THRESHOLD)
    bright_percent = (bright_pixels / total_pixels) * 100

    is_occupied = bright_percent > OverviewDetectConfig.MIN_BRIGHT_PERCENT
    return is_occupied, bright_percent


def count_targets() -> int:
    """
    Подсчитать количество целей в overview.

    Returns:
        Количество целей (0 если overview пустой или ошибка)
    """
    global _overview_debug_saved

    # Отводим мышку чтобы тултип не закрывал анкоры
    _move_mouse_to_safe_area()

    # Сначала проверяем что overview не пустой
    if is_overview_empty():
        logger.debug("Overview пустой, целей нет")
        return 0

    # Ищем заголовок
    header_pos = find_header_position()
    if not header_pos:
        logger.error("Не удалось найти заголовок overview")
        return 0

    # Считаем занятые строки (собираем info для debug)
    target_count = 0
    rows_info = []

    for i in range(OverviewDetectConfig.MAX_TARGETS):
        row_image = _grab_row_region(header_pos, i)
        is_occupied, bright_percent = _is_row_occupied(row_image)

        rows_info.append({
            "index": i,
            "bright_percent": bright_percent,
            "is_occupied": is_occupied
        })

        if is_occupied:
            target_count += 1
        else:
            # Первая пустая строка = конец списка
            break

    logger.debug(f"Найдено целей: {target_count}")

    # Debug-скриншот при первом вызове если >= 2 целей
    if not _overview_debug_saved and target_count >= 2:
        _save_overview_debug(header_pos, rows_info)
        _overview_debug_saved = True

    return target_count


def get_row_position(header_pos: Tuple[int, int], row_index: int) -> Tuple[int, int]:
    """
    Получить координаты центра строки в overview.

    Args:
        header_pos: Позиция заголовка (x, y)
        row_index: Индекс строки (0 = первая)

    Returns:
        (x, y) центра строки
    """
    header_x, header_y = header_pos

    # X - середина области строки (там где текст названия)
    row_x = header_x

    # Y - центр строки
    row_y = header_y + OverviewDetectConfig.HEADER_TO_FIRST_ROW + (row_index * OverviewDetectConfig.ROW_HEIGHT)

    return (row_x, row_y)


def lock_all_targets() -> int:
    """
    Залочить все видимые цели через Ctrl+Click.

    Returns:
        Количество залоченных целей (0 если ошибка или пусто)
    """
    from .mouse import click, random_delay
    from .keyboard import key_down, key_up

    # Сначала считаем сколько целей
    target_count = count_targets()

    if target_count == 0:
        logger.info("Нет целей для лока")
        return 0

    # Ищем заголовок
    header_pos = find_header_position()
    if not header_pos:
        logger.error("Не найден заголовок overview")
        return 0

    logger.info(f"Лочу {target_count} целей...")

    # Зажимаем Ctrl
    key_down("ctrl")
    random_delay(0.15, 0.25)

    # Кликаем по каждой строке (с хуманизацией!)
    for i in range(target_count):
        row_x, row_y = get_row_position(header_pos, i)
        logger.debug(f"  Ctrl+Click по цели #{i+1}: ({row_x}, {row_y})")
        click(row_x, row_y)  # humanize=True по умолчанию
        random_delay(0.2, 0.4)  # Пауза между локами

    # Отпускаем Ctrl
    random_delay(0.1, 0.2)
    key_up("ctrl")

    # Отводим мышку чтобы тултип не закрывал анкор "Название"
    _move_mouse_to_safe_area()

    logger.info(f"Залочено {target_count} целей")
    return target_count


def kill_locked_targets(
    locked_count: int,
    guns_key: str = "2",
    check_interval: float = 1.0,
    kill_timeout: float = 60.0
) -> int:
    """
    Убить залоченные цели. Вызывать ПОСЛЕ lock_all_targets().

    Логика:
    1. Проверяем есть ли залоченные цели (анчор)
    2. Включаем пушки -> ждём активации -> ждём выключения (цель мертва)
    3. Повторяем пока есть залоченные цели (но не больше locked_count раз)

    Args:
        locked_count: Сколько целей залочено (максимум итераций)
        guns_key: Клавиша активации пушек
        check_interval: Интервал проверки статуса пушек (сек)
        kill_timeout: Таймаут на убийство ОДНОЙ цели (сек)

    Returns:
        Количество убитых целей
    """
    import time
    from .keyboard import press_key
    from .mouse import random_delay
    from .hud import are_guns_active

    if locked_count == 0:
        logger.info("Нет залоченных целей")
        return 0

    # Проверяем есть ли вообще залоченные цели
    if not has_locked_targets():
        logger.warning("Анчор лока не найден - нет залоченных целей")
        return 0

    logger.info(f"=== Убиваю до {locked_count} залоченных целей ===")
    killed = 0

    for i in range(locked_count):
        # Проверяем есть ли ещё залоченные цели
        if not has_locked_targets():
            logger.info(f"Лок пустой после {killed} убийств")
            break

        logger.info(f"--- Цель {i+1}/{locked_count} (убито: {killed}) ---")

        # Включаем пушки
        logger.debug(f"Нажимаю '{guns_key}' для активации пушек...")
        press_key(guns_key)

        # Ждём активации пушек (1-2 сек)
        random_delay(1.0, 2.0)

        # Проверяем что пушки активировались
        if not are_guns_active():
            logger.warning("Пушки не активировались - проверяю лок...")
            if not has_locked_targets():
                logger.info("Лок пустой - все цели убиты")
                break
            else:
                logger.warning("Лок есть, но пушки не стреляют - пробую ещё раз")
                continue

        logger.debug("Пушки активны, жду смерти цели...")

        # Ждём пока пушки не выключатся (цель мертва)
        start_time = time.time()
        while time.time() - start_time < kill_timeout:
            if not are_guns_active():
                elapsed = time.time() - start_time
                logger.info(f"Цель {i+1} убита за {elapsed:.1f}с")
                killed += 1
                break
            time.sleep(check_interval)
        else:
            logger.warning(f"Таймаут {kill_timeout}с на цель {i+1}")
            break

        # Пауза перед следующей целью
        random_delay(0.3, 0.6)

    logger.info(f"=== Убито {killed} целей ===")
    return killed


def clear_anomaly(
    guns_key: str = "2",
    check_interval: float = 1.0,
    kill_timeout: float = 60.0,
    max_waves: int = 10
) -> int:
    """
    Зачистить аномалию - лочить и убивать пока overview не пустой.

    Args:
        guns_key: Клавиша активации пушек
        check_interval: Интервал проверки пушек
        kill_timeout: Таймаут на одну цель
        max_waves: Максимум волн (защита от зацикливания)

    Returns:
        Общее количество убитых целей
    """
    from .mouse import random_delay

    logger.info("=== ЗАЧИСТКА АНОМАЛИИ ===")
    total_killed = 0
    wave = 0

    while wave < max_waves:
        wave += 1

        # Проверяем есть ли цели в overview
        if is_overview_empty():
            logger.info(f"Overview пустой - аномалия зачищена! Всего убито: {total_killed}")
            return total_killed

        target_count = count_targets()
        if target_count == 0:
            logger.info(f"Нет целей - аномалия зачищена! Всего убито: {total_killed}")
            return total_killed

        logger.info(f"--- Волна {wave}: {target_count} целей ---")

        # Лочим и убиваем
        killed = lock_and_kill(guns_key, check_interval, kill_timeout)
        total_killed += killed

        logger.info(f"Волна {wave} завершена: убито {killed}, всего {total_killed}")

        # Пауза между волнами (ждём респавн или проверяем)
        random_delay(1.0, 2.0)

    logger.warning(f"Достигнут лимит волн ({max_waves}). Убито: {total_killed}")
    return total_killed


def lock_and_kill(guns_key: str = "2", check_interval: float = 1.0, kill_timeout: float = 60.0) -> int:
    """
    Залочить все видимые цели и убить их.

    Args:
        guns_key: Клавиша активации пушек
        check_interval: Интервал проверки пушек
        kill_timeout: Таймаут на одну цель

    Returns:
        Количество убитых целей
    """
    from .mouse import random_delay

    # Лочим цели
    locked = lock_all_targets()

    if locked == 0:
        return 0

    # Пауза после лока (цели не сразу лочатся в игре)
    random_delay(2.0, 2.5)

    # Убиваем
    return kill_locked_targets(locked, guns_key, check_interval, kill_timeout)


def count_targets_detailed() -> dict:
    """
    Подсчитать цели с детальной информацией (для отладки).

    Returns:
        dict с полями:
            - count: количество целей
            - header_pos: позиция заголовка
            - rows: список (row_index, bright_pixels, is_occupied)
    """
    result = {
        "count": 0,
        "header_pos": None,
        "rows": [],
        "is_empty": False
    }

    # Отводим мышку чтобы тултип не закрывал анкоры
    _move_mouse_to_safe_area()

    # Проверка пустоты
    if is_overview_empty():
        result["is_empty"] = True
        return result

    # Ищем заголовок
    header_pos = find_header_position()
    if not header_pos:
        return result

    result["header_pos"] = header_pos

    # Анализируем строки
    for i in range(OverviewDetectConfig.MAX_TARGETS):
        row_image = _grab_row_region(header_pos, i)
        is_occupied, bright_percent = _is_row_occupied(row_image)

        result["rows"].append({
            "index": i,
            "bright_percent": bright_percent,
            "is_occupied": is_occupied
        })

        if is_occupied:
            result["count"] += 1
        else:
            # Первая пустая строка = конец списка
            break

    return result
