#!/usr/bin/env python
"""
Тест боевой системы через Sanderling.
1. Найти цель с "Pithi" в названии
2. Кликнуть на нее в овере
3. Аппрочнуть
4. Включить пушки (F1)
5. Ждать убийства
6. Переключиться на вкладку Dock
7. Кликнуть на станцию
8. Аппрочнуть станцию
"""

import sys
import os
import time
import keyboard

# Добавляем корень проекта в path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.sanderling import SanderlingService
from shared import mouse


def click_smooth(x, y, name=""):
    """Плавный клик с хуманизацией."""
    if x == 0 and y == 0:
        print(f"  ❌ ОШИБКА: Координаты (0, 0) - невалидные!")
        return False
    
    if name:
        print(f"  → Кликаю: {name} @ ({x}, {y})")
    
    # Используем хуманизированный клик из shared/mouse.py
    mouse.click(x, y, humanize=True, duration=0.5)
    time.sleep(0.3)
    return True


def main():
    print("="*60)
    print("ТЕСТ БОЕВОЙ СИСТЕМЫ")
    print("="*60)
    print("\nЭтапы:")
    print("  1. Найти цель с 'Pithi'")
    print("  2. Кликнуть на цель")
    print("  3. Залочить цель (Lock Target)")
    print("  4. Ждать 3 секунды")
    print("  5. Аппрочнуть цель")
    print("  6. Включить пушки (клавиша 1)")
    print("  7. Ждать убийства")
    print("  8. Переключиться на Dock")
    print("  9. Аппрочнуть станцию")
    print()
    
    # Запустить Sanderling
    print("[1/9] Запускаю Sanderling...")
    service = SanderlingService()
    
    if not service.start():
        print("❌ Не удалось запустить сервис")
        return
    
    print("✓ Сервис запущен")
    time.sleep(2)
    
    # Получить состояние
    state = service.get_state()
    if not state:
        print("❌ Не удалось получить состояние")
        service.stop()
        return
    
    print(f"✓ Overview: {len(state.overview)} записей")
    print(f"✓ Tabs: {len(state.overview_tabs)} вкладок")
    
    # Найти цель с "Pithi"
    print("\n[2/9] Ищу цель с 'Pithi' в названии...")
    target = None
    for entry in state.overview:
        if entry.name and 'Pithi' in entry.name:
            target = entry
            break
    
    if not target:
        print("❌ Цель с 'Pithi' не найдена в overview")
        print("\nДоступные цели:")
        for entry in state.overview[:10]:
            print(f"  - {entry.name}")
        service.stop()
        return
    
    print(f"✓ Найдена цель: {target.name}")
    print(f"  Тип: {target.type}")
    print(f"  Дистанция: {target.distance}")
    print(f"  Координаты: {target.center}")
    
    # Проверить координаты
    if not target.center or target.center == (0, 0):
        print("\n❌ ОШИБКА: Координаты цели невалидные!")
        print("  Это означает что парсер не смог извлечь координаты из overview.")
        print("  Возможные причины:")
        print("    - Overview entry не имеет _displayX/_displayY")
        print("    - Нужно использовать абсолютные координаты")
        service.stop()
        return
    
    # Пауза
    print("\n⚠️ Переключись на окно EVE!")
    for i in range(5, 0, -1):
        print(f"Начинаю через {i}...")
        time.sleep(1)
    
    # Кликнуть на цель в овере
    print("\n[3/9] Кликаю на цель в overview...")
    if not click_smooth(target.center[0], target.center[1], target.name):
        print("❌ Не удалось кликнуть на цель")
        service.stop()
        return
    time.sleep(0.5)
    
    # Залочить цель (Ctrl+Click или просто повторный клик)
    print("\n[4/9] Лочу цель (Ctrl+Click)...")
    
    # Используем Ctrl+Click для лока
    keyboard.press('ctrl')
    time.sleep(0.1)
    if not click_smooth(target.center[0], target.center[1], "Lock (Ctrl+Click)"):
        keyboard.release('ctrl')
        print("❌ Не удалось залочить цель")
        service.stop()
        return
    keyboard.release('ctrl')
    
    print("  ⏳ Жду 5 секунды (лок цели)...")
    time.sleep(5)
    
    # Обновить состояние
    state = service.get_state()
    
    # Проверить что цель залочена
    if len(state.targets) == 0:
        print("❌ Цель не залочена")
        print("  Попробуй вручную залочить цель перед запуском скрипта")
        service.stop()
        return
    
    print(f"✓ Цель залочена! Залочено целей: {len(state.targets)}")
    
    # Обновить состояние для получения новых действий
    state = service.get_state()
    
    # Найти кнопку Approach или Align To
    print("\n[5/8] Ищу кнопку Approach/Align To...")
    approach_action = next((a for a in state.selected_actions if a.name in ['approach', 'align_to']), None)
    
    if not approach_action:
        print("❌ Кнопка Approach/Align To не найдена")
        print("Доступные действия:")
        for action in state.selected_actions:
            print(f"  - {action.name}")
        service.stop()
        return
    
    print(f"✓ Найдена кнопка: {approach_action.name}")
    click_smooth(approach_action.center[0], approach_action.center[1], approach_action.name.upper())
    time.sleep(1)
    
    # Включить пушки (клавиша 1)
    print("\n[6/8] Включаю пушки (клавиша 1)...")
    keyboard.press_and_release('1')
    print("✓ Клавиша '1' нажата")
    time.sleep(1)
    
    # Ждать убийства цели
    print("\n[7/8] Жду убийства цели...")
    print("  (проверяю каждые 2 секунды)")
    print("  Убийство = исчезновение из списка залоченных целей")
    
    max_wait = 120  # 2 минуты максимум
    elapsed = 0
    target_killed = False
    last_hull = None
    
    while elapsed < max_wait:
        time.sleep(2)
        elapsed += 2
        
        # Обновить состояние
        state = service.get_state()
        
        # Проверить есть ли залоченные цели
        targets_count = len(state.targets)
        
        if targets_count == 0:
            print(f"\n✓ Цель убита! (прошло {elapsed}с)")
            print("  Цель исчезла из списка залоченных целей")
            target_killed = True
            break
        
        # Показать прогресс
        if targets_count > 0:
            # Найти активную цель или первую
            active_target = next((t for t in state.targets if t.is_active), state.targets[0])
            
            # Показать здоровье
            if active_target.shield is not None and active_target.hull is not None:
                shield_pct = active_target.shield * 100
                armor_pct = active_target.armor * 100 if active_target.armor else 0
                hull_pct = active_target.hull * 100
                
                print(f"  [{elapsed}с] {active_target.name}")
                print(f"         S:{shield_pct:>3.0f}% A:{armor_pct:>3.0f}% H:{hull_pct:>3.0f}%")
                
                # Отследить изменение hull
                if last_hull is not None and hull_pct < last_hull:
                    print(f"         ⚠️ Hull падает! ({last_hull:.0f}% → {hull_pct:.0f}%)")
                last_hull = hull_pct
            else:
                print(f"  [{elapsed}с] Цель жива, залочено целей: {targets_count}")
    
    if not target_killed:
        print(f"\n⚠️ Таймаут ({max_wait}с) - цель не убита")
        print(f"  Залочено целей: {len(state.targets)}")
        service.stop()
        return
    
    # Переключиться на вкладку Dock
    print("\n[8/8] Переключаюсь на вкладку Dock...")
    state = service.get_state()
    
    dock_tab = next((t for t in state.overview_tabs if 'Dock' in t.label), None)
    
    if not dock_tab:
        print("❌ Вкладка Dock не найдена")
        print("Доступные вкладки:")
        for tab in state.overview_tabs:
            print(f"  - {tab.label}")
        service.stop()
        return
    
    print(f"✓ Найдена вкладка: {dock_tab.label}")
    click_smooth(dock_tab.center[0], dock_tab.center[1], dock_tab.label)
    time.sleep(1)
    
    # Обновить overview
    state = service.get_state()
    
    # Найти станцию
    print("\n[9/9] Ищу станцию...")
    station = None
    for entry in state.overview:
        if entry.type and 'Station' in entry.type:
            station = entry
            break
    
    if not station:
        # Попробовать по названию
        for entry in state.overview:
            if entry.name and ('Station' in entry.name or 'станц' in entry.name.lower()):
                station = entry
                break
    
    if not station:
        print("❌ Станция не найдена в overview")
        print("\nДоступные объекты:")
        for entry in state.overview[:10]:
            print(f"  - {entry.name} ({entry.type})")
        service.stop()
        return
    
    print(f"✓ Найдена станция: {station.name}")
    
    # Кликнуть на станцию
    click_smooth(station.center[0], station.center[1], station.name)
    time.sleep(1)
    
    # Обновить состояние
    state = service.get_state()
    
    # Найти кнопку Approach или Align To
    approach_action = next((a for a in state.selected_actions if a.name in ['approach', 'align_to']), None)
    
    if not approach_action:
        print("❌ Кнопка Approach/Align To не найдена")
        service.stop()
        return
    
    print(f"✓ Аппрочу станцию ({approach_action.name})...")
    click_smooth(approach_action.center[0], approach_action.center[1], approach_action.name.upper())

    
    # Финал
    print("\n" + "="*60)
    print("ТЕСТ ЗАВЕРШЕН")
    print("="*60)
    print("\n✓ Все этапы выполнены:")
    print("  1. Найдена цель с 'Pithi'")
    print("  2. Кликнул на цель")
    print("  3. Залочил цель (Lock Target)")
    print("  4. Подождал 3 секунды")
    print("  5. Аппрочнул цель")
    print("  6. Включил пушки (клавиша 1)")
    print("  7. Дождался убийства (цель исчезла из targets)")
    print("  8. Переключился на вкладку Dock")
    print("  9. Аппрочнул станцию")
    print("\n🎉 Боевая система работает!")
    
    # Остановить сервис
    service.stop()
    print("\n✓ Сервис остановлен")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
