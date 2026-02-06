"""
Детальный анализ структуры дронов в космосе.
"""
import sys
import os
import logging
import time
import json

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.sanderling.service import SanderlingService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def find_node_by_path(ui_tree, path_parts):
    """Найти узел по пути."""
    node = ui_tree
    for part in path_parts:
        if 'children[' in part:
            # Извлекаем индекс
            idx = int(part.split('[')[1].split(']')[0])
            children = node.get('children', [])
            if children and idx < len(children):
                node = children[idx]
            else:
                return None
        elif part != 'root':
            return None
    return node


def print_node_recursive(node, indent=0, max_depth=5, current_depth=0):
    """Рекурсивно выводит структуру узла."""
    if current_depth >= max_depth or not isinstance(node, dict):
        return
    
    prefix = "  " * indent
    node_type = node.get('pythonObjectTypeName', 'Unknown')
    
    logger.info(f"{prefix}Type: {node_type}")
    
    # Выводим интересные поля
    dict_entries = node.get('dictEntriesOfInterest', {})
    if dict_entries:
        for key, value in dict_entries.items():
            if key not in ['children', '_sr'] and not key.startswith('_'):
                logger.info(f"{prefix}  {key}: {value}")
    
    # Рекурсивно обрабатываем детей
    children = node.get('children', [])
    if children:
        logger.info(f"{prefix}  Children ({len(children)}):")
        for i, child in enumerate(children[:10]):  # Первые 10
            logger.info(f"{prefix}    [{i}]:")
            print_node_recursive(child, indent + 3, max_depth, current_depth + 1)


def main():
    """Главная функция."""
    logger.info("=== ДЕТАЛЬНЫЙ АНАЛИЗ ДРОНОВ ===")
    
    # Инициализация Sanderling
    sanderling = SanderlingService()
    
    try:
        # Запуск Sanderling
        logger.info("Запуск Sanderling...")
        if not sanderling.start():
            logger.error("Не удалось запустить Sanderling")
            return
        
        logger.info("Sanderling запущен")
        time.sleep(2.0)
        
        # Получение UI tree
        ui_tree = sanderling.get_ui_tree()
        
        if not ui_tree:
            logger.error("Не удалось получить UI tree")
            return
        
        logger.info("UI tree получен\n")
        
        # Анализ DroneGroupHeaderInSpace
        logger.info("=" * 70)
        logger.info("ЗАГОЛОВОК ДРОНОВ В КОСМОСЕ (DroneGroupHeaderInSpace)")
        logger.info("=" * 70)
        
        header_path = ['root', 'children[10]', 'children[1]', 'children[2]', 
                       'children[1]', 'children[1]', 'children[0]']
        header_node = find_node_by_path(ui_tree, header_path)
        
        if header_node:
            print_node_recursive(header_node, max_depth=3)
        else:
            logger.warning("Заголовок не найден")
        
        # Анализ первого дрона в космосе
        logger.info("\n" + "=" * 70)
        logger.info("ПЕРВЫЙ ДРОН В КОСМОСЕ (DroneInSpaceEntry #0)")
        logger.info("=" * 70)
        
        drone1_path = ['root', 'children[10]', 'children[1]', 'children[2]', 
                       'children[1]', 'children[1]', 'children[1]', 'children[0]',
                       'children[0]', 'children[0]', 'children[0]']
        drone1_node = find_node_by_path(ui_tree, drone1_path)
        
        if drone1_node:
            print_node_recursive(drone1_node, max_depth=4)
            
            # Сохраняем полную структуру первого дрона
            dump_file = f"temp/drone_entry_detailed_{time.strftime('%Y%m%d_%H%M%S')}.json"
            with open(dump_file, 'w', encoding='utf-8') as f:
                json.dump(drone1_node, f, indent=2, ensure_ascii=False)
            logger.info(f"\nПолная структура первого дрона сохранена: {dump_file}")
        else:
            logger.warning("Первый дрон не найден")
        
        # Анализ второго дрона в космосе
        logger.info("\n" + "=" * 70)
        logger.info("ВТОРОЙ ДРОН В КОСМОСЕ (DroneInSpaceEntry #1)")
        logger.info("=" * 70)
        
        drone2_path = ['root', 'children[10]', 'children[1]', 'children[2]', 
                       'children[1]', 'children[1]', 'children[1]', 'children[0]',
                       'children[0]', 'children[0]', 'children[1]']
        drone2_node = find_node_by_path(ui_tree, drone2_path)
        
        if drone2_node:
            print_node_recursive(drone2_node, max_depth=4)
        else:
            logger.warning("Второй дрон не найден")
        
    except KeyboardInterrupt:
        logger.info("\nПрервано пользователем")
    except Exception as e:
        logger.exception(f"Ошибка: {e}")
    finally:
        logger.info("\nОстановка Sanderling...")
        sanderling.stop()
        logger.info("Завершено")


if __name__ == "__main__":
    main()
