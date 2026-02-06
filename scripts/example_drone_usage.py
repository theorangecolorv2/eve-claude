"""
Пример использования информации о дронах в боте.
"""
import sys
import time
import logging
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.sanderling.service import SanderlingService
from eve.keyboard import press_key, hold_key, release_key

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def launch_drones(sanderling: SanderlingService) -> bool:
    """
    Выпустить дроны, если они еще не в космосе.
    
    Args:
        sanderling: Сервис Sanderling
        
    Returns:
        True если дроны выпущены или уже в космосе
    """
    state = sanderling.get_state()
    
    if not state or not state.drones:
        logger.warning("Окно дронов не найдено")
        return False
    
    drones = state.drones
    
    if drones.in_space_count > 0:
        logger.info(f"Дроны уже в космосе: {drones.in_space_count}/{drones.max_drones}")
        return True
    
    logger.info("Выпускаю дроны (Shift+F)...")
    hold_key('shift')
    time.sleep(0.05)
    press_key('f')
    time.sleep(0.05)
    release_key('shift')
    
    # Ждем выпуска дронов
    time.sleep(2)
    
    # Проверяем результат
    state = sanderling.get_state()
    if state and state.drones:
        logger.info(f"Дроны выпущены: {state.drones.in_space_count}/{state.drones.max_drones}")
        return state.drones.in_space_count > 0
    
    return False


def attack_with_drones():
    """
    Атаковать цель дронами (F).
    """
    logger.info("Атакую дронами (F)...")
    press_key('f')


def check_drone_health(sanderling: SanderlingService) -> bool:
    """
    Проверить здоровье дронов.
    
    Args:
        sanderling: Сервис Sanderling
        
    Returns:
        True если все дроны здоровы (>50% HP)
    """
    state = sanderling.get_state()
    
    if not state or not state.drones:
        return True
    
    drones = state.drones
    
    if not drones.drones_in_space:
        return True
    
    damaged_drones = []
    
    for drone in drones.drones_in_space:
        # Считаем общее здоровье (среднее от щитов, брони и структуры)
        avg_health = (drone.shield + drone.armor + drone.hull) / 3.0
        
        if avg_health < 0.5:
            damaged_drones.append((drone.name, avg_health))
    
    if damaged_drones:
        logger.warning("Обнаружены поврежденные дроны:")
        for name, health in damaged_drones:
            logger.warning(f"  {name}: {health*100:.1f}% HP")
        return False
    
    return True


def check_drone_state(sanderling: SanderlingService) -> str:
    """
    Проверить состояние дронов.
    
    Args:
        sanderling: Сервис Sanderling
        
    Returns:
        "Idle", "Fighting", "Returning" или "Unknown"
    """
    state = sanderling.get_state()
    
    if not state or not state.drones or not state.drones.drones_in_space:
        return "Unknown"
    
    # Проверяем состояние первого дрона (обычно все дроны в одном состоянии)
    first_drone = state.drones.drones_in_space[0]
    return first_drone.state


def main():
    """Основная функция."""
    logger.info("Пример использования дронов...")
    
    # Инициализация Sanderling
    sanderling = SanderlingService()
    
    try:
        logger.info("Запуск Sanderling...")
        sanderling.start()
        
        # Ждем инициализации
        time.sleep(2)
        
        # Пример 1: Выпустить дроны
        if launch_drones(sanderling):
            logger.info("Дроны готовы к бою")
        
        time.sleep(1)
        
        # Пример 2: Проверить состояние дронов
        drone_state = check_drone_state(sanderling)
        logger.info(f"Состояние дронов: {drone_state}")
        
        # Пример 3: Атаковать дронами (если есть цель)
        if drone_state == "Idle":
            logger.info("Дроны бездействуют, можно атаковать")
            # attack_with_drones()  # Раскомментируйте для атаки
        
        # Пример 4: Проверить здоровье дронов
        if check_drone_health(sanderling):
            logger.info("Все дроны здоровы")
        else:
            logger.warning("Есть поврежденные дроны, возможно нужно вернуть их")
        
        logger.info("Пример завершен")
        
    except KeyboardInterrupt:
        logger.info("Прервано пользователем")
    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
    finally:
        logger.info("Остановка Sanderling...")
        sanderling.stop()
        logger.info("Завершено")


if __name__ == "__main__":
    main()
