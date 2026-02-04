"""
Автоматическое использование филамента.
Делает все автоматически: открывает инвентарь, активирует фильтр, использует филамент.
"""
import sys
import os
import logging
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.sanderling.service import SanderlingService
from eve.inventory import InventoryManager
from config import FILAMENT_NAMES
import time

def main():
    """Основная функция"""
    print("="*80)
    print("АВТОМАТИЧЕСКОЕ ИСПОЛЬЗОВАНИЕ ФИЛАМЕНТА")
    print("="*80)
    
    filament_to_use = FILAMENT_NAMES['CALM_EXOTIC']
    
    print(f"\nИспользую: {filament_to_use}")
    print("\nТребования:")
    print("1. EVE Online запущен")
    print("2. Филамент есть в инвентаре")
    print("3. Фильтр !FILAMENT! создан")
    
    input("\nНажмите Enter для запуска...")
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(levelname)s: %(message)s'
    )
    
    service = SanderlingService()
    
    try:
        print("\nЗапуск Sanderling...")
        if not service.start():
            print("[ERROR] Не удалось запустить Sanderling")
            return
        
        print("[OK] Sanderling запущен")
        time.sleep(2)
        
        inventory = InventoryManager(service)
        
        if inventory.use_filament(filament_to_use):
            print("\n" + "="*80)
            print("SUCCESS!")
            print("="*80)
        else:
            print("\n[ERROR] Не удалось использовать филамент")
        
    except Exception as e:
        print(f"\n[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        service.stop()
        print("\n[OK] Сервис остановлен")

if __name__ == "__main__":
    main()
