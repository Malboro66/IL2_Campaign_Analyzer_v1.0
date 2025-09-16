# app/ui/squadron_tab.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import pyqtSignal

class SquadronTab(QWidget):
    member_selected = pyqtSignal(dict)  # opcional: emite quando um membro do esquadrão é clicado

    def __init__(self, parent=None):
        super().__init__(parent)
        self.squadron_data = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Nome", "Patente", "Abates", "Missões Voadas", "Status"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.table)

    def update_data(self, squadron: list):
        """Preenche a tabela com os dados do esquadrão"""
        self.squadron_data = squadron or []
        self.table.setRowCount(len(self.squadron_data))

        for row, member in enumerate(self.squadron_data):
            self.table.setItem(row, 0, QTableWidgetItem(member.get('name', '')))
            self.table.setItem(row, 1, QTableWidgetItem(member.get('rank', '')))
            self.table.setItem(row, 2, QTableWidgetItem(str(member.get('victories', 0))))
            self.table.setItem(row, 3, QTableWidgetItem(str(member.get('missions_flown', 0))))
            self.table.setItem(row, 4, QTableWidgetItem(member.get('status', '')))

    def _on_selection_changed(self):
        items = self.table.selectedItems()
        if items:
            row = items[0].row()
            member_data = self.squadron_data[row]
            self.member_selected.emit(member_data)
