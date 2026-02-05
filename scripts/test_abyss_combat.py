"""
Тест боевой системы для абисса.

Проверяет:
- Переключение на вкладку PvP Foe
- Получение списка врагов
- Лок врагов
- Убийство врагов
"""
import sys
import os
import logging
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.window import activate_window
from core.sanderling.service import SanderlingService
from eve.overview_combat import switch_to_pvp_tab, get_all_enemies, lock_enemies_batch, clear_enemies
from eve.combat import launch_drones, recall_drones

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def test_switch_tab():
    """Тест переключения на вкладку PvP Foe."""
    logger.info("=== ТЕСТ: Переключение на вкладку PvP Foe ===")
    
    if not activate_window("EVE"):
        logger.error("Окно EVE не найдено")
        return False
    
    sanderling = SanderlingService()
    if not sanderling.start():
        logger.error("Не удалось запустить Sanderling")
        return False
    
    try:
        time.sleep(2)
        
        # Переключаемся на вкладку
        if switch_to_pvp_tab(sanderling, "PvP Foe"):
            logger.info("✓ Успешно переключились на вкладку PvP Foe")
            return True
        else:
            logger.error("✗ Не удалось переключиться на вкладку")
            return False
    
    finally:
        sanderling.stop()


def test_get_enemies():
    """Тест получения списка врагов."""
    logger.info("=== ТЕСТ: Получение списка врагов ===")
    
    if not activate_window("EVE"):
        logger.error("Окно EVE не найдено")
        return False
    
    sanderling = SanderlingService()
    if not sanderling.start():
        logger.error("Не удалось запустить Sanderling")
        return False
    
    try:
        time.sleep(2)
        
        # Переключаемся на вкладку
        if not switch_to_pvp_tab(sanderling, "PvP Foe"):
            logger.error("Не удалось переключиться на вкладку")
            return False
        
        time.sleep(1)
        
        # Получаем врагов
        enemies = get_all_enemies(sanderling)
        logger.info(f"Найдено врагов: {len(enemies)}")
        
        for i, enemy in enumerate(enemies, 1):
            logger.info(f"  {i}. {enemy.name} - {enemy.distance}")
        
        return True
    
    finally:
        sanderling.stop()


def test_lock_enemies():
    """Тест лока врагов."""
    logger.info("=== ТЕСТ: Лок врагов (пачкой до 5) ===")
    
    if not activate_window("EVE"):
        logger.error("Окно EVE не найдено")
        return False
    
    sanderling = SanderlingService()
    if not sanderling.start():
        logger.error("Не удалось запустить Sanderling")
        return False
    
    try:
        time.sleep(2)
        
        # Переключаемся на вкладку
        if not switch_to_pvp_tab(sanderling, "PvP Foe"):
            logger.error("Не удалось переключиться на вкладку")
            return False
        
        time.sleep(1)
        
        # Лочим врагов (до 5)
        locked = lock_enemies_batch(sanderling, max_locks=5)
        logger.info(f"Залочено врагов: {locked}")
        
        return locked > 0
    
    finally:
        sanderling.stop()


def test_full_combat():
    """Полный тест боевой системы."""
    logger.info("=== ТЕСТ: Полная боевая система ===")
    logger.info("ВНИМАНИЕ: Этот тест будет атаковать врагов!")
    logger.info("Убедитесь что вы в безопасной зоне (абисс или тестовая система)")
    
    input("Нажмите Enter для продолжения или Ctrl+C для отмены...")
    
    if not activate_window("EVE"):
        logger.error("Окно EVE не найдено")
        return False
    
    sanderling = SanderlingService()
    if not sanderling.start():
        logger.error("Не удалось запустить Sanderling")
        return False
    
    try:
        time.sleep(2)
        
        # Выпускаем дронов
        logger.info("Выпускаю дронов...")
        launch_drones()
        time.sleep(2)
        
        # Зачистка врагов
        killed = clear_enemies(
            sanderling,
            guns_key="2",
            drones_key="f",
            pvp_tab_name="PvP Foe"
        )
        
        logger.info(f"Убито врагов: {killed}")
        
        # Возвращаем дронов
        logger.info("Возвращаю дронов...")
        recall_drones()
        time.sleep(2)
        
        return killed > 0
    
    finally:
        sanderling.stop()


def main():
    """Главная функция."""
    logger.info("=" * 60)
    logger.info("ТЕСТ БОЕВОЙ СИСТЕМЫ ДЛЯ АБИССА")
    logger.info("=" * 60)
    
    tests = [
        ("Переключение на вкладку", test_switch_tab),
        ("Получение списка врагов", test_get_enemies),
        ("Лок врагов", test_lock_enemies),
    ]
    
    for name, test_func in tests:
        logger.info("")
        try:
            result = test_func()
            status = "✓ PASS" if result else "✗ FAIL"
            logger.info(f"{status}: {name}")
        except Exception as e:
            logger.error(f"✗ ERROR: {name} - {e}", exc_info=True)
        
        time.sleep(2)
    
    # Полный тест отдельно (опасный)
    logger.info("")
    logger.info("=" * 60)
    try:
        test_full_combat()
    except KeyboardInterrupt:
        logger.info("Полный тест отменён пользователем")
    except Exception as e:
        logger.error(f"Ошибка в полном тесте: {e}", exc_info=True)


if __name__ == "__main__":
    main()
