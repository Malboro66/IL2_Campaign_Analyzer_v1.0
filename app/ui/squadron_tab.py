"""
Defines the UI tab for displaying squadron member information.
"""
from __future__ import annotations

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import pyqtSignal


class SquadronTab(QWidget):
    """
    A widget to display a table of all pilots in the player's squadron.

    This tab shows details for each pilot, including their rank, victories,
    missions flown, and current status.

    Signals:
        member_selected (pyqtSignal): Emitted when a squadron member is
                                      selected in the table.
    """
    member_selected = pyqtSignal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the SquadronTab.

        Args:
            parent (QWidget | None, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.squadron_data = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """
        Set up the user interface for the tab.
        """
        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Nome", "Patente", "Abates", "Missões Voadas", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

        layout.addWidget(self.table)

    def update_data(self, squadron_members: list) -> None:
        """
        Update the table with a new list of squadron members.

        Args:
            squadron_members (list): A list of dictionaries, where each
                                     dictionary represents a pilot.
        """
        if not isinstance(squadron_members, list):
            squadron_members = []

        self.squadron_data = [m for m in squadron_members if isinstance(m, dict)]
        self.table.setRowCount(len(self.squadron_data))

        for row, member in enumerate(self.squadron_data):
            self.table.setItem(row, 0, QTableWidgetItem(str(member.get("name", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(str(member.get("rank", ""))))
            self.table.setItem(row, 2, QTableWidgetItem(str(member.get("victories", 0))))
            self.table.setItem(row, 3, QTableWidgetItem(str(member.get("missions_flown", 0))))
            self.table.setItem(row, 4, QTableWidgetItem(str(member.get("status", ""))))

    def _on_selection_changed(self) -> None:
        """
        Handle the selection of an item in the table.

        Emits the `member_selected` signal with the data of the selected pilot.
        """
        items = self.table.selectedItems()
        if not items:
            return
        row = items[0].row()
        if 0 <= row < len(self.squadron_data):
            member_data = self.squadron_data[row]
            self.member_selected.emit(member_data)
