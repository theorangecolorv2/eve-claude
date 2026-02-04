"""
Тестовый скрипт для использования филамента через Sanderling.
Демонстрирует полный цикл: открытие инвентаря -> активация фильтра -> использование филамента.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.sanderling.service import SanderlingService
from eve.inventory import InventoryManager
from config import FILAMENT_NAMES
import time

def main():
    """Основная функция"""
    print("="*80)
    print("ТЕСТ ИСПОЛЬЗОВАНИЯ ФИЛАМЕНТА")
    print("="*80)
    
    # Какой филамент использовать
    filament_to_use = FILAMENT_NAMES['CALM_EXOTIC']
    
    print(f"\nБудем использовать: {filament_to_use}")
    print("\nУбедитесь что:")
    print("1. EVE Online запущен")
    print("2. В инвентаре есть филамент")
    print("3. Фильтр !FILAMENT! создан")
    print("\nИнвентарь будет открыт автоматически!")
    
    input("\nНажмите Enter для продолжения...")
    
    service = SanderlingService()
    
    try:
        # Запускаем сервис
        print("\n[1/6] Запуск Sanderling...")
        if not service.start():
            print("[ERROR] Не удалось запустить Sanderling")
            return
        
        print("[OK] Sanderling запущен")
        time.sleep(2)
        
        # Создаем менеджер инвентаря
        inventory = InventoryManager(service)
        
        # Открываем инвентарь если закрыт
        print("\n[2/6] Проверка инвентаря...")
        if not inventory.is_open():
            print("[INFO] Инвентарь закрыт, открываю...")
            if not inventory.open_inventory():
                print("[ERROR] Не удалось открыть инвентарь")
                print("[INFO] Проверьте что кнопка Cargo видна в Neocom")
                return
        
        print("[OK] Инвентарь открыт")
        
        # Получаем текущее состояние
        state = service.get_state()
        if state and state.inventory:
            print(f"  Фильтров: {len(state.inventory.filters)}")
            print(f"  Предметов: {len(state.inventory.items)}")
        
        # Активируем фильтр
        print(f"\n[3/6] Активация фильтра {INVENTORY_FILTERS['FILAMENT']}...")
        if not inventory.activate_filter(INVENTORY_FILTERS['FILAMENT']):
            print("[WARNING] Не удалось активировать фильтр")
            print("[INFO] Продолжаю без фильтра...")
        else:
            print("[OK] Фильтр активирован")
        
        time.sleep(1)
        
        # Ищем филамент
        print(f"\n[4/6] Поиск филамента '{filament_to_use}'...")
        item = inventory.find_item(filament_to_use)
        if not item:
            print("[ERROR] Филамент не найден в инвентаре")
            print("[INFO] Убедитесь что филамент есть в инвентаре")
            return
        
        print(f"[OK] Филамент найден: {item.name}")
        print(f"  Координаты: {item.center}")
        
        # Правый клик
        print(f"\n[5/6] Правый клик по филаменту...")
        if not inventory.right_click_item(item):
            print("[ERROR] Не удалось кликнуть по филаменту")
            return
        
        print("[OK] Контекстное меню открыто")
        
        # Кликаем "Использовать"
        print(f"\n[6/6] Клик по 'Использовать'...")
        if not inventory.click_context_menu_item(CONTEXT_MENU_ACTIONS['USE']):
            if not inventory.click_context_menu_item(CONTEXT_MENU_ACTIONS['USE_EN']):
                print("[ERROR] Не удалось найти кнопку 'Использовать'")
                return
        
        print("[OK] Филамент использован!")
        
        print("\n" + "="*80)
        print("SUCCESS!")
        print("="*80)
        print("Филамент был использован.")
        print("Если вы попали в Abyss - все работает корректно!")
        
    except Exception as e:
        print(f"\n[ERROR] Произошла ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        service.stop()
        print("\n[OK] Сервис остановлен")

if __name__ == "__main__":
    main()
