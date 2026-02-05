"""
Детальный анализ OverviewScrollEntry для поиска признаков врагов.
"""
import json
from pathlib import Path


def find_node_by_path(root, path_str):
    """Находит узел по пути типа '/child[0]/child[1]'."""
    node = root
    parts = [p for p in path_str.split('/') if p]
    
    for part in parts:
        if part.startswith('child[') and part.endswith(']'):
            idx = int(part[6:-1])
            children = node.get('children', [])
            if isinstance(children, list) and idx < len(children):
                node = children[idx]
            else:
                return None
        else:
            return None
    
    return node


def analyze_scroll_entry(entry, depth=0, max_depth=3):
    """Рекурсивно анализирует OverviewScrollEntry и его детей."""
    if depth > max_depth:
        return
    
    indent = "  " * depth
    obj_type = entry.get("pythonObjectTypeName", "")
    data = entry.get("dictEntriesOfInterest", {})
    
    print(f"{indent}[{obj_type}]")
    
    # Выводим интересные поля
    interesting_keys = ['_setText', '_name', '_hint', '_texturePath', 'texturePath', 
                       '_color', '_bgColor', 'iconNo', 'typeID', 'groupID', 'categoryID']
    
    for key in interesting_keys:
        if key in data:
            value = data[key]
            # Обрезаем длинные строки
            if isinstance(value, str) and len(value) > 100:
                value = value[:100] + "..."
            print(f"{indent}  {key}: {value}")
    
    # Рекурсивно обходим детей
    children = entry.get("children")
    if isinstance(children, list):
        for i, child in enumerate(children):
            if isinstance(child, dict):
                analyze_scroll_entry(child, depth+1, max_depth)


def main():
    temp_dir = Path("temp")
    json_files = list(temp_dir.glob("eve-online-memory-reading-*.json"))
    
    if not json_files:
        print("Нет JSON файлов в temp/")
        return
    
    filepath = json_files[0]
    print(f"Анализирую: {filepath}\n")
    
    with open(filepath, encoding='utf-8') as f:
        data = json.load(f)
    
    # Ищем OverviewScrollEntry
    def find_scroll_entries(node, path=""):
        results = []
        if not isinstance(node, dict):
            return results
        
        obj_type = node.get("pythonObjectTypeName", "")
        if obj_type == "OverviewScrollEntry":
            results.append((path, node))
        
        children = node.get("children")
        if isinstance(children, list):
            for i, child in enumerate(children):
                results.extend(find_scroll_entries(child, f"{path}/child[{i}]"))
        
        return results
    
    entries = find_scroll_entries(data)
    print(f"Найдено OverviewScrollEntry: {len(entries)}\n")
    
    # Анализируем первые 3 записи
    for i, (path, entry) in enumerate(entries[:3]):
        print(f"{'='*60}")
        print(f"ENTRY {i+1}")
        print(f"Path: {path}")
        print(f"{'='*60}")
        analyze_scroll_entry(entry, max_depth=4)
        print()


if __name__ == "__main__":
    main()
