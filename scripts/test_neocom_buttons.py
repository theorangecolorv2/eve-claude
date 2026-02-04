#!/usr/bin/env python
"""
Тест кнопок Neocom (боковая панель).
Открывает карго, потом инвентарь, чтобы показать разницу.
"""

import sys
import os
import time
import pyautogui

# Добавляем корень проекта в path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.sanderling import SanderlingService


def click_with_feedback(x, y, button_name):
    """Кликнуть с визуальной обратной связью."""
    print(f"\n{'='*60}")
    print(f"Кликаю по кнопке: {button_name}")
    print(f"Координаты: ({x}, {y})")
    print(f"{'='*60}")
    
    # Плавное движение мыши
    pyautogui.moveTo(x, y, duration=0.5)
    time.sleep(0.3)
    
    # Клик
    pyautogui.click(x, y)
    print(f"✓ Клик выполнен!")


def main():
    print("="*60)
    print("ТЕСТ КНОПКИ INVENTORY")
    print("="*60)
    print("\nЭтот скрипт откроет INVENTORY (инвентарь)")
    print()
    
    # Запустить Sanderling
    print("Запускаю Sanderling сервис...")
    service = SanderlingService()
    
    if not service.start():
        print("❌ Не удалось запустить сервис")
        return
    
    print("✓ Сервис запущен")
    print("\nЖду первое чтение памяти...")
    time.sleep(2)
    
    # Получить состояние
    state = service.get_state()
    
    if not state or not state.neocom_buttons:
        print("❌ Не удалось получить кнопки Neocom")
        service.stop()
        return
    
    print(f"\n✓ Найдено кнопок: {len(state.neocom_buttons)}")
    
    # Показать все кнопки
    print("\nДоступные кнопки:")
    for btn in state.neocom_buttons:
        print(f"  - {btn.button_type:20} @ ({btn.center[0]}, {btn.center[1]})")
    
    # Найти кнопку inventory
    inv_btn = next((b for b in state.neocom_buttons if b.button_type == 'inventory'), None)
    
    if not inv_btn:
        print("\n❌ Кнопка INVENTORY не найдена")
        service.stop()
        return
    
    print("\n" + "="*60)
    print("НАЧИНАЮ ТЕСТ")
    print("="*60)
    
    # Пауза перед началом
    print("\nПереключись на окно EVE Online!")
    for i in range(5, 0, -1):
        print(f"Начинаю через {i}...")
        time.sleep(1)
    
    # Открыть INVENTORY
    print("\n" + "="*60)
    print("Открываю INVENTORY (инвентарь)")
    print("="*60)
    print("\nINVENTORY - это полный инвентарь.")
    print("Здесь показываются:")
    print("  - Карго корабля")
    print("  - Ангар станции (если задокован)")
    print("  - Контейнеры")
    print("  - Дрон-бей")
    print("  - И другие хранилища")
    
    click_with_feedback(inv_btn.center[0], inv_btn.center[1], "INVENTORY")
    
    print("\n⏳ Жду 3 секунды...")
    time.sleep(3)
    
    # Финал
    print("\n" + "="*60)
    print("ТЕСТ ЗАВЕРШЕН")
    print("="*60)
    print("\n✓ Инвентарь открыт!")
    print()
    
    # Остановить сервис
    service.stop()
    print("✓ Сервис остановлен")
    print("\nГотово!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
