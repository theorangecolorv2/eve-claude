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
except ImportError as e:
    logger.debug(f"Импорт enter_abyss: {e}")
    def enter_abyss(*args, **kwargs):
        raise NotImplementedError("Функция перенесена в bots/abyss_farmer/enter.py")

