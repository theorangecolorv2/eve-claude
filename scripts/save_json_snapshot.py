#!/usr/bin/env python
"""Сохранить один JSON снимок для анализа."""
import sys
import os
import subprocess
import json
import re
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    """Сохранить JSON снимок."""
    print("Running Sanderling to capture UI tree...")
    
    # Запустить Sanderling
    cmd = [
        "external/sanderling-bin/read-memory-64-bit.exe",
        "read-memory-eve-online",
        "--pid=13132",
        "--root-address=0x276A59E2CF8",
        "--remove-other-dict-entries"
    ]
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=10.0
    )
    
    if result.returncode != 0:
        print(f"ERROR: Sanderling failed with exit code {result.returncode}")
        return
    
    # Найти путь к JSON файлу
    output = result.stdout
    match = re.search(r"to file '([^']+)'", output)
    
    if not match:
        print("ERROR: Could not find JSON file path in output")
        print(output)
        return
    
    json_file = Path(match.group(1))
    
    if not json_file.exists():
        print(f"ERROR: JSON file not found: {json_file}")
        return
    
    # Скопировать в удобное место
    target = Path("ui_tree_snapshot.json")
    with open(json_file, 'r', encoding='utf-8') as f:
        ui_tree = json.load(f)
    
    with open(target, 'w', encoding='utf-8') as f:
        json.dump(ui_tree, f, indent=2, ensure_ascii=False)
    
    # Удалить оригинал
    json_file.unlink()
    
    print(f"\nSaved UI tree snapshot to: {target}")
    print(f"File size: {target.stat().st_size / 1024:.1f} KB")
    print(f"Root type: {ui_tree.get('pythonObjectTypeName')}")
    print("\nNow you can analyze it with:")
    print("  python dev_tools/analyze_ui_tree.py ui_tree_snapshot.json")

if __name__ == "__main__":
    main()
