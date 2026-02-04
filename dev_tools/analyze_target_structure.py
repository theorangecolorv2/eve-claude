#!/usr/bin/env python
"""Детальный анализ структуры целей и overview."""
import json
import sys
from pathlib import Path


def find_nodes_by_type(node, target_type, results=None, depth=0, max_depth=100):
    """Найти все узлы определенного типа."""
    if results is None:
        results = []
    if depth > max_depth or not isinstance(node, dict):
        return results
    if node.get('pythonObjectTypeName') == target_type:
        results.append(node)
    children = node.get('children', [])
    if isinstance(children, list):
        for child in children:
            find_nodes_by_type(child, target_type, results, depth + 1, max_depth)
    return results


def print_all_children(node, indent=0, max_depth=5):
    """Вывести все дочерние элементы."""
    if indent > max_depth or not isinstance(node, dict):
        return
    
    prefix = "  " * indent
    node_type = node.get('pythonObjectTypeName', 'Unknown')
    dict_entries = node.get('dictEntriesOfInterest', {})
    
    print(f"{prefix}[{node_type}]")
    
    # Показать важные поля
    important = ['_name', '_text', '_setText', '_hint', '_displayX', '_displayY']
    for key in important:
        if key in dict_entries:
            value = dict_entries[key]
            if isinstance(value, dict) and 'int_low32' in value:
                value = value['int_low32']
            if isinstance(value, str) and len(value) > 60:
                value = value[:60] + '...'
            print(f"{prefix}  {key}: {value}")
    
    # Рекурсивно показать children
    children = node.get('children', [])
    if isinstance(children, list) and children:
        for child in children:
            print_all_children(child, indent + 1, max_depth)


def main():
    """Главная функция."""
    json_files = list(Path('.').glob('eve-online-memory-reading-*.json'))
    if not json_files:
        print("ERROR: No JSON files found")
        return
    json_file = max(json_files, key=lambda p: p.stat().st_mtime)
    
    print(f"Analyzing: {json_file}\n")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        ui_tree = json.load(f)
    
    # Анализ целей
    print("=" * 80)
    print("TARGET STRUCTURE (TargetInBar)")
    print("=" * 80)
    targets = find_nodes_by_type(ui_tree, 'TargetInBar')
    if targets:
        print(f"\nFound {len(targets)} targets. Showing first one:\n")
        print_all_children(targets[0], max_depth=4)
    
    # Анализ overview
    print("\n" + "=" * 80)
    print("OVERVIEW STRUCTURE (OverviewScrollEntry)")
    print("=" * 80)
    overview = find_nodes_by_type(ui_tree, 'OverviewScrollEntry')
    if overview:
        print(f"\nFound {len(overview)} entries. Showing first one:\n")
        print_all_children(overview[0], max_depth=3)


if __name__ == "__main__":
    main()
