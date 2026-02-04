#!/usr/bin/env python
"""Найти кнопки Neocom (боковая панель)."""
import json
from pathlib import Path

def find_neocom_buttons(node, path=[]):
    """Рекурсивно найти все кнопки Neocom."""
    results = []
    
    if not isinstance(node, dict):
        return results
    
    type_name = node.get('pythonObjectTypeName', '')
    
    # Ищем кнопки боковой панели
    if any(keyword in type_name for keyword in ['LeftSideButton', 'ButtonInventory', 'ButtonCargo', 'Neocom']):
        dict_entries = node.get('dictEntriesOfInterest', {})
        name = dict_entries.get('_name', 'N/A')
        x = dict_entries.get('_displayX', 0)
        y = dict_entries.get('_displayY', 0)
        width = dict_entries.get('_displayWidth', 0)
        height = dict_entries.get('_displayHeight', 0)
        
        results.append({
            'type': type_name,
            'name': name,
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'path_length': len(path)
        })
    
    # Рекурсия
    children = node.get('children', [])
    if isinstance(children, list):
        for child in children:
            results.extend(find_neocom_buttons(child, path + [node]))
    
    return results

def main():
    # Загрузить JSON
    json_file = Path('ui_tree_snapshot.json')
    if not json_file.exists():
        print("❌ ui_tree_snapshot.json не найден")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        ui_tree = json.load(f)
    
    # Найти кнопки
    buttons = find_neocom_buttons(ui_tree)
    
    print(f"\n{'='*80}")
    print(f"НАЙДЕНО КНОПОК NEOCOM: {len(buttons)}")
    print(f"{'='*80}\n")
    
    for btn in buttons:
        print(f"Type: {btn['type']}")
        print(f"  Name: {btn['name']}")
        print(f"  Position: ({btn['x']}, {btn['y']})")
        print(f"  Size: {btn['width']}x{btn['height']}")
        print(f"  Path depth: {btn['path_length']}")
        print()

if __name__ == '__main__':
    main()
