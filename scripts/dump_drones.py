"""
Скрипт для дампа информации о дронах.
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


def search_drones_in_tree(node, path="root", depth=0, max_depth=10):
    """
    Рекурсивный поиск информации о дронах в UI tree.
    
    Args:
        node: Узел UI tree
        path: Путь к узлу
        depth: Текущая глубина
        max_depth: Максимальная глубина поиска
        
    Returns:
        Список найденных узлов с дронами
    """
    if depth > max_depth:
        return []
    
    results = []
    
    if not isinstance(node, dict):
        return results
    
    # Проверяем текущий узел
    node_type = node.get('pythonObjectTypeName', '')
    
    # Ищем упоминания дронов
    if any(keyword in node_type.lower() for keyword in ['drone', 'fighter']):
        results.append({
            'path': path,
            'type': node_type,
            'node': node,
            'depth': depth
        })
        logger.info(f"Найден узел с дронами на глубине {depth}: {path}")
        logger.info(f"  Type: {node_type}")
    
    # Проверяем dictEntriesOfInterest
    dict_entries = node.get('dictEntriesOfInterest', {})
    for key, value in dict_entries.items():
        if isinstance(value, str) and any(keyword in value.lower() for keyword in ['drone', 'fighter']):
            logger.info(f"Найдено упоминание дронов в {path}.{key}: {value}")
    
    # Рекурсивно проверяем дочерние узлы
    children = node.get('children', [])
    if children is None:
        children = []
    
    for i, child in enumerate(children):
        child_results = search_drones_in_tree(child, f"{path}/children[{i}]", depth + 1, max_depth)
        results.extend(child_results)
    
    return results


def main():
    """Главная функция."""
    logger.info("=== ДАМП ИНФОРМАЦИИ О ДРОНАХ ===")
    
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
        logger.info("Получаю UI tree...")
        ui_tree = sanderling.get_ui_tree()
        
        if not ui_tree:
            logger.error("Не удалось получить UI tree")
            return
        
        logger.info("UI tree получен\n")
        
        # Поиск информации о дронах
        logger.info("=" * 70)
        logger.info("ПОИСК ИНФОРМАЦИИ О ДРОНАХ В UI TREE")
        logger.info("=" * 70)
        
        drone_nodes = search_drones_in_tree(ui_tree, max_depth=15)
        
        if not drone_nodes:
            logger.warning("Информация о дронах не найдена в UI tree")
            logger.info("\nВозможные причины:")
            logger.info("1. Дроны не выпущены")
            logger.info("2. Окно дронов закрыто")
            logger.info("3. Нужно искать глубже или по другим ключевым словам")
        else:
            logger.info(f"\nНайдено узлов с дронами: {len(drone_nodes)}\n")
            
            # Детальный вывод каждого узла
            for i, result in enumerate(drone_nodes, 1):
                logger.info(f"Узел #{i}:")
                logger.info(f"  Path: {result['path']}")
                logger.info(f"  Type: {result['type']}")
                logger.info(f"  Depth: {result['depth']}")
                
                node = result['node']
                
                # Выводим dictEntriesOfInterest
                dict_entries = node.get('dictEntriesOfInterest', {})
                if dict_entries:
                    logger.info("  Dict Entries:")
                    for key, value in dict_entries.items():
                        logger.info(f"    {key}: {value}")
                
                # Выводим количество детей
                children_count = len(node.get('children', []))
                logger.info(f"  Children count: {children_count}")
                logger.info("")
        
        # Сохранение полного дампа
        logger.info("=" * 70)
        logger.info("СОХРАНЕНИЕ ДАМПА")
        logger.info("=" * 70)
        
        dump_file = f"temp/drones_dump_{time.strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("temp", exist_ok=True)
        
        dump_data = {
            "timestamp": time.time(),
            "drone_nodes_found": len(drone_nodes),
            "drone_nodes": [
                {
                    "path": r['path'],
                    "type": r['type'],
                    "depth": r['depth'],
                    "dict_entries": r['node'].get('dictEntriesOfInterest', {}),
                    "children_count": len(r['node'].get('children', []))
                }
                for r in drone_nodes
            ]
        }
        
        with open(dump_file, 'w', encoding='utf-8') as f:
            json.dump(dump_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Дамп сохранен: {dump_file}")
        
        # Также сохраним полный UI tree для анализа
        full_tree_file = f"temp/full_ui_tree_{time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(full_tree_file, 'w', encoding='utf-8') as f:
            json.dump(ui_tree, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Полный UI tree сохранен: {full_tree_file}")
        
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
