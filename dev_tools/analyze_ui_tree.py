#!/usr/bin/env python
"""Анализ UI tree из Sanderling для отладки парсера."""
import json
import sys
from collections import Counter
from pathlib import Path


def find_all_types(node, types_counter=None, depth=0, max_depth=100):
    """Рекурсивно найти все типы узлов в дереве."""
    if types_counter is None:
        types_counter = Counter()
    
    if depth > max_depth:
        return types_counter
    
    if not isinstance(node, dict):
        return types_counter
    
    # Подсчитать тип текущего узла
    node_type = node.get('pythonObjectTypeName')
    if node_type:
        types_counter[node_type] += 1
    
    # Рекурсивно обработать children
    children = node.get('children', [])
    if isinstance(children, list):
        for child in children:
            find_all_types(child, types_counter, depth + 1, max_depth)
    
    return types_counter


def find_nodes_by_type(node, target_type, results=None, depth=0, max_depth=100):
    """Найти все узлы определенного типа."""
    if results is None:
        results = []
    
    if depth > max_depth:
        return results
    
    if not isinstance(node, dict):
        return results
    
    # Проверить текущий узел
    if node.get('pythonObjectTypeName') == target_type:
        results.append(node)
    
    # Рекурсивно обработать children
    children = node.get('children', [])
    if isinstance(children, list):
        for child in children:
            find_nodes_by_type(child, target_type, results, depth + 1, max_depth)
    
    return results


def analyze_node(node, indent=0):
    """Вывести информацию об узле."""
    if not isinstance(node, dict):
        return
    
    node_type = node.get('pythonObjectTypeName', 'Unknown')
    dict_entries = node.get('dictEntriesOfInterest', {})
    
    print("  " * indent + f"Type: {node_type}")
    
    # Показать важные поля
    important_fields = ['_name', '_setText', '_displayX', '_displayY', '_displayWidth', '_displayHeight']
    for field in important_fields:
        if field in dict_entries:
            value = dict_entries[field]
            if isinstance(value, dict) and 'int_low32' in value:
                value = value['int_low32']
            print("  " * indent + f"  {field}: {value}")


def main():
    """Главная функция."""
    if len(sys.argv) < 2:
        # Найти последний JSON файл
        json_files = list(Path('.').glob('eve-online-memory-reading-*.json'))
        if not json_files:
            print("ERROR: No JSON files found")
            print("Usage: python dev_tools/analyze_ui_tree.py <json_file>")
            return
        json_file = max(json_files, key=lambda p: p.stat().st_mtime)
        print(f"Using latest file: {json_file}")
    else:
        json_file = sys.argv[1]
    
    print(f"\nAnalyzing: {json_file}")
    print("=" * 80)
    
    # Загрузить JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        ui_tree = json.load(f)
    
    print(f"\nRoot type: {ui_tree.get('pythonObjectTypeName')}")
    print(f"Root has children: {'children' in ui_tree}")
    
    # Подсчитать все типы
    print("\n" + "=" * 80)
    print("ALL NODE TYPES IN UI TREE:")
    print("=" * 80)
    types_counter = find_all_types(ui_tree)
    
    for node_type, count in types_counter.most_common(30):
        print(f"  {node_type:40} : {count:5} nodes")
    
    print(f"\nTotal unique types: {len(types_counter)}")
    print(f"Total nodes: {sum(types_counter.values())}")
    
    # Поиск специфичных типов для целей, overview, модулей
    print("\n" + "=" * 80)
    print("SEARCHING FOR GAME ELEMENTS:")
    print("=" * 80)
    
    # Targets
    target_types = ['TargetInBar', 'Target', 'SelectedItemView', 'SelectedItem']
    print("\n[TARGETS]")
    for target_type in target_types:
        nodes = find_nodes_by_type(ui_tree, target_type)
        print(f"  {target_type}: {len(nodes)} found")
        if nodes:
            print(f"    Example:")
            analyze_node(nodes[0], indent=2)
    
    # Overview
    overview_types = ['OverviewScrollEntry', 'OverviewEntry', 'OverView', 'OverviewWindow']
    print("\n[OVERVIEW]")
    for overview_type in overview_types:
        nodes = find_nodes_by_type(ui_tree, overview_type)
        print(f"  {overview_type}: {len(nodes)} found")
        if nodes:
            print(f"    Example:")
            analyze_node(nodes[0], indent=2)
    
    # Modules
    module_types = ['ShipSlot', 'ModuleButton', 'ShipModule', 'HudButton']
    print("\n[MODULES]")
    for module_type in module_types:
        nodes = find_nodes_by_type(ui_tree, module_type)
        print(f"  {module_type}: {len(nodes)} found")
        if nodes:
            print(f"    Example:")
            analyze_node(nodes[0], indent=2)
    
    # Поиск по ключевым словам в именах типов
    print("\n" + "=" * 80)
    print("TYPES CONTAINING KEYWORDS:")
    print("=" * 80)
    
    keywords = ['target', 'overview', 'slot', 'module', 'weapon', 'gun', 'ship', 'hud']
    for keyword in keywords:
        matching = [t for t in types_counter.keys() if keyword.lower() in t.lower()]
        if matching:
            print(f"\n'{keyword}':")
            for t in matching:
                print(f"  {t}: {types_counter[t]} nodes")


if __name__ == "__main__":
    main()
