"""
Тест поиска кнопки "Взять все".
"""
import logging
import time
from core.sanderling.service import SanderlingService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    logger.info("="*80)
    logger.info("ТЕСТ КНОПКИ 'ВЗЯТЬ ВСЕ'")
    logger.info("="*80)
    
    # Запустить Sanderling
    sanderling = SanderlingService()
    
    logger.info("Запускаю Sanderling...")
    if not sanderling.start():
        logger.error("Не удалось запустить Sanderling")
        return
    
    logger.info("Жду 3 секунды...")
    time.sleep(3.0)
    
    # Получить state
    logger.info("Получаю state...")
    state = sanderling.get_state()
    
    if not state:
        logger.error("Нет state")
        sanderling.stop()
        return
    
    logger.info("\n" + "="*80)
    logger.info("INVENTORY")
    logger.info("="*80)
    
    if not state.inventory:
        logger.warning("Inventory не открыт")
    else:
        logger.info(f"✓ Inventory открыт")
        logger.info(f"  Center: {state.inventory.center}")
        logger.info(f"  Bounds: {state.inventory.bounds}")
        logger.info(f"  Filters: {len(state.inventory.filters)}")
        logger.info(f"  Items: {len(state.inventory.items)}")
        
        if state.inventory.loot_all_button:
            logger.info(f"\n✓ Кнопка 'Взять все' найдена!")
            logger.info(f"  Координаты: {state.inventory.loot_all_button}")
        else:
            logger.warning("\n✗ Кнопка 'Взять все' НЕ найдена")
    
    logger.info("="*80)
    
    # Остановить Sanderling
    logger.info("\nОстанавливаю Sanderling...")
    sanderling.stop()
    
    logger.info("="*80)
    logger.info("ТЕСТ ЗАВЕРШЕН")
    logger.info("="*80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⚠ Прервано пользователем")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}", exc_info=True)
