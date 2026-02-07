"""
Скрипт для запуска Abyss Farmer бота.
"""
import sys
import os
import logging
from datetime import datetime

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.sanderling.service import SanderlingService
    from bots.abyss_farmer.main import AbyssFarmer
    from config import FILAMENT_NAMES
except Exception as e:
    print(f"ОШИБКА ИМПОРТА:")
    import traceback
    traceback.print_exc()
    sys.exit(1)


def setup_logging():
    """Настроить логирование в файл и консоль."""
    # Создаем директорию для логов если её нет
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Имя файла лога с датой и временем
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f'abyss_farmer_{timestamp}.log')
    
    # Настраиваем логирование - ВСЕ логи включая DEBUG
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Лог: {log_file}")
    
    return log_file


def main():
    """Точка входа."""
    print("="*60)
    print("ABYSS FARMER BOT")
    print("="*60)
    print()
    
    # Настраиваем логирование
    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Создаем сервис Sanderling
        logger.info("Инициализация Sanderling...")
        try:
            sanderling = SanderlingService()
            if not sanderling.start():
                logger.error("Не удалось запустить Sanderling service")
                return
        except Exception as e:
            logger.exception(f"Ошибка создания SanderlingService: {e}")
            return
        
        # Ждем пока сервис запустится
        import time
        logger.info("Ожидание первого чтения...")
        for i in range(10):
            time.sleep(1)
            try:
                state = sanderling.get_state()
                if state:
                    logger.info(f"Получен state на попытке {i+1}")
                    break
                else:
                    logger.debug(f"Попытка {i+1}: state = None")
            except Exception as e:
                logger.exception(f"Попытка {i+1}: Ошибка get_state: {e}")
        else:
            logger.error("Не удалось получить state за 10 попыток")
            return
        
        logger.info("Sanderling подключен")

        # Выбор филамента (до переключения окна)
        print("\nДоступные филаменты:")
        filaments = list(FILAMENT_NAMES.items())
        for i, (key, name) in enumerate(filaments, 1):
            print(f"{i}. {name}")

        choice = input(f"\nВыберите филамент (1-{len(filaments)}), Enter для Calm Exotic: ")

        filament_name = None
        if choice.strip():
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(filaments):
                    filament_name = filaments[idx][1]
            except ValueError:
                pass

        # Даем время переключить окно на EVE
        print("\nПереключитесь на окно EVE Online...")
        logger.info("Ожидание 3 секунды для переключения окна...")
        time.sleep(3)

        # Создаем и запускаем бота
        logger.info("Запуск бота...")
        bot = AbyssFarmer(sanderling, filament_name)
        bot.run()
        
    except KeyboardInterrupt:
        logger.info("Остановка по Ctrl+C")
    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")
    finally:
        print(f"\nЛог: {log_file}")


if __name__ == '__main__':
    main()
