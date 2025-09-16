# app/ui/dashboard_tab.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QGroupBox, QGridLayout
)
from PyQt5.QtCore import Qt

try:
    import pyqtgraph as pg
    PG_AVAILABLE = True
except Exception:
    PG_AVAILABLE = False


class DashboardTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_data = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # KPIs principais
        self.kpi_group = QGroupBox("Resumo da Campanha")
        grid = QGridLayout()

        self.lbl_missions = QLabel("0")
        self.lbl_kills = QLabel("0")
        self.lbl_aces = QLabel("0")
        self.lbl_losses = QLabel("0")

        grid.addWidget(QLabel("Missões voadas:"), 0, 0)
        grid.addWidget(self.lbl_missions, 0, 1)

        grid.addWidget(QLabel("Vitórias totais:"), 1, 0)
        grid.addWidget(self.lbl_kills, 1, 1)

        grid.addWidget(QLabel("Número de ases:"), 2, 0)
        grid.addWidget(self.lbl_aces, 2, 1)

        grid.addWidget(QLabel("Perdas em combate:"), 3, 0)
        grid.addWidget(self.lbl_losses, 3, 1)

        self.kpi_group.setLayout(grid)
        layout.addWidget(self.kpi_group)

        # Mini gráfico de vitórias acumuladas
        if PG_AVAILABLE:
            self.plot_trend = pg.PlotWidget(title="Vitórias acumuladas")
            self.plot_trend.setBackground("w")
            self.plot_trend.showGrid(x=True, y=True)
            layout.addWidget(self.plot_trend)
        else:
            self.lbl_no_pg = QLabel(
                "pyqtgraph não disponível. Instale com: pip install pyqtgraph"
            )
            self.lbl_no_pg.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.lbl_no_pg)

        layout.addStretch(1)

    def update_data(self, data: dict):
        if not data:
            return
        self.all_data = data

        missions = data.get("missions", []) or []
        aces = data.get("aces", []) or []
        pilot = data.get("pilot", {})

        total_missions = len(missions)
        total_kills = sum(int(m.get("kills", 0)) for m in missions)
        total_losses = sum(int(m.get("losses", 0)) for m in missions)

        self.lbl_missions.setText(str(total_missions))
        self.lbl_kills.setText(str(total_kills))
        self.lbl_aces.setText(str(len(aces)))
        self.lbl_losses.setText(str(total_losses))

        if PG_AVAILABLE:
            self._update_trend_chart(missions)

    def _update_trend_chart(self, missions):
        self.plot_trend.clear()
        if not missions:
            return
        kills_per_mission = [int(m.get("kills", 0)) for m in missions]
        cumulative = []
        total = 0
        for k in kills_per_mission:
            total += k
            cumulative.append(total)

        self.plot_trend.plot(
            list(range(1, len(cumulative) + 1)),
            cumulative,
            pen=pg.mkPen(color="#2a9df4", width=2),
            symbol="o",
            symbolBrush="#2a9df4"
        )
