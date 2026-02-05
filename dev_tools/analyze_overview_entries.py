"""
Анализ overview entries из JSON дампа для поиска признаков врагов.
"""
import json
import sys
from pathlib import Path


def find_overview_entries(node, path="", depth=0):
    """Рекурсивно ищет overview entries в UI tree."""
    results = []
    
    if not isinstance(node, dict):
        return results
    
    # Проверяем тип объекта
    obj_type = node.get("pythonObjectTypeName", "")
    
    # Ищем OverviewEntry, OverviewScrollEntry или строки в списке
    if "entry" in obj_type.lower() and "overview" in obj_type.lower():
        results.append({
            "path": path,
            "type": obj_type,
            "data": node.get("dictEntriesOfInterest", {}),
            "depth": depth
        })
    
    # Также ищем ScrollEntry (строки в скролле)
    if "scrollentry" in obj_type.lower() or "listentry" in obj_type.lower():
        results.append({
            "path": path,
            "type": obj_type,
            "data": node.get("dictEntriesOfInterest", {}),
            "depth": depth
        })
    
    # Рекурсивно обходим детей
    children = node.get("children")
    if isinstance(children, list):
        for i, child in enumerate(children):
            results.extend(find_overview_entries(child, f"{path}/child[{i}]", depth+1))
    
    return results


def analyze_json_dump(filepath):
    """Анализирует JSON дамп."""
    print(f"Анализирую: {filepath}")
    
    with open(filepath, encoding='utf-8') as f:
        data = json.load(f)
    
    # Ищем overview entries
    entries = find_overview_entries(data)
    
    print(f"\nНайдено объектов: {len(entries)}")
    
    # Группируем по типам
    by_type = {}
    for entry in entries:
        t = entry['type']
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(entry)
    
    print(f"\nТипы объектов:")
    for t, items in by_type.items():
        print(f"  {t}: {len(items)}")
    
    # Выводим ScrollEntry и ListEntry (это скорее всего строки с целями)
    print(f"\n=== СТРОКИ OVERVIEW (ScrollEntry/ListEntry) ===")
    scroll_entries = [e for e in entries if "scroll" in e['type'].lower() or "list" in e['type'].lower()]
    
    for i, entry in enumerate(scroll_entries[:5]):
        print(f"\n--- Entry {i+1} ---")
        print(f"Type: {entry['type']}")
        print(f"Depth: {entry['depth']}")
        
        data = entry['data']
        print(f"Data keys: {list(data.keys())}")
        
        # Выводим все поля
        for key, value in data.items():
            if not key.startswith('_') or key in ['_setText', '_name', '_hint', '_texturePath', '_color']:
                print(f"  {key}: {value}")


if __name__ == "__main__":
    # Анализируем все JSON файлы в temp/
    temp_dir = Path("temp")
    json_files = list(temp_dir.glob("eve-online-memory-reading-*.json"))
    
    if not json_files:
        print("Нет JSON файлов в temp/")
        sys.exit(1)
    
    # Берём первый файл
    analyze_json_dump(json_files[0])
