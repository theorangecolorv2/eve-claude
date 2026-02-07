# eve/sanderling/__init__.py
"""
⚠️ DEPRECATED: Этот модуль не используется.
Используйте core.sanderling вместо eve.sanderling.

Пример:
    from core.sanderling.service import SanderlingService
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
