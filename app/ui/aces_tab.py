from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import pyqtSignal
from app.core.signals import signals   # importa o EventBus

class AcesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.aces_data = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Nome do Ás", "Vitórias"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.table)

    def update_data(self, aces: list):
        self.aces_data = aces or []
        self.table.setRowCount(len(self.aces_data))
        for row, ace in enumerate(self.aces_data):
            self.table.setItem(row, 0, QTableWidgetItem(ace.get("name", "N/A")))
            self.table.setItem(row, 1, QTableWidgetItem(str(ace.get("victories", 0))))

    def _on_selection_changed(self):
        items = self.table.selectedItems()
        if items:
            row = items[0].row()
            ace_data = self.aces_data[row]
            signals.ace_selected.emit(ace_data)  # 🔔 emite via EventBus
