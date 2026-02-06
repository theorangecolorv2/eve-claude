"""
Детальный дамп overview для отладки.
"""
import sys
import os
import logging
import time
import json

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.sanderling.service import SanderlingService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Главная функция."""
    logger.info("=== ДЕТАЛЬНЫЙ ДАМП OVERVIEW ===")
    
    # Инициализация Sanderling
    sanderling = SanderlingService()
    
    try:
        # Запуск Sanderling
        logger.info("Запуск Sanderling...")
        if not sanderling.start():
            logger.error("Не удалось запустить Sanderling")
            return
        
        logger.info("Sanderling запущен")
        time.sleep(2.0)
        
        # Получение состояния
        state = sanderling.get_state()
        if not state:
            logger.error("Не удалось получить состояние игры")
            return
        
        logger.info("Подключение к игре установлено\n")
        
        # ===== ВКЛАДКИ OVERVIEW =====
        logger.info("=" * 70)
        logger.info("ВКЛАДКИ OVERVIEW")
        logger.info("=" * 70)
        
        if not state.overview_tabs:
            logger.warning("Нет вкладок overview!")
        else:
            logger.info(f"Найдено вкладок: {len(state.overview_tabs)}\n")
            
            for i, tab in enumerate(state.overview_tabs, 1):
                logger.info(f"Вкладка #{i}:")
                logger.info(f"  Label (raw): {repr(tab.label)}")
                logger.info(f"  Label (display): {tab.label}")
                logger.info(f"  Center: {tab.center}")
                
                # Очистка от HTML и спецсимволов
                import re
                label_clean = re.sub(r'<[^>]+>', '', tab.label)
                label_clean = ''.join(c for c in label_clean if c.isalnum() or c.isspace())
                label_clean = label_clean.strip()
                logger.info(f"  Label (clean): {label_clean}")
                logger.info("")
        
        # ===== ЗАПИСИ OVERVIEW =====
        logger.info("=" * 70)
        logger.info("ЗАПИСИ OVERVIEW")
        logger.info("=" * 70)
        
        if not state.overview:
            logger.warning("Overview пустой!")
        else:
            logger.info(f"Найдено записей: {len(state.overview)}\n")
            
            for i, entry in enumerate(state.overview[:10], 1):  # Первые 10
                logger.info(f"Запись #{i}:")
                logger.info(f"  Name: {entry.name}")
                logger.info(f"  Type: {entry.type}")
                logger.info(f"  Distance: {entry.distance}")
                logger.info(f"  Center: {entry.center}")
                logger.info("")
            
            if len(state.overview) > 10:
                logger.info(f"... и еще {len(state.overview) - 10} записей")
        
        # ===== TARGETS =====
        logger.info("=" * 70)
        logger.info("ЗАЛОЧЕННЫЕ ЦЕЛИ")
        logger.info("=" * 70)
        
        if not state.targets:
            logger.info("Нет залоченных целей")
        else:
            logger.info(f"Залочено целей: {len(state.targets)}\n")
            
            for i, target in enumerate(state.targets, 1):
                logger.info(f"Цель #{i}:")
                logger.info(f"  Name: {target.name}")
                logger.info(f"  Type: {target.type}")
                logger.info(f"  Distance: {target.distance}")
                logger.info(f"  Is Active: {target.is_active}")
                logger.info(f"  Shield: {target.shield:.1%}")
                logger.info(f"  Armor: {target.armor:.1%}")
                logger.info(f"  Hull: {target.hull:.1%}")
                logger.info("")
        
        # ===== SELECTED ACTIONS =====
        logger.info("=" * 70)
        logger.info("ДОСТУПНЫЕ ДЕЙСТВИЯ (SELECTED ACTIONS)")
        logger.info("=" * 70)
        
        if not state.selected_actions:
            logger.info("Нет доступных действий (ничего не выбрано)")
        else:
            logger.info(f"Доступно действий: {len(state.selected_actions)}\n")
            
            for i, action in enumerate(state.selected_actions, 1):
                logger.info(f"Действие #{i}:")
                logger.info(f"  Name: {action.name}")
                logger.info(f"  Center: {action.center}")
                logger.info("")
        
        # ===== СОХРАНЕНИЕ В JSON =====
        logger.info("=" * 70)
        logger.info("СОХРАНЕНИЕ ДАМПА")
        logger.info("=" * 70)
        
        dump_data = {
            "timestamp": time.time(),
            "overview_tabs": [
                {
                    "label": tab.label,
                    "center": tab.center
                }
                for tab in (state.overview_tabs or [])
            ],
            "overview_entries": [
                {
                    "name": entry.name,
                    "type": entry.type,
                    "distance": entry.distance,
                    "center": entry.center
                }
                for entry in (state.overview or [])
            ],
            "targets": [
                {
                    "name": target.name,
                    "type": target.type,
                    "distance": target.distance,
                    "is_active": target.is_active
                }
                for target in (state.targets or [])
            ],
            "selected_actions": [
                {
                    "name": action.name,
                    "center": action.center
                }
                for action in (state.selected_actions or [])
            ]
        }
        
        dump_file = f"temp/overview_dump_{time.strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("temp", exist_ok=True)
        
        with open(dump_file, 'w', encoding='utf-8') as f:
            json.dump(dump_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Дамп сохранен: {dump_file}")
        
    except KeyboardInterrupt:
        logger.info("\nПрервано пользователем")
    except Exception as e:
        logger.exception(f"Ошибка: {e}")
    finally:
        logger.info("\nОстановка Sanderling...")
        sanderling.stop()
        logger.info("Завершено")


if __name__ == "__main__":
    main()
