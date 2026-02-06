"""
Скрипт для проверки доступных вкладок overview.
"""
import sys
import os
import logging
import time

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.sanderling.service import SanderlingService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Главная функция."""
    logger.info("=== ПРОВЕРКА ВКЛАДОК OVERVIEW ===")
    
    # Инициализация Sanderling
    sanderling = SanderlingService()
    
    try:
        # Запуск Sanderling
        logger.info("Запуск Sanderling...")
        if not sanderling.start():
            logger.error("Не удалось запустить Sanderling")
            return
        
        logger.info("Sanderling запущен")
        time.sleep(2.0)
        
        # Получение состояния
        state = sanderling.get_state()
        if not state:
            logger.error("Не удалось получить состояние игры")
            return
        
        logger.info("Подключение к игре установлено")
        
        # Проверка вкладок
        if not state.overview_tabs:
            logger.warning("Нет вкладок overview!")
            return
        
        logger.info(f"\nНайдено вкладок: {len(state.overview_tabs)}")
        logger.info("-" * 50)
        
        for i, tab in enumerate(state.overview_tabs, 1):
            logger.info(f"{i}. Label: '{tab.label}'")
            logger.info(f"   Center: {tab.center}")
            logger.info("")
        
        logger.info("-" * 50)
        logger.info("\nДля использования в коде:")
        logger.info("Доступные названия вкладок:")
        for tab in state.overview_tabs:
            logger.info(f"  - '{tab.label}'")
        
    except KeyboardInterrupt:
        logger.info("Прервано пользователем")
    except Exception as e:
        logger.exception(f"Ошибка: {e}")
    finally:
        logger.info("\nОстановка Sanderling...")
        sanderling.stop()
        logger.info("Завершено")


if __name__ == "__main__":
    main()
