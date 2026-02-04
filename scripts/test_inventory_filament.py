"""
Тестовый скрипт для работы с инвентарем и филаментами через Sanderling
"""
import sys
import os
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time

def find_nodes_by_type(node, type_name, results=None):
    """Рекурсивно ищет узлы по типу"""
    if results is None:
        results = []
    
    if not isinstance(node, dict):
        return results
    
    # Если нашли нужный тип, добавляем ВЕСЬ узел (не только dictEntriesOfInterest)
    if node.get('pythonObjectTypeName') == type_name:
        results.append(node)
    
    # Поиск в children (может быть массивом)
    children = node.get('children', [])
    if isinstance(children, list):
        for child in children:
            find_nodes_by_type(child, type_name, results)
    
    # Также проверяем dictEntriesOfInterest.children
    dict_entries = node.get('dictEntriesOfInterest', {})
    if isinstance(dict_entries, dict):
        children_in_dict = dict_entries.get('children', {})
        if isinstance(children_in_dict, dict):
            entries = children_in_dict.get('listEntriesOfInterest', [])
            for entry in entries:
                find_nodes_by_type(entry, type_name, results)
    
    return results

def collect_all_nodes(node, all_nodes=None):
    """Собирает все узлы в плоский список"""
    if all_nodes is None:
        all_nodes = []
    
    if not isinstance(node, dict):
        return all_nodes
    
    # Добавляем dictEntriesOfInterest
    dict_entries = node.get('dictEntriesOfInterest', {})
    if dict_entries:
        all_nodes.append(dict_entries)
    
    # Рекурсия в children (массив)
    children = node.get('children', [])
    if isinstance(children, list):
        for child in children:
            collect_all_nodes(child, all_nodes)
    
    # Рекурсия в dictEntriesOfInterest.children.listEntriesOfInterest
    if isinstance(dict_entries, dict):
        children_in_dict = dict_entries.get('children', {})
        if isinstance(children_in_dict, dict):
            entries = children_in_dict.get('listEntriesOfInterest', [])
            for entry in entries:
                collect_all_nodes(entry, all_nodes)
    
    return all_nodes

def find_filter_text(node):
    """Рекурсивно ищет текст фильтра"""
    if not isinstance(node, dict):
        return None
    
    # Проверяем _setText в dictEntriesOfInterest
    dict_entries = node.get('dictEntriesOfInterest', {})
    text = dict_entries.get('_setText')
    if text:
        return text
    
    # Ищем в children (массив)
    children = node.get('children')
    if isinstance(children, list):
        for child in children:
            result = find_filter_text(child)
            if result:
                return result
    
    return None

def analyze_inventory(ui_tree):
    """Анализирует структуру инвентаря"""
    print("\n" + "="*80)
    print("АНАЛИЗ ИНВЕНТАРЯ")
    print("="*80)
    
    # Ищем InventoryPrimary
    inventory_primary = find_nodes_by_type(ui_tree, "InventoryPrimary")
    print(f"\n[InventoryPrimary] Найдено: {len(inventory_primary)}")
    if inventory_primary:
        inv_dict = inventory_primary[0].get('dictEntriesOfInterest', {})
        print(f"  Координаты: x={inv_dict.get('_displayX')}, y={inv_dict.get('_displayY')}")
        print(f"  Размер: w={inv_dict.get('_displayWidth')}, h={inv_dict.get('_displayHeight')}")
    
    # Ищем фильтры
    inv_filters = find_nodes_by_type(ui_tree, "InvFilters")
    print(f"\n[InvFilters] Найдено: {len(inv_filters)}")
    
    # Ищем FilterEntry
    filter_entries = find_nodes_by_type(ui_tree, "FilterEntry")
    print(f"\n[FilterEntry] Найдено: {len(filter_entries)}")
    
    for i, entry_node in enumerate(filter_entries):
        entry = entry_node.get('dictEntriesOfInterest', {})
        print(f"\n  Фильтр #{i+1}:")
        print(f"    Координаты: x={entry.get('_displayX')}, y={entry.get('_displayY')}")
        print(f"    Размер: w={entry.get('_displayWidth')}, h={entry.get('_displayHeight')}")
        
        # Ищем текст фильтра рекурсивно
        text = find_filter_text(entry_node)
        print(f"    DEBUG: find_filter_text вернул: {repr(text)}")
        if text:
            print(f"    Текст: {text}")
            if 'FILAMENT' in text:
                print(f"    [OK] НАЙДЕН ФИЛЬТР: {text}")
    
    return filter_entries

def analyze_items(ui_tree):
    """Анализирует предметы в инвентаре"""
    print("\n" + "="*80)
    print("АНАЛИЗ ПРЕДМЕТОВ")
    print("="*80)
    
    # Ищем TreeViewEntryInventory
    tree_entries = find_nodes_by_type(ui_tree, "TreeViewEntryInventory")
    print(f"\n[TreeViewEntryInventory] Найдено: {len(tree_entries)}")
    
    # Ищем TreeViewEntryInventoryCargo
    cargo_entries = find_nodes_by_type(ui_tree, "TreeViewEntryInventoryCargo")
    print(f"\n[TreeViewEntryInventoryCargo] Найдено: {len(cargo_entries)}")
    
    # Собираем все узлы
    all_nodes = collect_all_nodes(ui_tree)
    
    print(f"\n[Поиск филаментов по текстуре]")
    filament_nodes = []
    for node in all_nodes:
        texture = node.get('_texturePath', '')
        if 'abyssalFilament' in texture:
            filament_nodes.append(node)
            print(f"  [OK] Найдена текстура филамента: {texture}")
    
    print(f"\n[Поиск филаментов по тексту]")
    for node in all_nodes:
        text = node.get('_setText', '')
        if text and isinstance(text, str) and 'Filament' in text:
            print(f"  [OK] Найден текст: {text}")
            print(f"    Координаты: x={node.get('_displayX')}, y={node.get('_displayY')}")
            print(f"    Размер: w={node.get('_displayWidth')}, h={node.get('_displayHeight')}")
    
    return filament_nodes

def main():
    print("Анализ инвентаря из сохраненного снапшота...")
    
    # Читаем JSON файл
    json_file = "ui_tree_snapshot.json"
    if not os.path.exists(json_file):
        print(f"[ERROR] Файл {json_file} не найден. Сначала запустите: python scripts/save_json_snapshot.py")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        ui_tree = json.load(f)
    
    print(f"[OK] UI tree загружен из {json_file}")
    
    # Анализируем инвентарь
    filter_entries = analyze_inventory(ui_tree)
    
    # Анализируем предметы
    filament_nodes = analyze_items(ui_tree)
    
    print("\n" + "="*80)
    print("ИТОГИ")
    print("="*80)
    print(f"Фильтров найдено: {len(filter_entries)}")
    print(f"Филаментов найдено: {len(filament_nodes)}")
    
    # Ищем конкретно !FILAMENT! фильтр
    print("\n[Поиск фильтра !FILAMENT!]")
    filament_filter = None
    for entry_node in filter_entries:
        entry = entry_node.get('dictEntriesOfInterest', {})
        text = find_filter_text(entry_node)
        if text and '!FILAMENT!' in text:
            filament_filter = entry
            x = entry.get('_displayX', 0)
            y = entry.get('_displayY', 0)
            w = entry.get('_displayWidth', 0)
            h = entry.get('_displayHeight', 0)
            print(f"[OK] Фильтр !FILAMENT! найден!")
            print(f"  Текст: {text}")
            print(f"  Координаты: x={x}, y={y}")
            print(f"  Размер: w={w}, h={h}")
            print(f"  Координаты для клика: x={x + w//2}, y={y + h//2}")
            break
    
    if not filament_filter:
        print("[ERROR] Фильтр !FILAMENT! не найден")

if __name__ == "__main__":
    main()
