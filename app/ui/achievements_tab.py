# app/ui/achievements_tab.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QHBoxLayout
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from app.core.achievements import achievement_system


class AchievementsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

        # Conecta desbloqueios
        achievement_system.unlocked.connect(self._add_achievement)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>Conquistas Desbloqueadas</b>"))

        self.list = QListWidget()
        layout.addWidget(self.list)

    def _add_achievement(self, achievement):
        item = QListWidgetItem()
        item.setText(f"{achievement['title']} — {achievement['desc']}")
        if achievement["icon"]:
            item.setIcon(QIcon(achievement["icon"]))
        self.list.addItem(item)
