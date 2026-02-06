"""
Дамп предметов инвентаря
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
import time
from core.sanderling.service import SanderlingService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Дамп предметов инвентаря"""
    logger.info("="*80)
    logger.info("ДАМП ПРЕДМЕТОВ ИНВЕНТАРЯ")
    logger.info("="*80)
    
    # Инициализация Sanderling
    sanderling = SanderlingService()
    sanderling.start()
    time.sleep(2)
    
    state = sanderling.get_state()
    
    if not state or not state.inventory:
        logger.error("Инвентарь не открыт")
        return
    
    logger.info(f"Инвентарь открыт: {state.inventory.is_open}")
    logger.info(f"Найдено предметов: {len(state.inventory.items)}")
    logger.info("")
    
    for i, item in enumerate(state.inventory.items, 1):
        logger.info(f"#{i}:")
        logger.info(f"  Name: {item.name}")
        logger.info(f"  Hint: {item.hint}")
        logger.info(f"  Center: {item.center}")
        logger.info(f"  Bounds: {item.bounds}")
        logger.info(f"  Texture: {item.texture_path}")
        logger.info("")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⚠️ Прервано пользователем")
    except Exception as e:
        logger.exception(f"❌ Ошибка: {e}")
