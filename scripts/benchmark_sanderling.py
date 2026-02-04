"""
Бенчмарк производительности Sanderling.
Замеряет реальное время чтения и парсинга UI tree.
"""
import logging
import time
import statistics
from core.sanderling.service import SanderlingService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def benchmark_sanderling(num_reads: int = 20):
    """
    Замерить производительность Sanderling.
    
    Args:
        num_reads: Количество чтений для замера
    """
    logger.info("="*80)
    logger.info("БЕНЧМАРК SANDERLING")
    logger.info("="*80)
    
    # Создать и запустить Sanderling
    service = SanderlingService()
    
    logger.info("Запускаю Sanderling...")
    if not service.start():
        logger.error("Не удалось запустить Sanderling")
        return
    
    logger.info("✓ Sanderling запущен")
    
    # Ждем первого чтения
    logger.info("Жду первого чтения...")
    time.sleep(2.0)
    
    # Замеряем время чтения из фонового потока
    logger.info(f"\nЗамеряю {num_reads} чтений из фонового потока...")
    logger.info("(Ждем пока фоновый поток сделает чтения...)")
    
    read_times = []
    prev_count = service._read_count
    
    start_time = time.time()
    
    while len(read_times) < num_reads:
        time.sleep(0.05)  # Проверяем каждые 50 мс
        
        current_count = service._read_count
        if current_count > prev_count:
            # Было новое чтение
            read_time = service._last_read_time_ms
            read_times.append(read_time)
            
            logger.info(f"  [{len(read_times):2d}/{num_reads}] Read time: {read_time:6.1f} мс")
            prev_count = current_count
        
        # Таймаут 30 секунд
        if time.time() - start_time > 30:
            logger.warning("Таймаут ожидания чтений")
            break
    
    # Статистика
    logger.info("\n" + "="*80)
    logger.info("СТАТИСТИКА")
    logger.info("="*80)
    
    if not read_times:
        logger.error("Нет данных для анализа")
        service.stop()
        return
    
    logger.info(f"\nЧтение памяти (read-memory-64-bit.exe):")
    logger.info(f"  Среднее:  {statistics.mean(read_times):6.1f} мс")
    logger.info(f"  Медиана:  {statistics.median(read_times):6.1f} мс")
    logger.info(f"  Минимум:  {min(read_times):6.1f} мс")
    logger.info(f"  Максимум: {max(read_times):6.1f} мс")
    logger.info(f"  Стд.откл: {statistics.stdev(read_times):6.1f} мс")
    
    avg_read = statistics.mean(read_times)
    max_fps = 1000.0 / avg_read
    
    logger.info(f"\n📊 РЕКОМЕНДАЦИИ:")
    logger.info(f"  Среднее время чтения: {avg_read:.1f} мс")
    logger.info(f"  Максимальная частота: {max_fps:.1f} чтений/сек")
    logger.info(f"  Рекомендуемый read_interval_ms: {int(avg_read * 1.5)} мс (с запасом 50%)")
    logger.info(f"  Минимальный read_interval_ms: {int(avg_read * 1.2)} мс (с запасом 20%)")
    logger.info(f"  Агрессивный read_interval_ms: {int(avg_read)} мс (без запаса)")
    
    # Текущая настройка
    current_interval = service.config.read_interval_ms
    logger.info(f"\n⚙ Текущая настройка: {current_interval} мс")
    
    if current_interval < avg_read:
        logger.warning(f"  ⚠ СЛИШКОМ БЫСТРО! Sanderling не успевает обрабатывать")
        logger.warning(f"  Рекомендуется увеличить до {int(avg_read * 1.2)} мс минимум")
    elif current_interval < avg_read * 1.2:
        logger.warning(f"  ⚠ Мало запаса. Рекомендуется {int(avg_read * 1.5)} мс")
    elif current_interval > avg_read * 3:
        logger.info(f"  ✓ Можно ускорить до {int(avg_read * 1.5)} мс")
    else:
        logger.info(f"  ✓ Оптимально")
    
    # Остановить сервис
    logger.info("\nОстанавливаю Sanderling...")
    service.stop()
    
    logger.info("="*80)
    logger.info("БЕНЧМАРК ЗАВЕРШЕН")
    logger.info("="*80)


if __name__ == "__main__":
    try:
        benchmark_sanderling(num_reads=20)
    except KeyboardInterrupt:
        logger.info("\n⚠ Прервано пользователем")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}", exc_info=True)
