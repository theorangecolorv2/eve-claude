"""
Ручной запуск зачистки врагов.

Использует вкладку "PvP Foe" для фильтрации врагов.
Лочит и убивает волнами (до 5 за раз).

Использование:
    python scripts/test_clear_enemies.py
"""
import sys
import os
import logging
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.window import activate_window
from core.sanderling.service import SanderlingService
from eve.combat import launch_drones, recall_drones
from eve.overview_combat import clear_enemies

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Главная функция."""
    logger.info("=" * 60)
    logger.info("РУЧНАЯ ЗАЧИСТКА ВРАГОВ")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Этот скрипт:")
    logger.info("  1. Переключится на вкладку 'PvP Foe'")
    logger.info("  2. Выпустит дронов")
    logger.info("  3. Залочит до 5 врагов")
    logger.info("  4. Убьёт их (пушки + дроны)")
    logger.info("  5. Повторит пока есть враги")
    logger.info("  6. Вернёт дронов")
    logger.info("")
    logger.info("ВАЖНО: Убедитесь что у вас есть вкладка 'PvP Foe' в overview!")
    logger.info("")
    
    input("Нажмите Enter для начала или Ctrl+C для отмены...")
    
    # Активация окна EVE
    logger.info("Активирую окно EVE...")
    if not activate_window("EVE"):
        logger.error("Окно EVE не найдено! Убедитесь что игра запущена.")
        return
    
    # Запуск Sanderling
    logger.info("Запускаю Sanderling...")
    sanderling = SanderlingService()
    if not sanderling.start():
        logger.error("Не удалось запустить Sanderling")
        return
    
    try:
        # Прогрев
        logger.info("Жду 2 секунды для прогрева...")
        time.sleep(2)
        
        # Зачистка врагов (дроны выпустятся внутри clear_enemies)
        logger.info("")
        logger.info("=" * 60)
        logger.info("НАЧАЛО ЗАЧИСТКИ")
        logger.info("=" * 60)
        
        killed = clear_enemies(
            sanderling,
            guns_key="1",  # Ракеты
            drones_key="f",  # Дроны атакуют
            pvp_tab_name="PvP Foe",
            max_locks=5,
            max_waves=10,
            launch_drones_first=True  # Выпустить дронов автоматически
        )
        
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"ЗАЧИСТКА ЗАВЕРШЕНА: убито {killed} врагов")
        logger.info("=" * 60)
        
        # Возвращаем дронов
        logger.info("")
        logger.info("Возвращаю дронов...")
        recall_drones()
        time.sleep(2)
        
        logger.info("")
        logger.info("✓ ГОТОВО")
    
    except KeyboardInterrupt:
        logger.info("Зачистка остановлена пользователем")
    
    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
    
    finally:
        logger.info("Останавливаю Sanderling...")
        sanderling.stop()


if __name__ == "__main__":
    main()
