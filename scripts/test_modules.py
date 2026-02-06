"""
Тест активации модулей в средних слотах.
"""
import logging
import time
import sys
from pathlib import Path

# Добавить корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.sanderling.service import SanderlingService
from eve.modules import ensure_mid_slots_active, activate_all_mid_slots

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_with_sanderling():
    """Тест с проверкой через Sanderling."""
    logger.info("="*80)
    logger.info("ТЕСТ АКТИВАЦИИ МОДУЛЕЙ (с Sanderling)")
    logger.info("="*80)
    
    # Запустить Sanderling
    sanderling = SanderlingService()
    
    logger.info("Запускаю Sanderling...")
    if not sanderling.start():
        logger.error("Не удалось запустить Sanderling")
        return
    
    logger.info("Жду 2 секунды...")
    time.sleep(2.0)
    
    # Получить состояние
    state = sanderling.get_state()
    
    if state and state.ship and state.ship.modules:
        mid_modules = [m for m in state.ship.modules if m.slot_type == 'mid']
        logger.info(f"\nНайдено модулей в средних слотах: {len(mid_modules)}")
        
        for i, module in enumerate(mid_modules, 1):
            status = "✓ АКТИВЕН" if module.is_active else "✗ НЕАКТИВЕН"
            logger.info(f"  {i}. {module.slot_name}: {status}")
    else:
        logger.warning("Не удалось получить данные о модулях")
    
    # Активировать модули
    logger.info("\n" + "="*80)
    logger.info("Активирую модули...")
    logger.info("="*80)
    
    result = ensure_mid_slots_active(
        left_key="2",
        right_key="3",
        sanderling_service=sanderling
    )
    
    if result:
        logger.info("✓ Модули активированы")
    else:
        logger.error("✗ Ошибка активации модулей")
    
    # Проверить результат
    logger.info("\nЖду 1 секунду...")
    time.sleep(1.0)
    
    state = sanderling.get_state()
    
    if state and state.ship and state.ship.modules:
        mid_modules = [m for m in state.ship.modules if m.slot_type == 'mid']
        logger.info(f"\nСостояние после активации:")
        
        for i, module in enumerate(mid_modules, 1):
            status = "✓ АКТИВЕН" if module.is_active else "✗ НЕАКТИВЕН"
            logger.info(f"  {i}. {module.slot_name}: {status}")
        
        active_count = sum(1 for m in mid_modules if m.is_active)
        logger.info(f"\nАктивных модулей: {active_count}/{len(mid_modules)}")
    
    # Остановить Sanderling
    logger.info("\nОстанавливаю Sanderling...")
    sanderling.stop()
    
    logger.info("="*80)
    logger.info("ТЕСТ ЗАВЕРШЕН")
    logger.info("="*80)


def test_blind():
    """Тест без Sanderling (вслепую)."""
    logger.info("="*80)
    logger.info("ТЕСТ АКТИВАЦИИ МОДУЛЕЙ (вслепую)")
    logger.info("="*80)
    
    logger.info("\nАктивирую все модули в средних слотах...")
    activate_all_mid_slots(["2", "3"])
    
    logger.info("✓ Модули активированы")
    logger.info("="*80)


def main():
    """Главная функция."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--blind":
        test_blind()
    else:
        test_with_sanderling()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⚠ Прервано пользователем")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}", exc_info=True)
