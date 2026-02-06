"""
Тест парсинга дронов из Sanderling.
"""
import sys
import time
import logging
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.sanderling.service import SanderlingService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def main():
    """Основная функция."""
    logger.info("Запуск теста парсинга дронов...")
    
    # Инициализация Sanderling
    sanderling = SanderlingService()
    
    try:
        logger.info("Запуск Sanderling...")
        sanderling.start()
        
        # Ждем инициализации
        time.sleep(2)
        
        logger.info("Получаю состояние игры...")
        state = sanderling.get_state()
        
        if not state:
            logger.error("Не удалось получить состояние игры")
            return
        
        if not state.drones:
            logger.warning("Окно дронов не найдено или закрыто")
            logger.info("Откройте окно дронов в игре и запустите скрипт снова")
            return
        
        drones = state.drones
        
        logger.info("=" * 60)
        logger.info("СОСТОЯНИЕ ДРОНОВ")
        logger.info("=" * 60)
        
        logger.info(f"Окно дронов открыто: {drones.window_open}")
        logger.info(f"Дронов в космосе: {drones.in_space_count}/{drones.max_drones}")
        logger.info("")
        
        if drones.drones_in_space:
            logger.info("ДРОНЫ В КОСМОСЕ:")
            logger.info("-" * 60)
            
            for i, drone in enumerate(drones.drones_in_space, 1):
                logger.info(f"{i}. {drone.name}")
                logger.info(f"   Состояние: {drone.state}")
                logger.info(f"   Здоровье:")
                logger.info(f"     Щиты:     {drone.shield*100:.1f}%")
                logger.info(f"     Броня:    {drone.armor*100:.1f}%")
                logger.info(f"     Структура: {drone.hull*100:.1f}%")
                logger.info(f"   Координаты: {drone.center}")
                logger.info("")
        else:
            logger.info("Нет дронов в космосе")
            logger.info("")
        
        if drones.drones_in_bay:
            logger.info("ДРОНЫ В ОТСЕКЕ:")
            logger.info("-" * 60)
            
            for i, drone in enumerate(drones.drones_in_bay, 1):
                logger.info(f"{i}. {drone.name}")
                logger.info(f"   Здоровье:")
                logger.info(f"     Щиты:     {drone.shield*100:.1f}%")
                logger.info(f"     Броня:    {drone.armor*100:.1f}%")
                logger.info(f"     Структура: {drone.hull*100:.1f}%")
                logger.info("")
        else:
            logger.info("Нет дронов в отсеке")
            logger.info("")
        
        logger.info("=" * 60)
        logger.info("Тест завершен успешно")
        
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
