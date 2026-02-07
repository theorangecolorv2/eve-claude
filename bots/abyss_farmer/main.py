"""
Основной цикл работы Abyss Farmer бота.

Полный цикл:
1. Варп на спот (1 SPOT 1 или 2 SPOT 2)
2. Использование филамента
3. Зачистка абисса
4. Выход и варп на другой спот
5. Повтор цикла пока не кончатся филаменты
"""
import logging
import time
from typing import Optional
from core.sanderling.service import SanderlingService
from eve.bookmarks import right_click_bookmark
from eve.mouse import random_delay
from bots.abyss_farmer.enter import enter_abyss
from bots.abyss_farmer.room_new import default_room
from config import FILAMENT_NAMES

logger = logging.getLogger(__name__)


class AbyssFarmer:
    """Основной класс бота для фарма абисса."""
    
    def __init__(self, sanderling: SanderlingService, filament_name: str = None):
        """
        Инициализация бота.
        
        Args:
            sanderling: Сервис Sanderling
            filament_name: Название филамента (по умолчанию Calm Exotic)
        """
        self.sanderling = sanderling
        self.filament_name = filament_name or FILAMENT_NAMES['CALM_EXOTIC']
        self.current_spot = 1  # Начинаем со спота 1
        self.cycles_completed = 0
        self.total_rooms_cleared = 0
        
    def run(self):
        """
        Запустить основной цикл бота.
        
        Работает пока не кончатся филаменты.
        """
        logger.info("=== ЗАПУСК ABYSS FARMER ===")
        logger.info(f"Филамент: {self.filament_name}")
        logger.info(f"Начальный спот: {self.current_spot}")
        
        start_time = time.time()
        
        try:
            while True:
                cycle_start = time.time()
                logger.info(f"\n{'='*60}")
                logger.info(f"ЦИКЛ #{self.cycles_completed + 1}")
                logger.info(f"{'='*60}\n")
                
                # Выполняем один цикл
                success = self._run_cycle()
                
                if not success:
                    logger.error("Цикл завершился с ошибкой")
                    break
                
                self.cycles_completed += 1
                cycle_time = time.time() - cycle_start
                
                logger.info(f"\n{'='*60}")
                logger.info(f"ЦИКЛ #{self.cycles_completed} ЗАВЕРШЕН ЗА {cycle_time/60:.1f} МИН")
                logger.info(f"Всего циклов: {self.cycles_completed}")
                logger.info(f"Всего комнат: {self.total_rooms_cleared}")
                logger.info(f"{'='*60}\n")
                
        except KeyboardInterrupt:
            logger.info("Остановка по Ctrl+C")
        except Exception as e:
            logger.exception(f"Критическая ошибка: {e}")
        finally:
            total_time = time.time() - start_time
            logger.info(f"\n{'='*60}")
            logger.info(f"=== СТАТИСТИКА ===")
            logger.info(f"Всего циклов: {self.cycles_completed}")
            logger.info(f"Всего комнат: {self.total_rooms_cleared}")
            logger.info(f"Время работы: {total_time/60:.1f} мин")
            if self.cycles_completed > 0:
                logger.info(f"Среднее время цикла: {total_time/self.cycles_completed/60:.1f} мин")
            logger.info(f"{'='*60}\n")
    
    def _run_cycle(self) -> bool:
        """
        Выполнить один полный цикл.
        
        Returns:
            True если цикл успешен, False если нужно остановиться
        """
        # Шаг 1: Варп на текущий спот
        if not self._warp_to_current_spot():
            logger.error("Не удалось варпнуть на спот")
            return False
        
        # Шаг 2: Использовать филамент и войти в абисс
        if not self._enter_abyss_with_filament():
            logger.error("Не удалось войти в абисс")
            # Возможно филаменты кончились
            return False
        
        # Шаг 3: Зачистить комнаты абисса
        rooms_cleared = self._clear_abyss()
        if rooms_cleared == 0:
            logger.error("Не удалось зачистить ни одной комнаты")
            return False
        
        self.total_rooms_cleared += rooms_cleared
        logger.info(f"Зачищено комнат в этом цикле: {rooms_cleared}")
        
        # Шаг 4: Выход из абисса (автоматический)
        logger.info("Ожидание выхода из абисса...")
        random_delay(8.0, 9.0)
        
        # Шаг 5: Переключить спот для следующего цикла
        self._switch_spot()
        
        return True
    
    def _warp_to_current_spot(self) -> bool:
        """
        Варпнуть на текущий спот.
        
        Returns:
            True если успешно
        """
        spot_name = f"{self.current_spot} SPOT {self.current_spot}"
        logger.info(f"Шаг 1: Варп на {spot_name}...")
        
        # Кликаем ПКМ по букмарке
        logger.info(f"Клик ПКМ по букмарке '{spot_name}'...")
        if not right_click_bookmark(self.sanderling, spot_name):
            logger.error(f"Не удалось кликнуть по букмарке '{spot_name}'")
            return False
        
        # Ждем появления контекстного меню (увеличено для обновления Sanderling)
        random_delay(1.5, 2.0)
        
        # Ищем кнопку "Перейти в варп режим" в контекстном меню
        warp_button = self._find_warp_button_in_context_menu()
        
        if not warp_button:
            logger.warning("Кнопка 'Перейти в варп режим' не найдена в контекстном меню")
            logger.info("Возможно уже находимся на споте или меню не прогрузилось")
            
            # Пробуем еще раз
            logger.info("Повторная попытка...")
            random_delay(0.5, 0.8)
            
            if not right_click_bookmark(self.sanderling, spot_name):
                logger.error("Повторный клик не удался")
                return False
            
            random_delay(1.5, 2.0)
            warp_button = self._find_warp_button_in_context_menu()
            
            if not warp_button:
                logger.warning("Кнопка все еще не найдена, считаем что уже на споте")
                return True
        
        # Кликаем по кнопке варпа (увеличен duration на 25%)
        logger.info(f"Клик по кнопке 'Перейти в варп режим' @ {warp_button.center}")
        from eve.mouse import click
        click(warp_button.center[0], warp_button.center[1], duration=0.225)  # 0.18 * 1.25 = 0.225
        
        # Ждем завершения варпа
        logger.info("Ожидание завершения варпа (25-28 сек)...")
        random_delay(25.0, 28.0)
        
        logger.info(f"Варп на {spot_name} завершен")
        return True
    
    def _find_warp_button_in_context_menu(self) -> Optional[object]:
        """
        Найти кнопку "Перейти в варп режим" в контекстном меню.
        
        Returns:
            Объект кнопки или None
        """
        state = self.sanderling.get_state()
        if not state or not state.context_menu:
            logger.debug("Нет контекстного меню")
            return None
        
        # Проверяем что меню открыто
        if not state.context_menu.is_open:
            logger.debug("Контекстное меню не открыто")
            return None
        
        # Получаем items из контекстного меню
        menu_items = state.context_menu.items if hasattr(state.context_menu, 'items') else []
        
        if not menu_items:
            logger.debug("Контекстное меню пустое")
            return None
        
        logger.debug(f"Контекстное меню открыто, пунктов: {len(menu_items)}")
        
        # Ищем кнопку с "warp" в названии в контекстном меню
        for item in menu_items:
            if not item.text:
                continue
            
            text_lower = item.text.lower()
            
            # Проверяем разные варианты названия
            if any(keyword in text_lower for keyword in [
                'warp',
                'варп',
                'перейти в варп'
            ]):
                logger.debug(f"Найдена кнопка варпа в контекстном меню: '{item.text}'")
                return item
        
        logger.debug(f"Кнопка варпа не найдена. Доступные пункты: {[item.text for item in menu_items]}")
        return None
    
    def _enter_abyss_with_filament(self) -> bool:
        """
        Использовать филамент и войти в абисс.
        
        Returns:
            True если успешно, False если филаменты кончились
        """
        logger.info("Шаг 2: Использование филамента...")
        
        try:
            success = enter_abyss(self.sanderling, self.filament_name)
            
            if not success:
                logger.error("Не удалось использовать филамент")
                logger.info("Возможно филаменты закончились")
                return False
            
            # Ждем появления Cache (проверка что в абиссе)
            logger.info("Проверка входа в абисс (ожидание Cache)...")
            if not self._wait_for_abyss_entry():
                logger.error("Не удалось подтвердить вход в абисс")
                return False
            
            logger.info("Успешный вход в абисс")
            return True
            
        except Exception as e:
            logger.exception(f"Ошибка при входе в абисс: {e}")
            return False
    
    def _wait_for_abyss_entry(self, timeout: float = 30.0) -> bool:
        """
        Ждать появления Cache (подтверждение входа в абисс).
        
        Args:
            timeout: Таймаут ожидания (сек)
            
        Returns:
            True если Cache появился
        """
        start = time.time()
        
        while time.time() - start < timeout:
            state = self.sanderling.get_state()
            
            if not state or not state.overview:
                time.sleep(1.0)
                continue
            
            # Ищем Cache в overview
            for entry in state.overview:
                if not entry.name:
                    continue
                
                name_lower = entry.name.lower()
                
                if any(keyword in name_lower for keyword in [
                    'bioadaptive cache',
                    'biocombinative cache',
                    'triglavian cache',
                    'cache'
                ]):
                    logger.info(f"Cache обнаружен: {entry.name}")
                    return True
            
            time.sleep(1.0)
        
        logger.error(f"Cache не появился за {timeout} секунд")
        return False
    
    def _clear_abyss(self) -> int:
        """
        Зачистить все комнаты абисса.
        
        Returns:
            Количество зачищенных комнат
        """
        logger.info("Шаг 3: Зачистка абисса...")
        
        rooms_cleared = 0
        max_rooms = 3  # Обычно 3 комнаты в абиссе
        
        for room_num in range(1, max_rooms + 1):
            logger.info(f"\n{'='*50}")
            logger.info(f"КОМНАТА {room_num}/{max_rooms}")
            logger.info(f"{'='*50}\n")
            
            try:
                # Определяем тип комнаты
                from bots.abyss_farmer.room_detector import detect_room_type
                room_type = detect_room_type(self.sanderling, timeout=30.0)
                logger.info(f"Тип комнаты: {room_type}")
                
                # Выбираем обработчик в зависимости от типа
                if room_type == "tessera":
                    from bots.abyss_farmer.room_tessera import tessera_room
                    success = tessera_room(self.sanderling, timeout=300.0)
                elif room_type == "knight":
                    from bots.abyss_farmer.room_knight import knight_room
                    success = knight_room(self.sanderling, timeout=300.0)
                elif room_type == "vila":
                    from bots.abyss_farmer.room_vila import vila_room
                    success = vila_room(self.sanderling, timeout=300.0)
                elif room_type == "overmind":
                    from bots.abyss_farmer.room_overmind import overmind_room
                    success = overmind_room(self.sanderling, timeout=300.0)
                else:
                    # Стандартная комната
                    success = default_room(self.sanderling, timeout=300.0)
                
                if not success:
                    logger.error(f"Не удалось зачистить комнату {room_num}")
                    break
                
                rooms_cleared += 1
                logger.info(f"Комната {room_num} зачищена успешно")
                
                # Небольшая пауза между комнатами
                random_delay(2.0, 3.0)
                
            except Exception as e:
                logger.exception(f"Ошибка в комнате {room_num}: {e}")
                break
        
        logger.info(f"\nЗачищено комнат: {rooms_cleared}/{max_rooms}")
        return rooms_cleared
    
    def _switch_spot(self):
        """Переключить текущий спот на другой."""
        old_spot = self.current_spot
        self.current_spot = 2 if self.current_spot == 1 else 1
        logger.info(f"Переключение спота: {old_spot} -> {self.current_spot}")


def main():
    """Точка входа для запуска бота."""
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Создаем сервис Sanderling
    sanderling = SanderlingService()
    
    # Создаем и запускаем бота
    bot = AbyssFarmer(sanderling)
    bot.run()


if __name__ == '__main__':
    main()
