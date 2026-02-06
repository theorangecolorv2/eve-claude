"""
Дамп контекстного меню с орбитой.
Инструкция:
1. Запустить скрипт
2. ПКМ по цели в overview
3. Навести мышку на "выйти на орбиту" (чтобы появилось подменю)
4. Скрипт сохранит структуру меню
"""
import sys
import time
import json
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.sanderling.service import SanderlingService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    logger.info("Запуск дампа контекстного меню...")
    logger.info("ИНСТРУКЦИЯ:")
    logger.info("1. ПКМ по цели в overview")
    logger.info("2. Наведите мышку на 'выйти на орбиту'")
    logger.info("3. Подождите 2 секунды")
    logger.info("")
    logger.info("Ожидание 5 секунд для подготовки...")
    
    sanderling = SanderlingService()
    
    try:
        sanderling.start()
        time.sleep(2)
        
        # Ждем пока пользователь откроет меню
        time.sleep(5)
        
        logger.info("Получаю UI tree...")
        ui_tree = sanderling.get_ui_tree()
        
        if not ui_tree:
            logger.error("Не удалось получить UI tree")
            return
        
        # Сохраняем полный UI tree
        output_file = f"temp/orbit_menu_full_{time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(ui_tree, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Полный UI tree сохранен: {output_file}")
        
        # Парсим контекстное меню
        state = sanderling.get_state()
        
        if state and state.context_menu:
            logger.info("Контекстное меню найдено!")
            logger.info(f"Открыто: {state.context_menu.is_open}")
            logger.info(f"Пунктов меню: {len(state.context_menu.items)}")
            logger.info("")
            logger.info("Пункты меню:")
            for i, item in enumerate(state.context_menu.items, 1):
                logger.info(f"  {i}. {item.text}")
                logger.info(f"     Координаты: {item.center}")
        else:
            logger.warning("Контекстное меню не найдено в parsed state")
        
        # Ищем Menu и MenuEntry узлы вручную
        logger.info("")
        logger.info("Поиск Menu узлов...")
        
        def find_nodes(node, node_type, path="root", depth=0, max_depth=15):
            if depth > max_depth:
                return []
            
            results = []
            
            if isinstance(node, dict):
                if node.get('pythonObjectTypeName') == node_type:
                    results.append({
                        'path': path,
                        'node': node
                    })
                
                children = node.get('children', [])
                if isinstance(children, list):
                    for i, child in enumerate(children):
                        results.extend(find_nodes(child, node_type, f"{path}/children[{i}]", depth + 1, max_depth))
            
            return results
        
        # Ищем все Menu узлы
        menu_nodes = find_nodes(ui_tree, 'Menu')
        logger.info(f"Найдено Menu узлов: {len(menu_nodes)}")
        
        # Ищем все MenuEntry узлы
        menu_entry_nodes = find_nodes(ui_tree, 'MenuEntry')
        logger.info(f"Найдено MenuEntry узлов: {len(menu_entry_nodes)}")
        
        # Сохраняем найденные узлы
        if menu_nodes or menu_entry_nodes:
            menu_data = {
                'menu_nodes': [{'path': m['path'], 'node': m['node']} for m in menu_nodes],
                'menu_entry_nodes': [{'path': m['path'], 'node': m['node']} for m in menu_entry_nodes]
            }
            
            menu_file = f"temp/orbit_menu_parsed_{time.strftime('%Y%m%d_%H%M%S')}.json"
            with open(menu_file, 'w', encoding='utf-8') as f:
                json.dump(menu_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Данные меню сохранены: {menu_file}")
        
        logger.info("")
        logger.info("Готово!")
        
    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
    finally:
        sanderling.stop()


if __name__ == "__main__":
    main()
