"""
Тест клика на букмарк.
"""
import sys
import os
import logging
import time

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.sanderling.service import SanderlingService
from eve.bookmarks import click_bookmark, right_click_bookmark

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=== ТЕСТ КЛИКА НА БУКМАРК ===")
    
    # Запускаем Sanderling
    sanderling = SanderlingService()
    sanderling.start()
    
    try:
        # Ждем пока Sanderling прочитает данные
        logger.info("Ожидание чтения данных...")
        time.sleep(3.0)
        
        # Тест ЛКМ
        logger.info("\n=== ТЕСТ ЛКМ НА '1 SPOT 1' ===")
        if click_bookmark(sanderling, "1 SPOT 1"):
            logger.info("✓ ЛКМ выполнен")
        else:
            logger.error("✗ ЛКМ не выполнен")
        
        time.sleep(2.0)
        
        # Тест ПКМ
        logger.info("\n=== ТЕСТ ПКМ НА '2 SPOT 2' ===")
        if right_click_bookmark(sanderling, "2 SPOT 2"):
            logger.info("✓ ПКМ выполнен")
        else:
            logger.error("✗ ПКМ не выполнен")
        
        time.sleep(2.0)
        
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
