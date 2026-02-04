"""
Тестовый скрипт для работы с инвентарем через Sanderling.
Демонстрирует получение абсолютных координат фильтров и предметов.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.sanderling.service import SanderlingService
from config import INVENTORY_FILTERS, FILAMENT_NAMES, CONTEXT_MENU_ACTIONS
import time

def test_inventory():
    """Тестирует парсинг инвентаря"""
    print("="*80)
    print("ТЕСТ ИНВЕНТАРЯ")
    print("="*80)
    
    service = SanderlingService()
    
    try:
        # Запускаем сервис
        if not service.start():
            print("[ERROR] Не удалось запустить Sanderling")
            return
        
        print("[OK] Sanderling запущен")
        time.sleep(2)
        
        # Получаем состояние
        state = service.get_state()
        if not state:
            print("[ERROR] Не удалось получить состояние")
            return
        
        print("[OK] Состояние получено")
        
        # Проверяем инвентарь
        if not state.inventory:
            print("\n[INFO] Инвентарь закрыт")
            print("[INFO] Откройте инвентарь и запустите скрипт снова")
            return
        
        inv = state.inventory
        print(f"\n[OK] Инвентарь открыт")
        print(f"  Центр окна: {inv.center}")
        print(f"  Границы: {inv.bounds}")
        
        # Выводим фильтры
        print(f"\n[ФИЛЬТРЫ] Найдено: {len(inv.filters)}")
        for i, f in enumerate(inv.filters):
            status = "[АКТИВЕН]" if f.is_active else "[НЕАКТИВЕН]"
            print(f"  {i+1}. {f.name} {status}")
            print(f"     Координаты для клика: {f.center}")
            print(f"     Границы: {f.bounds}")
        
        # Ищем фильтр !FILAMENT!
        filament_filter = None
        for f in inv.filters:
            if f.name == INVENTORY_FILTERS['FILAMENT']:
                filament_filter = f
                break
        
        if filament_filter:
            print(f"\n[OK] Фильтр {INVENTORY_FILTERS['FILAMENT']} найден!")
            print(f"  Абсолютные координаты для клика: {filament_filter.center}")
            print(f"  Активен: {filament_filter.is_active}")
        else:
            print(f"\n[WARNING] Фильтр {INVENTORY_FILTERS['FILAMENT']} не найден")
        
        # Выводим предметы
        print(f"\n[ПРЕДМЕТЫ] Найдено: {len(inv.items)}")
        for i, item in enumerate(inv.items):
            print(f"  {i+1}. {item.name}")
            if item.hint:
                print(f"     Подсказка: {item.hint}")
            print(f"     Координаты для клика: {item.center}")
            print(f"     Границы: {item.bounds}")
            if item.texture_path:
                print(f"     Текстура: {item.texture_path}")
        
        # Ищем филамент
        filament_item = None
        for item in inv.items:
            if 'Filament' in item.name:
                filament_item = item
                break
        
        if filament_item:
            print(f"\n[OK] Филамент найден: {filament_item.name}")
            print(f"  Абсолютные координаты для клика: {filament_item.center}")
            print(f"  Границы: {filament_item.bounds}")
        else:
            print(f"\n[WARNING] Филамент не найден в инвентаре")
        
        # Проверяем контекстное меню
        if state.context_menu and state.context_menu.is_open:
            print(f"\n[OK] Контекстное меню открыто")
            print(f"[ПУНКТЫ МЕНЮ] Найдено: {len(state.context_menu.items)}")
            for i, item in enumerate(state.context_menu.items):
                print(f"  {i+1}. {item.text}")
                print(f"     Координаты для клика: {item.center}")
            
            # Ищем кнопку "Использовать"
            use_button = None
            for item in state.context_menu.items:
                if item.text in [CONTEXT_MENU_ACTIONS['USE'], CONTEXT_MENU_ACTIONS['USE_EN']]:
                    use_button = item
                    break
            
            if use_button:
                print(f"\n[OK] Кнопка 'Использовать' найдена!")
                print(f"  Абсолютные координаты для клика: {use_button.center}")
            else:
                print(f"\n[WARNING] Кнопка 'Использовать' не найдена")
        else:
            print(f"\n[INFO] Контекстное меню закрыто")
            print(f"[INFO] Сделайте правый клик по предмету чтобы открыть меню")
        
        # Итоги
        print("\n" + "="*80)
        print("ИТОГИ")
        print("="*80)
        print(f"Инвентарь открыт: {inv.is_open}")
        print(f"Фильтров найдено: {len(inv.filters)}")
        print(f"Предметов найдено: {len(inv.items)}")
        print(f"Фильтр !FILAMENT! найден: {'Да' if filament_filter else 'Нет'}")
        print(f"Филамент найден: {'Да' if filament_item else 'Нет'}")
        
        if filament_filter and filament_item:
            print("\n[SUCCESS] Все необходимые элементы найдены!")
            print("\nДля использования филамента:")
            print(f"1. Кликнуть по фильтру: {filament_filter.center}")
            print(f"2. Правый клик по филаменту: {filament_item.center}")
            print(f"3. Кликнуть 'Использовать' в контекстном меню")
        
    finally:
        service.stop()
        print("\n[OK] Сервис остановлен")

if __name__ == "__main__":
    test_inventory()
