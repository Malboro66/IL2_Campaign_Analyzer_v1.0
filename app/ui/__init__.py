# app/ui/__init__.py

from __future__ import annotations

from .base_tab import BaseTab
from .dashboard_tab import DashboardTab
from .missions_tab import MissionsTab
from .squadron_tab import SquadronTab
from .aces_tab import AcesTab
from .stats_tab import StatsTab
from .settings_tab import SettingsTab
from .achievements_tab import AchievementsTab
from .notifications_tab import NotificationsTab
from .tab_manager import TabManager

__all__ = [
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
