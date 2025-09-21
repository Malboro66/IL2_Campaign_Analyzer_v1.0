from __future__ import annotations

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt

try:
    from app.core.signals import signals
except Exception:
    from app.core.signals import signals


class AcesTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.aces_data = []
        self._setup_ui()

    def _setup_ui(self) -> None:
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
        items = self.table.selectedItems()
        if not items:
            return
        row = items[0].row()
        if 0 <= row < len(self.aces_data):
            signals.ace_selected.emit(self.aces_data[row])
