"""
Тестовый скрипт для входа в Abyss.

Использование:
    python scripts/test_abyss_enter.py
"""
import sys
import logging
from pathlib import Path

# Добавляем корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.sanderling.service import SanderlingService
from bots.abyss_farmer.enter import enter_abyss
from config import FILAMENT_NAMES

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Тест входа в Abyss."""
    logger.info("=== ТЕСТ ВХОДА В ABYSS ===")
    
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
        
        # Войти в Abyss
        logger.info("Пытаюсь войти в Abyss...")
        success = enter_abyss(sanderling, filament_name=FILAMENT_NAMES['CALM_EXOTIC'])
        
        if success:
            logger.info("✅ УСПЕШНО ВОШЛИ В ABYSS!")
        else:
            logger.error("❌ НЕ УДАЛОСЬ ВОЙТИ В ABYSS")
    
    finally:
        logger.info("Останавливаю Sanderling...")
        sanderling.stop()
    
    logger.info("=== ТЕСТ ЗАВЕРШЕН ===")


if __name__ == "__main__":
    main()
