# app/ui/missions_tab.py

from __future__ import annotations

import re
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter, QGroupBox, QVBoxLayout,
    QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal


class MissionsTab(QWidget):
    mission_selected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.missions_data = []
        self.selected_index = -1
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Vertical)

        self.missions_table = QTableWidget()
        self.missions_table.setColumnCount(4)
        self.missions_table.setHorizontalHeaderLabels(["Data", "Hora", "Aeronave", "Tipo de Missão"])
        self.missions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.missions_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.missions_table.setSelectionMode(QTableWidget.SingleSelection)
        self.missions_table.itemSelectionChanged.connect(self._on_selection_changed)

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

    @staticmethod
    def _fmt_date(value: str) -> str:
        if not value:
            return ""
        s = str(value).strip()
        if len(s) == 10 and s[2] == "/" and s[5] == "/":
            return s
        if len(s) == 8 and s.isdigit():
            return f"{s[6:8]}/{s[4:6]}/{s[0:4]}"
        if len(s) == 10 and (s[4] in "-/" and s[7] in "-/"):
            y, m, d = s[0:4], s[5:7], s[8:10]
            if y.isdigit() and m.isdigit() and d.isdigit():
                return f"{d}/{m}/{y}"
        return s

    @staticmethod
    def _fmt_time_hhmm(s: str) -> str:
        if not s:
            return ""
        s = s.strip()
        m = re.match(r"^(\d{1,2}):(\d{2})(?::\d{2})?$", s)
        if m:
            hh, mm = m.group(1), m.group(2)
            return f"{hh.zfill(2)}:{mm}"
        if len(s) == 4 and s.isdigit():
            return f"{s[:2]}:{s[2:]}"
        return ""

    @staticmethod
    def _extract_time_from_description(desc: str) -> str:
        if not desc:
            return ""
        m = re.search(r"\b(\d{1,2}:\d{2}(?::\d{2})?)\b", desc)
        return m.group(1) if m else ""

    def _derive_display_time(self, mission: dict) -> str:
        from_desc = self._extract_time_from_description(mission.get("description", "") or "")
        if from_desc:
            return self._fmt_time_hhmm(from_desc)
        return self._fmt_time_hhmm(mission.get("time", "") or "")

    def update_data(self, missions: list):
        self.missions_data = missions or []
        self.missions_table.setRowCount(len(self.missions_data))
        self.details_text.clear()
        self.selected_index = -1

        for row, mission in enumerate(self.missions_data):
            date_text = self._fmt_date(mission.get("date", ""))
            time_text = self._derive_display_time(mission)

            self.missions_table.setItem(row, 0, QTableWidgetItem(date_text))
            self.missions_table.setItem(row, 1, QTableWidgetItem(time_text))
            self.missions_table.setItem(row, 2, QTableWidgetItem(mission.get("aircraft", "")))
            self.missions_table.setItem(row, 3, QTableWidgetItem(mission.get("type", "") or mission.get("duty", "")))

        # Selecionar a primeira missão ao trocar de campanha para exibir detalhes imediatamente
        if self.missions_data:
            self.missions_table.selectRow(0)
            self._on_selection_changed()

    def _on_selection_changed(self):
        items = self.missions_table.selectedItems()
        if items:
            self.selected_index = items[0].row()
            mission_data = self.missions_data[self.selected_index]

            desc = mission_data.get("description", "") or ""
            # Mostrar somente companheiros do mesmo esquadrão (já filtrado pelo processor)
            squadmates = mission_data.get("squadmates", []) or []
            pilots_line = ""
            if squadmates:
                pilots_line = "\nPilotos do esquadrão na missão: " + ", ".join(squadmates)

            self.details_text.setText(desc + pilots_line)
            self.mission_selected.emit(mission_data)
        else:
            self.selected_index = -1
            self.details_text.clear()
