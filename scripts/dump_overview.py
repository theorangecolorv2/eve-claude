"""
Скрипт для дампа overview из Sanderling.

Использование:
    python scripts/dump_overview.py
"""
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Добавляем корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.sanderling.service import SanderlingService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Дамп overview."""
    logger.info("=== ДАМП OVERVIEW ===")
    
    # Создать и запустить Sanderling
    sanderling = SanderlingService()
    
    logger.info("Запускаю Sanderling...")
    if not sanderling.start():
        logger.error("Не удалось запустить Sanderling")
        return
    
    try:
        # Подождать пока Sanderling прогреется
        import time
        logger.info("Жду 3 секунды для прогрева Sanderling...")
        time.sleep(3)
        
        # Получить state
        logger.info("Читаю state...")
        state = sanderling.get_state()
        
        if not state:
            logger.error("State пустой!")
            return
        
        # Вывести overview
        logger.info("")
        logger.info("=" * 80)
        logger.info("OVERVIEW ENTRIES")
        logger.info("=" * 80)
        
        if not state.overview:
            logger.warning("Overview пустой!")
        else:
            logger.info(f"Найдено записей: {len(state.overview)}")
            logger.info("")
            
            for i, entry in enumerate(state.overview, 1):
                logger.info(f"#{i}:")
                logger.info(f"  Name: {entry.name}")
                logger.info(f"  Type: {entry.type}")
                logger.info(f"  Distance: {entry.distance}")
                logger.info(f"  Center: {entry.center}")
                logger.info("")
        
        # Сохранить в файл
        output_dir = Path(__file__).parent.parent / "output"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"overview_dump_{timestamp}.json"
        
        # Конвертируем в dict для JSON
        overview_data = []
        if state.overview:
            for entry in state.overview:
                overview_data.append({
                    "index": entry.index,
                    "name": entry.name,
                    "type": entry.type,
                    "distance": entry.distance,
                    "center": entry.center,
                    "bounds": entry.bounds
                })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(overview_data, f, indent=2, ensure_ascii=False)
        
        logger.info("=" * 80)
        logger.info(f"Дамп сохранен: {output_file}")
        logger.info("=" * 80)
        
        # Также проверим targets
        logger.info("")
        logger.info("=" * 80)
        logger.info("TARGETS")
        logger.info("=" * 80)
        
        if not state.targets:
            logger.info("Нет залоченных целей")
        else:
            logger.info(f"Залочено целей: {len(state.targets)}")
            for i, target in enumerate(state.targets, 1):
                logger.info(f"#{i}: {target.name} ({target.type})")
        
        logger.info("=" * 80)
    
    except KeyboardInterrupt:
        logger.info("Прервано пользователем")
    
    finally:
        logger.info("Останавливаю Sanderling...")
        sanderling.stop()
    
    logger.info("=== ДАМП ЗАВЕРШЕН ===")


if __name__ == "__main__":
    main()
