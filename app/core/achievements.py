# app/core/achievements.py
from PyQt5.QtCore import QObject, pyqtSignal


class AchievementSystem(QObject):
    unlocked = pyqtSignal(dict)  # {"id": "first_kill", "title": "Primeira Vitória", "icon": "..."}

    def __init__(self):
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
        """Verifica dados da campanha e desbloqueia medalhas"""
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
        self.achievements[key]["unlocked"] = True
        self.unlocked.emit(self.achievements[key])


# Instância global
achievement_system = AchievementSystem()
