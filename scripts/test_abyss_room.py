"""
Тест полного прохождения комнаты в абиссе.

Тестирует:
- Обработку контейнера (аппроч, атака, лут)
- Зачистку врагов (лок волнами, убийство)

Использование:
    python scripts/test_abyss_room.py
"""
import sys
import os
import logging
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.window import activate_window
from core.sanderling.service import SanderlingService
from bots.abyss_farmer.room import room

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Главная функция."""
    logger.info("=" * 60)
    logger.info("ТЕСТ ПРОХОЖДЕНИЯ КОМНАТЫ В АБИССЕ")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Этот скрипт протестирует:")
    logger.info("  1. Выпуск дронов")
    logger.info("  2. Поиск и обработку контейнера")
    logger.info("  3. Зачистку врагов волнами (до 5 за раз)")
    logger.info("  4. Возврат дронов")
    logger.info("")
    logger.info("ВАЖНО: Запускайте в абиссе, когда появились контейнер и враги!")
    logger.info("")
    
    input("Нажмите Enter для начала теста или Ctrl+C для отмены...")
    
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
        
        # Запуск теста
        logger.info("")
        logger.info("=" * 60)
        logger.info("НАЧАЛО ТЕСТА")
        logger.info("=" * 60)
        
        success = room(sanderling, timeout=300.0)
        
        logger.info("")
        logger.info("=" * 60)
        if success:
            logger.info("✓ ТЕСТ ПРОЙДЕН УСПЕШНО")
        else:
            logger.error("✗ ТЕСТ ПРОВАЛЕН")
        logger.info("=" * 60)
    
    except KeyboardInterrupt:
        logger.info("Тест остановлен пользователем")
    
    except Exception as e:
        logger.error(f"Ошибка в тесте: {e}", exc_info=True)
    
    finally:
        logger.info("Останавливаю Sanderling...")
        sanderling.stop()


if __name__ == "__main__":
    main()
