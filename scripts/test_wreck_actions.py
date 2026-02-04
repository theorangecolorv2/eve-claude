"""
Тест действий с остовом (wreck).
Кликает по остову и показывает доступные действия.
"""
import logging
import time
from core.sanderling.service import SanderlingService
from eve.mouse import click

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    logger.info("="*80)
    logger.info("ТЕСТ ДЕЙСТВИЙ С ОСТОВОМ")
    logger.info("="*80)
    
    # Запустить Sanderling
    sanderling = SanderlingService()
    
    logger.info("Запускаю Sanderling...")
    if not sanderling.start():
        logger.error("Не удалось запустить Sanderling")
        return
    
    logger.info("Жду 3 секунды...")
    time.sleep(3.0)
    
    # Найти остов в overview
    logger.info("Ищу остов в overview...")
    state = sanderling.get_state()
    
    if not state or not state.overview:
        logger.error("Нет данных overview")
        sanderling.stop()
        return
    
    wreck = None
    for entry in state.overview:
        name_str = (entry.name or "").lower()
        type_str = (entry.type or "").lower()
        
        if 'остов' in name_str or 'wreck' in name_str or 'wreck' in type_str:
            wreck = entry
            logger.info(f"Найден остов: {entry.name}")
            logger.info(f"  Type: {entry.type}")
            logger.info(f"  Distance: {entry.distance}")
            logger.info(f"  Center: {entry.center}")
            break
    
    if not wreck:
        logger.error("Остов не найден в overview")
        sanderling.stop()
        return
    
    # Кликнуть по остову
    logger.info(f"\nКликаю по остову @ {wreck.center}...")
    click(wreck.center[0], wreck.center[1], duration=0.15)
    
    # Ждем обновления UI
    logger.info("Жду 1 секунду для обновления UI...")
    time.sleep(1.0)
    
    # Получить selected_actions
    logger.info("\nПолучаю selected_actions...")
    state = sanderling.get_state()
    
    if not state:
        logger.error("Нет state")
        sanderling.stop()
        return
    
    logger.info("\n" + "="*80)
    logger.info("SELECTED ACTIONS")
    logger.info("="*80)
    
    if not state.selected_actions:
        logger.warning("Нет доступных действий")
    else:
        logger.info(f"Найдено действий: {len(state.selected_actions)}\n")
        
        for i, action in enumerate(state.selected_actions, 1):
            logger.info(f"#{i}:")
            logger.info(f"  Name: {action.name}")
            logger.info(f"  Center: {action.center}")
            logger.info("")
    
    logger.info("="*80)
    
    # Найти кнопку "open_cargo" (Показать содержимое)
    open_cargo = next((a for a in state.selected_actions if a.name == 'open_cargo'), None)
    
    if not open_cargo:
        logger.error("Кнопка 'open_cargo' не найдена")
        sanderling.stop()
        return
    
    logger.info(f"\nКликаю 'open_cargo' @ {open_cargo.center}...")
    click(open_cargo.center[0], open_cargo.center[1], duration=0.15)
    
    # Ждем открытия окна лута
    logger.info("Жду 2 секунды для открытия окна лута...")
    time.sleep(2.0)
    
    # Получить обновленный state
    logger.info("\nПолучаю обновленный state...")
    state = sanderling.get_state()
    
    if not state:
        logger.error("Нет state")
        sanderling.stop()
        return
    
    # Проверить inventory window
    logger.info("\n" + "="*80)
    logger.info("INVENTORY WINDOW")
    logger.info("="*80)
    
    if not state.inventory:
        logger.warning("Inventory окно не открыто")
    else:
        logger.info(f"Caption: {state.inventory.caption}")
        logger.info(f"Type: {state.inventory.type}")
        
        # Проверить есть ли кнопка "Loot All" или "Взять все"
        logger.info("\nИщу кнопку 'Взять все'...")
        
        # Проверяем разные возможные атрибуты
        if hasattr(state.inventory, 'buttons'):
            logger.info(f"Найдено кнопок: {len(state.inventory.buttons)}")
            for btn in state.inventory.buttons:
                logger.info(f"  - {btn}")
        
        if hasattr(state.inventory, 'actions'):
            logger.info(f"Найдено actions: {len(state.inventory.actions)}")
            for action in state.inventory.actions:
                logger.info(f"  - {action}")
        
        # Выводим все атрибуты inventory
        logger.info("\nВсе атрибуты inventory:")
        for attr in dir(state.inventory):
            if not attr.startswith('_'):
                value = getattr(state.inventory, attr)
                if not callable(value):
                    logger.info(f"  {attr}: {value}")
    
    logger.info("="*80)
    
    # Остановить Sanderling
    logger.info("Останавливаю Sanderling...")
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
