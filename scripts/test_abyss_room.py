"""
Тестовый скрипт для прохождения комнаты в Abyss.

Использование:
    python scripts/test_abyss_room.py
"""
import sys
import logging
from pathlib import Path

# Добавляем корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.sanderling.service import SanderlingService
from bots.abyss_farmer.room import room

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Тест прохождения комнаты в Abyss."""
    logger.info("=== ТЕСТ ПРОХОЖДЕНИЯ КОМНАТЫ ===")
    
    # Создать и запустить Sanderling
    sanderling = SanderlingService()
    
    logger.info("Запускаю Sanderling...")
    if not sanderling.start():
        logger.error("Не удалось запустить Sanderling")
        return
    
    try:
        # Подождать пока Sanderling прогреется
        import time
        logger.info("Жду 3 секунды для прогрева Sanderling...")
        time.sleep(3)
        
        # Пройти комнату
        logger.info("Начинаю прохождение комнаты...")
        success = room(sanderling, timeout=300.0)
        
        if success:
            logger.info("✅ КОМНАТА ПРОЙДЕНА УСПЕШНО!")
        else:
            logger.error("❌ НЕ УДАЛОСЬ ПРОЙТИ КОМНАТУ")
    
    except KeyboardInterrupt:
        logger.info("Прервано пользователем")
    
    finally:
        logger.info("Останавливаю Sanderling...")
        sanderling.stop()
    
    logger.info("=== ТЕСТ ЗАВЕРШЕН ===")


if __name__ == "__main__":
    main()
