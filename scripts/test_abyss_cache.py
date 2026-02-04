"""
Тестовый скрипт для обработки контейнера (cache).

Использование:
    python scripts/test_abyss_cache.py
"""
import sys
import logging
from pathlib import Path

# Добавляем корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.sanderling.service import SanderlingService
from bots.abyss_farmer.cache import process_cache

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Тест обработки контейнера."""
    logger.info("=== ТЕСТ ОБРАБОТКИ КОНТЕЙНЕРА ===")
    
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
        
        # Обработать контейнер
        logger.info("Начинаю обработку контейнера...")
        logger.info("Параметры:")
        logger.info("  - Дистанция атаки: 30 км")
        logger.info("  - МВД: включен")
        logger.info("  - Дроны: выпущены")
        
        success = process_cache(
            sanderling,
            approach_timeout=120.0,
            kill_timeout=60.0,
            attack_distance_km=30.0,
            enable_mwd=True,
            launch_drones=True
        )
        
        if success:
            logger.info("✅ КОНТЕЙНЕР ОБРАБОТАН УСПЕШНО!")
        else:
            logger.error("❌ НЕ УДАЛОСЬ ОБРАБОТАТЬ КОНТЕЙНЕР")
    
    except KeyboardInterrupt:
        logger.info("Прервано пользователем")
    
    finally:
        logger.info("Останавливаю Sanderling...")
        sanderling.stop()
    
    logger.info("=== ТЕСТ ЗАВЕРШЕН ===")


if __name__ == "__main__":
    main()
