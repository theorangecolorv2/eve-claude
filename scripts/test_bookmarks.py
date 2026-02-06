"""
Тест парсинга букмарков (локаций).
"""
import sys
import os
import logging
import time

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.sanderling.service import SanderlingService

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=== ТЕСТ ПАРСИНГА БУКМАРКОВ ===")
    
    # Запускаем Sanderling
    sanderling = SanderlingService()
    sanderling.start()
    
    try:
        # Ждем пока Sanderling прочитает данные
        logger.info("Ожидание чтения данных (3 секунды)...")
        time.sleep(3.0)
        
        # Получаем состояние
        state = sanderling.get_state()
        
        if not state:
            logger.error("Не удалось получить состояние")
            return
        
        # Проверяем букмарки
        logger.info(f"\n=== БУКМАРКИ ===")
        logger.info(f"Найдено букмарков: {len(state.bookmarks)}")
        
        if state.bookmarks:
            for i, bookmark in enumerate(state.bookmarks, 1):
                logger.info(f"\n--- Букмарк {i} ---")
                logger.info(f"Название: {bookmark.name}")
                logger.info(f"Центр: {bookmark.center}")
                logger.info(f"Границы: {bookmark.bounds}")
                if bookmark.hint:
                    logger.info(f"Подсказка: {bookmark.hint}")
        else:
            logger.warning("Букмарки не найдены")
            logger.info("Убедитесь что окно с букмарками открыто в игре")
        
        # Поиск конкретных букмарков
        logger.info("\n=== ПОИСК КОНКРЕТНЫХ БУКМАРКОВ ===")
        
        target_names = ['1 SPOT 1', '2 SPOT 2', '3 HOME 3']
        
        for target_name in target_names:
            found = False
            for bookmark in state.bookmarks:
                if target_name in bookmark.name:
                    logger.info(f"✓ Найден '{target_name}': center={bookmark.center}")
                    found = True
                    break
            
            if not found:
                logger.warning(f"✗ Не найден '{target_name}'")
        
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
