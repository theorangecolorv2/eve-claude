"""Hybrid Overview Manager - uses Sanderling + CV fallback."""
import logging
from typing import Optional
from core.sanderling.service import SanderlingService
from core.cv.template_matcher import TemplateMatcher


logger = logging.getLogger(__name__)


class OverviewManager:
    """Менеджер для работы с Overview (гибридный режим)."""
    
    def __init__(self, sanderling_service: Optional[SanderlingService] = None):
        """
        Инициализация менеджера.
        
        Args:
            sanderling_service: Сервис Sanderling (опционально)
        """
        self.sanderling = sanderling_service
        self.cv_matcher = TemplateMatcher()
        
    def count_targets(self) -> int:
        """
        Подсчитать количество целей в Overview.
        
        Returns:
            Количество целей
        """
        # Попытка через Sanderling
        if self.sanderling and self.sanderling.is_running:
            try:
                state = self.sanderling.get_state()
                if state and state.overview:
                    count = len(state.overview)
                    logger.debug(f"Sanderling: {count} targets in overview")
                    return count
            except Exception as e:
                logger.warning(f"Sanderling failed, falling back to CV: {e}")
        
        # Fallback на CV
        return self._count_targets_cv()
        
    def _count_targets_cv(self) -> int:
        """
        Подсчитать цели через CV (fallback).
        
        Returns:
            Количество целей
        """
        # Импортируем старую логику
        try:
            from shared.eve.overview import count_targets as cv_count_targets
            count = cv_count_targets()
            logger.debug(f"CV fallback: {count} targets")
            return count
        except Exception as e:
            logger.error(f"CV fallback failed: {e}")
            return 0
