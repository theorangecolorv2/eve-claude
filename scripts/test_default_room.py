"""
Тестовый скрипт для проверки прохождения default room.
"""
import sys
import os
import logging
import time

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.sanderling.service import SanderlingService
from bots.abyss_farmer.room_new import default_room
from bots.abyss_farmer.room_tessera import tessera_room
from bots.abyss_farmer.room_knight import knight_room
from bots.abyss_farmer.room_overmind import overmind_room
from bots.abyss_farmer.room_detector import detect_room_type

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
    logger.info("=== ТЕСТ DEFAULT ROOM ===")
    
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
        
        # Определение типа комнаты
        logger.info("Определение типа комнаты...")
        room_type = detect_room_type(sanderling, timeout=30.0)
        logger.info(f"Тип комнаты: {room_type.upper()}")
        
        # Запуск прохождения комнаты
        if room_type == "tessera":
            logger.info("Запуск прохождения комнаты Tessera...")
            success = tessera_room(sanderling, timeout=300.0)
        elif room_type == "knight":
            logger.info("Запуск прохождения комнаты Knight...")
            success = knight_room(sanderling, timeout=300.0)
        elif room_type == "overmind":
            logger.info("Запуск прохождения комнаты Overmind/Tyrannos...")
            success = overmind_room(sanderling, timeout=300.0)
        else:
            logger.info("Запуск прохождения стандартной комнаты...")
            success = default_room(sanderling, timeout=300.0)
        
        if success:
            logger.info("[OK] Комната пройдена успешно!")
        else:
            logger.error("[FAIL] Не удалось пройти комнату")
        
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
