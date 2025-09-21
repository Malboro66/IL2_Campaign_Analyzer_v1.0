from __future__ import annotations
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout

class StatsTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.pilot_group = QGroupBox("Piloto"); self.pilot_layout = QFormLayout(); self.pilot_group.setLayout(self.pilot_layout)
        self.layout.addWidget(self.pilot_group)
        self.squadron_group = QGroupBox("Esquadrão"); self.squadron_layout = QFormLayout(); self.squadron_group.setLayout(self.squadron_layout)
        self.layout.addWidget(self.squadron_group)
        self.no_data_label = QLabel("Nenhuma campanha carregada."); self.layout.addWidget(self.no_data_label)

    def update_data(self, data: dict) -> None:
        if not data or "pilot" not in data:
            self.no_data_label.setText("Nenhuma campanha carregada."); return
        self.no_data_label.hide(); pilot = data.get("pilot", {}) or {}; squadron = data.get("squadron", {}) or {}
        self._clear_layout(self.pilot_layout); self._clear_layout(self.squadron_layout)
        self.pilot_layout.addRow("Nome:", QLabel(pilot.get("name", "N/A")))
        self.pilot_layout.addRow("Patente:", QLabel(pilot.get("rank", "N/A")))
        self.pilot_layout.addRow("Esquadrão:", QLabel(pilot.get("squadron", "N/A")))
        self.pilot_layout.addRow("Aeronave:", QLabel(pilot.get("aircraft", "N/A")))
        self.pilot_layout.addRow("Vitórias:", QLabel(str(pilot.get("kills", 0))))
        self.pilot_layout.addRow("Missões voadas:", QLabel(str(pilot.get("total_missions", 0))))
        self.squadron_layout.addRow("Nome:", QLabel(squadron.get("name", "N/A")))
        self.squadron_layout.addRow("Aeronave:", QLabel(squadron.get("aircraft", "N/A")))
        self.squadron_layout.addRow("Missões totais:", QLabel(str(squadron.get("total_missions", 0))))
        self.squadron_layout.addRow("Vitórias totais:", QLabel(str(squadron.get("total_kills", 0))))

    def _clear_layout(self, layout: QFormLayout) -> None:
        while layout.count():
            item = layout.takeAt(0); widget = item.widget()
            if widget: widget.deleteLater()
