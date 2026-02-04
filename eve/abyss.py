"""
Модуль для работы с Abyss (Бездна) в EVE Online.

DEPRECATED: Функционал перенесен в bots/abyss_farmer/
Этот файл оставлен для обратной совместимости.
"""
import logging

logger = logging.getLogger(__name__)

# Импорты для обратной совместимости
try:
    from bots.abyss_farmer.enter import enter_abyss
    from bots.abyss_farmer.room import room
except ImportError:
    logger.warning("Не удалось импортировать модули из bots/abyss_farmer/")
    
    def enter_abyss(*args, **kwargs):
        raise NotImplementedError("Функция перенесена в bots/abyss_farmer/enter.py")
    
    def room(*args, **kwargs):
        raise NotImplementedError("Функция перенесена в bots/abyss_farmer/room.py")
