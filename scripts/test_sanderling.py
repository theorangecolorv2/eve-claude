#!/usr/bin/env python
"""
Тестовый скрипт для Sanderling сервиса.

Запуск:
    python scripts/test_sanderling.py
"""

import sys
import os
import time
import logging
from typing import Optional

# Добавляем корень проекта в path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.sanderling import SanderlingService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def clear_screen():
    """Очистить экран."""
    os.system('cls' if os.name == 'nt' else 'clear')


def format_distance(distance: float) -> str:
    """Форматировать дистанцию."""
    if distance is None:
        return "N/A"
    if distance >= 1000:
        return f"{distance/1000:.1f} км"
    else:
        return f"{distance:.0f} м"


def format_percent(value: Optional[float]) -> str:
    """Форматировать процент."""
    if value is None:
        return "N/A"
    return f"{value*100:.0f}%"


def format_health_bar(shield: Optional[float], armor: Optional[float], hull: Optional[float]) -> str:
    """Форматировать полоску здоровья."""
    s = format_percent(shield) if shield is not None else "N/A"
    a = format_percent(armor) if armor is not None else "N/A"
    h = format_percent(hull) if hull is not None else "N/A"
    return f"S:{s:>4} A:{a:>4} H:{h:>4}"


def main():
    """Тестирование Sanderling сервиса."""

    print("=" * 60)
    print("SANDERLING SERVICE TEST - FULL AUTO MODE")
    print("=" * 60)

    # Создаём сервис
    service = SanderlingService()

    # Запускаем полностью автоматически
    print("\n[1/3] Searching for EVE Online process...")
    print("[2/3] Searching for root address (may take up to 3 minutes)...")
    print("[3/3] Starting UI tree reading...")
    print("\nStarting service...")
    
    if not service.start():
        print("\nERROR: Failed to start service")
        return

    print(f"\nService started")
    print(f"  PID: {service.eve_process_id}")
    print(f"  Root address: {service._root_address}")
    print("\nWaiting for first memory read...")
    time.sleep(2)

    # Основной цикл с обновлением на месте
    try:
        iteration = 0
        while True:
            iteration += 1
            
            # Очистить экран
            clear_screen()
            
            # Заголовок
            print("=" * 60)
            print(f"SANDERLING SERVICE - Iteration #{iteration}")
            print(f"Time: {time.strftime('%H:%M:%S')} | Reads: {service.read_count} | Read time: {service.last_read_time_ms}ms")
            print("=" * 60)

            # Targets
            print(f"\n[TARGETS] Total: {service.targets_count}")
            if service.targets_count > 0:
                for i, target in enumerate(service.targets[:5], 1):
                    active = " [ACTIVE]" if target.is_active else ""
                    dist = format_distance(target.distance)
                    health = format_health_bar(target.shield, target.armor, target.hull)
                    print(f"  {i}. {target.name}{active}")
                    print(f"     Type: {target.type} | Distance: {dist}")
                    print(f"     Health: {health}")
                if service.targets_count > 5:
                    print(f"  ... and {service.targets_count - 5} more")
            else:
                print("  (no targets)")

            # Overview
            print(f"\n[OVERVIEW] Total entries: {service.overview_count}")
            if service.overview_count > 0:
                for i, entry in enumerate(service.overview[:8], 1):
                    t = (entry.type[:20] + '...') if entry.type and len(entry.type) > 20 else (entry.type or 'N/A')
                    n = (entry.name[:30] + '...') if entry.name and len(entry.name) > 30 else (entry.name or 'N/A')
                    d = entry.distance or 'N/A'
                    print(f"  {i}. [{t:23}] {n:33} | {d}")
                if service.overview_count > 8:
                    print(f"  ... and {service.overview_count - 8} more")
            else:
                print("  (overview empty)")

            # Modules
            print(f"\n[MODULES] Total: {len(service.modules)}, Active: {service.active_modules_count}")
            if len(service.modules) > 0:
                for module in service.modules[:8]:
                    status = "[ON] " if module.is_active else "[OFF]"
                    slot = module.slot_name or "Unknown"
                    print(f"  {status} {slot}")
                if len(service.modules) > 8:
                    print(f"  ... and {len(service.modules) - 8} more")
            else:
                print("  (no modules)")
            
            # Ship Status
            state = service.get_state()
            if state and state.ship:
                ship = state.ship
                print(f"\n[SHIP STATUS]")
                print(f"  Health: {format_health_bar(ship.shield, ship.armor, ship.hull)}")
                print(f"  Capacitor: {format_percent(ship.capacitor)}")
                print(f"  Speed: {ship.speed:.0f} м/с")
            
            # Selected Actions
            if state and state.selected_actions:
                print(f"\n[AVAILABLE ACTIONS] Total: {len(state.selected_actions)}")
                for action in state.selected_actions[:6]:
                    print(f"  {action.name:20} @ ({action.center[0]}, {action.center[1]})")
                if len(state.selected_actions) > 6:
                    print(f"  ... and {len(state.selected_actions) - 6} more")
            
            # Overview Tabs
            if state and state.overview_tabs:
                print(f"\n[OVERVIEW TABS] Total: {len(state.overview_tabs)}")
                for tab in state.overview_tabs:
                    print(f"  {tab.label:30} @ ({tab.center[0]}, {tab.center[1]})")
            
            # Neocom Buttons
            if state and state.neocom_buttons:
                print(f"\n[NEOCOM BUTTONS] Total: {len(state.neocom_buttons)}")
                for btn in state.neocom_buttons:
                    print(f"  {btn.button_type:20} @ ({btn.center[0]}, {btn.center[1]})")


            # Stats
            print(f"\n[STATS]")
            print(f"  Successful reads: {service.read_count}")
            print(f"  Errors: {service.error_count}")
            if service.read_count > 0:
                success_rate = ((service.read_count / (service.read_count + service.error_count)) * 100)
                print(f"  Success rate: {success_rate:.1f}%")

            # Ждём 1 секунду
            print("\n[Press Ctrl+C to exit]")
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nStopping...")
    finally:
        service.stop()
        print("Done")


if __name__ == "__main__":
    main()
