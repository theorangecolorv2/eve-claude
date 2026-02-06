"""
Тестовый скрипт для проверки прохождения Abyss.
"""
import sys
import os
import logging
import time

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.sanderling.service import SanderlingService
from bots.abyss_farmer.main import run_abyss

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'logs/test_default_room_{time.strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Главная функция."""
    logger.info("=== ТЕСТ ABYSS БОТА ===")
    
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
        
        # Проверка подключения
        state = sanderling.get_state()
        if not state:
            logger.error("Не удалось получить состояние игры")
            return
        
        logger.info("Подключение к игре установлено")
        
        # Запуск прохождения Abyss (3 комнаты)
        success = run_abyss(sanderling, num_rooms=3)
        
        if success:
            logger.info("[OK] Abyss пройден успешно!")
        else:
            logger.error("[FAIL] Не удалось пройти Abyss")
        
    except KeyboardInterrupt:
        logger.info("Прервано пользователем")
    except Exception as e:
        logger.exception(f"Ошибка: {e}")
    finally:
        logger.info("Остановка Sanderling...")
        sanderling.stop()
        logger.info("Завершено")


if __name__ == "__main__":
    main()
