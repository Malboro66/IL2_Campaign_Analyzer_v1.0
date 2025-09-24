"""
Defines the UI tab for displaying campaign aces.
"""
from __future__ import annotations

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt

try:
    from app.core.signals import signals
except Exception:
    from app.core.signals import signals


class AcesTab(QWidget):
    """
    A widget to display a list of campaign aces in a table.

    Aces are pilots with more than 5 victories, sorted by their score.
    """
    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the AcesTab.

        Args:
            parent (QWidget | None, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.aces_data = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """
        Set up the user interface for the tab.
        """
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Nome do Ás", "Vitórias"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.table)

    def update_data(self, aces: list) -> None:
        """
        Update the table with a new list of aces.

        The list is filtered to include only pilots with more than 5 victories
        and then sorted in descending order of victories.

        Args:
            aces (list): A list of dictionaries, where each dictionary
                         represents an ace.
        """
        valid = [a for a in (aces or []) if isinstance(a, dict)]
        filtered_sorted = sorted(
            (a for a in valid if int(a.get("victories", 0) or 0) > 5),
            key=lambda a: int(a.get("victories", 0) or 0),
            reverse=True,
        )
        self.aces_data = filtered_sorted
        self.table.setRowCount(len(self.aces_data))
        for row, ace in enumerate(self.aces_data):
            self.table.setItem(row, 0, QTableWidgetItem(ace.get("name", "N/A")))
            self.table.setItem(row, 1, QTableWidgetItem(str(int(ace.get("victories", 0) or 0))))

    def _on_selection_changed(self) -> None:
        """
        Handle the selection of an item in the table.

        Emits the `ace_selected` signal with the data of the selected ace.
        """
        items = self.table.selectedItems()
        if not items:
            return
        row = items[0].row()
        if 0 <= row < len(self.aces_data):
            signals.ace_selected.emit(self.aces_data[row])
