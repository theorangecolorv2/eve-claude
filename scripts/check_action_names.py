#!/usr/bin/env python
"""Проверить реальные имена кнопок действий."""
import json

with open('ui_tree_snapshot.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

buttons = []

def find(node):
    if isinstance(node, dict):
        if node.get('pythonObjectTypeName') == 'SelectedItemButton':
            name = node.get('dictEntriesOfInterest', {}).get('_name', 'N/A')
            buttons.append(name)
        
        children = node.get('children', [])
        if isinstance(children, list):
            for child in children:
                find(child)

find(data)

print("Найденные имена кнопок:")
for name in sorted(set(buttons)):
    if name != 'N/A':
        print(f"  {name}")
