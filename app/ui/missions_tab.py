from __future__ import annotations
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSplitter, QGroupBox, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView, QLabel
from PyQt5.QtCore import Qt, pyqtSignal

class MissionsTab(QWidget):
    mission_selected = pyqtSignal(dict)
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.missions_data = []; self.selected_index = -1; self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self); splitter = QSplitter(Qt.Vertical)
        self.missions_table = QTableWidget(); self.missions_table.setColumnCount(4)
        self.missions_table.setHorizontalHeaderLabels(["Data", "Hora", "Aeronave", "Tipo de Missão"])
        self.missions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.missions_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.missions_table.setSelectionMode(QTableWidget.SingleSelection)
        self.missions_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.missions_table.itemSelectionChanged.connect(self._on_selection_changed)
        details_group = QGroupBox("Detalhes da Missão Selecionada"); details_layout = QVBoxLayout()
        self.details_text = QTextEdit(); self.details_text.setReadOnly(True); details_layout.addWidget(self.details_text)
        details_group.setLayout(details_layout); splitter.addWidget(self.missions_table); splitter.addWidget(details_group)
        splitter.setSizes([400, 260]); layout.addWidget(splitter)

    def update_data(self, missions: list) -> None:
        self.missions_data = missions or []; self.missions_table.setRowCount(len(self.missions_data))
        self.details_text.clear(); self.selected_index = -1
        for row, mission in enumerate(self.missions_data):
            self.missions_table.setItem(row, 0, QTableWidgetItem(mission.get("date", "")))
            self.missions_table.setItem(row, 1, QTableWidgetItem(mission.get("time", "")))
            self.missions_table.setItem(row, 2, QTableWidgetItem(mission.get("aircraft", "")))
            self.missions_table.setItem(row, 3, QTableWidgetItem(mission.get("type", "")))

    def _on_selection_changed(self) -> None:
        items = self.missions_table.selectedItems()
        if not items:
            self.selected_index = -1; self.details_text.clear(); return
        self.selected_index = items[0].row(); mission = self.missions_data[self.selected_index]
        report = mission.get("report", {}) or {}
        briefing = mission.get("description", "") or "-"
        hareport = report.get("haReport", "") or ""; narrative = report.get("narrative", "") or ""
        airfield = mission.get("airfield", "") or "-"; altitude = mission.get("altitude_m", None)
        altitude_str = f"{altitude} m" if altitude is not None else "-"
        squadmates = mission.get("squadmates", []) or []; squadmates_str = ", ".join(squadmates) if squadmates else "-"
        text_lines = [
            f"Esquadrão: {mission.get('squadron', '-')}",
            f"Aeródromo: {airfield}",
            f"Altitude: {altitude_str}",
            f"Companheiros: {squadmates_str}",
            "",
            "Briefing:", briefing,
        ]
        if hareport or narrative:
            text_lines += ["", "Debriefing:"]
            if hareport: text_lines.append(hareport)
            if narrative: text_lines.append(narrative)
        self.details_text.setPlainText("\n".join(text_lines))
        self.mission_selected.emit(mission)
