#!/usr/bin/env python
"""Детальный анализ конкретных узлов."""
import json
import sys
from pathlib import Path


def find_nodes_by_type(node, target_type, results=None, depth=0, max_depth=100):
    """Найти все узлы определенного типа."""
    if results is None:
        results = []
    
    if depth > max_depth:
        return results
    
    if not isinstance(node, dict):
        return results
    
    if node.get('pythonObjectTypeName') == target_type:
        results.append(node)
    
    children = node.get('children', [])
    if isinstance(children, list):
        for child in children:
            find_nodes_by_type(child, target_type, results, depth + 1, max_depth)
    
    return results


def print_node_structure(node, indent=0, max_depth=3):
    """Вывести структуру узла."""
    if indent > max_depth or not isinstance(node, dict):
        return
    
    prefix = "  " * indent
    node_type = node.get('pythonObjectTypeName', 'Unknown')
    dict_entries = node.get('dictEntriesOfInterest', {})
    
    print(f"{prefix}[{node_type}]")
    
    # Показать все поля dictEntriesOfInterest
    for key, value in dict_entries.items():
        if key == 'children':
            continue
        
        # Обработать int_low32
        if isinstance(value, dict) and 'int_low32' in value:
            value = value['int_low32']
        
        # Ограничить длину строк
        if isinstance(value, str) and len(value) > 50:
            value = value[:50] + '...'
        
        print(f"{prefix}  {key}: {value}")
    
    # Рекурсивно показать children
    children = node.get('children', [])
    if isinstance(children, list) and children:
        print(f"{prefix}  children: [{len(children)} items]")
        for i, child in enumerate(children[:3]):  # Показать первые 3
            print_node_structure(child, indent + 2, max_depth)
        if len(children) > 3:
            print(f"{prefix}    ... and {len(children) - 3} more")


def main():
    """Главная функция."""
    # Найти последний JSON файл
    json_files = list(Path('.').glob('eve-online-memory-reading-*.json'))
    if not json_files:
        print("ERROR: No JSON files found")
        return
    json_file = max(json_files, key=lambda p: p.stat().st_mtime)
    
    print(f"Analyzing: {json_file}\n")
    
    # Загрузить JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        ui_tree = json.load(f)
    
    # Targets
    print("=" * 80)
    print("TARGETS (TargetInBar)")
    print("=" * 80)
    targets = find_nodes_by_type(ui_tree, 'TargetInBar')
    print(f"Found: {len(targets)}\n")
    for i, target in enumerate(targets, 1):
        print(f"\n--- Target #{i} ---")
        print_node_structure(target, max_depth=2)
    
    # Overview
    print("\n" + "=" * 80)
    print("OVERVIEW (OverviewScrollEntry)")
    print("=" * 80)
    overview = find_nodes_by_type(ui_tree, 'OverviewScrollEntry')
    print(f"Found: {len(overview)}\n")
    for i, entry in enumerate(overview[:3], 1):  # Показать первые 3
        print(f"\n--- Entry #{i} ---")
        print_node_structure(entry, max_depth=2)
    if len(overview) > 3:
        print(f"\n... and {len(overview) - 3} more entries")
    
    # Modules
    print("\n" + "=" * 80)
    print("MODULES (ShipSlot)")
    print("=" * 80)
    modules = find_nodes_by_type(ui_tree, 'ShipSlot')
    print(f"Found: {len(modules)}\n")
    for i, module in enumerate(modules[:3], 1):  # Показать первые 3
        print(f"\n--- Module #{i} ---")
        print_node_structure(module, max_depth=2)
    if len(modules) > 3:
        print(f"\n... and {len(modules) - 3} more modules")


if __name__ == "__main__":
    main()
