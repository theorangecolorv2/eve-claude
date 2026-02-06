"""
Дамп полного UI tree в JSON файл.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
import time
import json
from pathlib import Path
from core.sanderling.service import SanderlingService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    logger.info("="*80)
    logger.info("ДАМП UI TREE")
    logger.info("="*80)
    
    # Запустить Sanderling
    sanderling = SanderlingService()
    
    logger.info("Запускаю Sanderling...")
    if not sanderling.start():
        logger.error("Не удалось запустить Sanderling")
        return
    
    logger.info("Жду 2 секунды...")
    time.sleep(2.0)
    
    # Получить последний UI tree напрямую
    logger.info("Читаю UI tree...")
    
    # Делаем прямое чтение
    ui_tree = sanderling._read_memory()
    
    if not ui_tree:
        logger.error("Не удалось прочитать UI tree")
        sanderling.stop()
        return
    
    # Сохранить в файл
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"ui_tree_dump_{timestamp}.json"
    
    logger.info(f"Сохраняю в {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(ui_tree, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✓ Дамп сохранен: {output_file}")
    logger.info(f"  Размер: {output_file.stat().st_size / 1024:.1f} KB")
    
    # Остановить Sanderling
    logger.info("\nОстанавливаю Sanderling...")
    sanderling.stop()
    
    logger.info("="*80)
    logger.info("ДАМП ЗАВЕРШЕН")
    logger.info("="*80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⚠ Прервано пользователем")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}", exc_info=True)
