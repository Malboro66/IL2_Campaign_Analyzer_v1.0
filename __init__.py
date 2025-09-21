# app/__init__.py

from __future__ import annotations

# Reexporta APIs de alto nível para facilitar imports
from .core import (
    IL2DataParser,
    IL2DataProcessor,
    IL2ReportGenerator,
    signals,
    notification_center,
)

from .ui import (
    BaseTab,
    DashboardTab,
    MissionsTab,
    SquadronTab,
    AcesTab,
    StatsTab,
    SettingsTab,
    AchievementsTab,
    NotificationsTab,
    TabManager,
)

__all__ = [
    # Core
    "IL2DataParser",
    "IL2DataProcessor",
    "IL2ReportGenerator",
    "signals",
    "notification_center",
    # UI
    "BaseTab",
    "DashboardTab",
    "MissionsTab",
    "SquadronTab",
    "AcesTab",
    "StatsTab",
    "SettingsTab",
    "AchievementsTab",
    "NotificationsTab",
    "TabManager",
]
