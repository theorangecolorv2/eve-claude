"""
Тестовый скрипт для проверки функции складывания предметов в стопки
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
import time
from core.sanderling.service import SanderlingService
from eve.inventory import InventoryManager
from config import FILAMENT_NAMES

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Тестирование функции use_filament с Stack All"""
    logger.info("="*80)
    logger.info("ТЕСТ: Использование филамента с автоматическим складыванием в стопки")
    logger.info("="*80)
    
    # Инициализация Sanderling
    sanderling = SanderlingService()
    sanderling.start()
    time.sleep(2)
    
    inventory = InventoryManager(sanderling)
    
    # Проверяем что инвентарь открыт
    if not inventory.is_open():
        logger.info("Открываю инвентарь...")
        if not inventory.open_inventory():
            logger.error("Не удалось открыть инвентарь")
            return
    
    logger.info("Инвентарь открыт")
    
    # Тестируем использование филамента
    # Функция теперь автоматически:
    # 1. Активирует фильтр !FILAMENT!
    # 2. Складывает все филаменты в стопки (Stack All)
    # 3. Использует филамент
    
    filament_name = FILAMENT_NAMES['CALM_EXOTIC']
    logger.info(f"Использую филамент: {filament_name}")
    
    if inventory.use_filament(filament_name):
        logger.info("✅ Филамент успешно использован!")
    else:
        logger.error("❌ Не удалось использовать филамент")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⚠️ Прервано пользователем")
    except Exception as e:
        logger.exception(f"❌ Ошибка: {e}")
