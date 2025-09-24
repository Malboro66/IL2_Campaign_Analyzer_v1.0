"""
Manages the achievement system for the IL-2 Campaign Analyzer.

This module defines the achievements, checks for their completion based on
campaign data, and signals when a new achievement is unlocked.
"""
from PyQt5.QtCore import QObject, pyqtSignal


class AchievementSystem(QObject):
    """
    Handles the logic for unlocking achievements.

    This class maintains the state of all achievements, checks campaign data
    against unlock criteria, and emits a signal when an achievement is earned.

    Attributes:
        unlocked (pyqtSignal): Signal emitted when an achievement is unlocked,
                               providing the achievement's data dictionary.
    """
    unlocked = pyqtSignal(dict)  # {"id": "first_kill", "title": "Primeira Vitória", "icon": "..."}

    def __init__(self):
        """
        Initialize the achievement system with a predefined list of achievements.
        """
        super().__init__()
        self.achievements = {
            "first_kill": {
                "title": "Primeira Vitória",
                "desc": "Obteve a primeira vitória aérea.",
                "icon": "resources/medals/first_kill.png",
                "unlocked": False
            },
            "ace": {
                "title": "Ás da Campanha",
                "desc": "Alcançou 5 vitórias aéreas.",
                "icon": "resources/medals/ace.png",
                "unlocked": False
            },
            "veteran": {
                "title": "Veterano de 50 Missões",
                "desc": "Sobreviveu a 50 missões.",
                "icon": "resources/medals/veteran.png",
                "unlocked": False
            }
        }

    def check_achievements(self, data):
        """
        Check campaign data against achievement criteria.

        Args:
            data (dict): The processed campaign data, containing pilot stats
                         and mission history.
        """
        pilot = data.get("pilot", {})
        missions = data.get("missions", [])

        # Primeira vitória
        if pilot.get("kills", 0) >= 1 and not self.achievements["first_kill"]["unlocked"]:
            self._unlock("first_kill")

        # Ás
        if pilot.get("kills", 0) >= 5 and not self.achievements["ace"]["unlocked"]:
            self._unlock("ace")

        # Veterano
        if pilot.get("total_missions", len(missions)) >= 50 and not self.achievements["veteran"]["unlocked"]:
            self._unlock("veteran")

    def _unlock(self, key):
        """
        Mark an achievement as unlocked and emit the 'unlocked' signal.

        Args:
            key (str): The identifier key for the achievement to unlock.
        """
        self.achievements[key]["unlocked"] = True
        self.unlocked.emit(self.achievements[key])


# Instância global
achievement_system = AchievementSystem()
