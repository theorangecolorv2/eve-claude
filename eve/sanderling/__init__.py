# eve/sanderling/__init__.py
"""
Sanderling - модуль чтения памяти EVE Online.

Позволяет получать данные о состоянии игры напрямую из памяти,
без использования template matching.
"""

from .service import SanderlingService
from .models import Target, OverviewEntry, Module, ShipState

__all__ = [
    'SanderlingService',
    'Target',
    'OverviewEntry',
    'Module',
    'ShipState',
]
