"""
Defines the UI tab for displaying unlocked achievements.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem
from PyQt5.QtGui import QIcon
from app.core.achievements import achievement_system


class AchievementsTab(QWidget):
    """
    A widget to display a list of achievements that the player has unlocked.

    This tab listens for signals from the central `achievement_system` and
    dynamically adds newly unlocked achievements to a list.
    """
    def __init__(self, parent=None):
        """
        Initialize the AchievementsTab.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self._setup_ui()

        # Connect to the global achievement system to receive unlocks
        achievement_system.unlocked.connect(self._add_achievement)

    def _setup_ui(self):
        """
        Set up the user interface for the tab.
        """
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>Conquistas Desbloqueadas</b>"))

        self.list = QListWidget()
        layout.addWidget(self.list)

    def _add_achievement(self, achievement: dict):
        """
        Add a new achievement to the list view.

        This method is a slot connected to the `unlocked` signal of the
        `achievement_system`.

        Args:
            achievement (dict): A dictionary containing the achievement's
                                title, description, and icon path.
        """
        item = QListWidgetItem()
        item.setText(f"{achievement['title']} — {achievement['desc']}")
        if achievement["icon"]:
            item.setIcon(QIcon(achievement["icon"]))
        self.list.addItem(item)
