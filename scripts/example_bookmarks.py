"""
Пример использования модуля букмарков.
"""
import sys
import os
import logging
import time

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.sanderling.service import SanderlingService
from eve.bookmarks import (
    get_bookmarks,
    find_bookmark,
    click_bookmark,
    right_click_bookmark,
    double_click_bookmark,
    get_bookmark_coordinates
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=== ПРИМЕР РАБОТЫ С БУКМАРКАМИ ===")
    
    # Запускаем Sanderling
    sanderling = SanderlingService()
    sanderling.start()
    
    try:
        # Ждем пока Sanderling прочитает данные
        logger.info("Ожидание чтения данных...")
        time.sleep(3.0)
        
        # 1. Получить все букмарки
        logger.info("\n=== ВСЕ БУКМАРКИ ===")
        bookmarks = get_bookmarks(sanderling)
        for bookmark in bookmarks:
            logger.info(f"  - {bookmark.name} at {bookmark.center}")
        
        # 2. Найти конкретный букмарк
        logger.info("\n=== ПОИСК БУКМАРКА ===")
        spot1 = find_bookmark(sanderling, "1 SPOT 1")
        if spot1:
            logger.info(f"Найден: {spot1.name} at {spot1.center}")
        
        # 3. Получить координаты
        logger.info("\n=== КООРДИНАТЫ ===")
        coords = get_bookmark_coordinates(sanderling, "2 SPOT 2")
        if coords:
            logger.info(f"Координаты '2 SPOT 2': {coords}")
        
        # 4. Клик на букмарк (раскомментируйте для теста)
        # logger.info("\n=== КЛИК НА БУКМАРК ===")
        # click_bookmark(sanderling, "1 SPOT 1")
        # time.sleep(1.0)
        
        # 5. ПКМ на букмарк (раскомментируйте для теста)
        # logger.info("\n=== ПКМ НА БУКМАРК ===")
        # right_click_bookmark(sanderling, "3 HOME 3")
        # time.sleep(1.0)
        
        # 6. Двойной клик (раскомментируйте для теста)
        # logger.info("\n=== ДВОЙНОЙ КЛИК ===")
        # double_click_bookmark(sanderling, "1 SPOT 1")
        # time.sleep(1.0)
        
        logger.info("\n=== ГОТОВО ===")
        
    except KeyboardInterrupt:
        logger.info("Прервано пользователем")
    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
    finally:
        logger.info("Остановка Sanderling...")
        sanderling.stop()
        logger.info("Завершено")


if __name__ == "__main__":
    main()
