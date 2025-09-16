# app/ui/missions_tab.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSplitter, QGroupBox, QVBoxLayout, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt, pyqtSignal

class MissionsTab(QWidget):
    mission_selected = pyqtSignal(dict)  # emite os dados da missão selecionada

    def __init__(self, parent=None):
        super().__init__(parent)
        self.missions_data = []
        self.selected_index = -1
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Vertical)

        # Tabela de missões
        self.missions_table = QTableWidget()
        self.missions_table.setColumnCount(4)
        self.missions_table.setHorizontalHeaderLabels(["Data", "Hora", "Aeronave", "Tipo de Missão"])
        self.missions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.missions_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.missions_table.setSelectionMode(QTableWidget.SingleSelection)
        self.missions_table.itemSelectionChanged.connect(self._on_selection_changed)

        # Detalhes da missão
        details_group = QGroupBox("Detalhes da Missão Selecionada")
        details_layout = QVBoxLayout()
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        details_layout.addWidget(self.details_text)
        details_group.setLayout(details_layout)

        splitter.addWidget(self.missions_table)
        splitter.addWidget(details_group)
        splitter.setSizes([400, 200])

        layout.addWidget(splitter)

    def update_data(self, missions: list):
        """Atualiza a tabela de missões com novos dados"""
        self.missions_data = missions or []
        self.missions_table.setRowCount(len(self.missions_data))
        self.details_text.clear()
        self.selected_index = -1

        for row, mission in enumerate(self.missions_data):
            self.missions_table.setItem(row, 0, QTableWidgetItem(mission.get('date', '')))
            self.missions_table.setItem(row, 1, QTableWidgetItem(mission.get('time', '')))
            self.missions_table.setItem(row, 2, QTableWidgetItem(mission.get('aircraft', '')))
            self.missions_table.setItem(row, 3, QTableWidgetItem(mission.get('duty', '')))

    def _on_selection_changed(self):
        items = self.missions_table.selectedItems()
        if items:
            self.selected_index = items[0].row()
            mission_data = self.missions_data[self.selected_index]
            self.details_text.setText(mission_data.get('description', ''))
            self.mission_selected.emit(mission_data)
        else:
            self.selected_index = -1
            self.details_text.clear()
