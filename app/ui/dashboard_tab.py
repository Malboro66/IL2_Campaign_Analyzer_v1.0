"""
Defines the main dashboard tab for the application.
"""
from __future__ import annotations

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QGridLayout, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt

try:
    from app.ui.base_tab import BaseTab
except Exception:
    from base_tab import BaseTab

try:
    import pyqtgraph as pg
    PG_AVAILABLE = True
except Exception:
    PG_AVAILABLE = False


class DashboardTab(BaseTab):
    """
    A widget that serves as the main dashboard for the campaign.

    It displays key statistics, a list of top aces, and a chart showing
    the trend of accumulated victories over time.
    """
    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the DashboardTab.

        Args:
            parent (QWidget | None, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.all_data = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        """
        Set up the user interface for the tab.
        """
        layout = QVBoxLayout(self)

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
        grid.addWidget(QLabel("Número de ases (> 5):"), 2, 0)
        grid.addWidget(self.lbl_aces, 2, 1)
        grid.addWidget(QLabel("Perdas em combate:"), 3, 0)
        grid.addWidget(self.lbl_losses, 3, 1)

        self.kpi_group.setLayout(grid)
        layout.addWidget(self.kpi_group)

        self.aces_group = QGroupBox("Ases da Campanha (> 5 vitórias)")
        self.aces_list_widget = QListWidget()
        aces_layout = QVBoxLayout(self.aces_group)
        aces_layout.addWidget(self.aces_list_widget)
        self.aces_group.setLayout(aces_layout)
        layout.addWidget(self.aces_group)

        if PG_AVAILABLE:
            self.plot_trend = pg.PlotWidget(title="Vitórias acumuladas")
            self.plot_trend.setBackground("w")
            self.plot_trend.showGrid(x=True, y=True)
            layout.addWidget(self.plot_trend)
        else:
            self.lbl_no_pg = QLabel("pyqtgraph não disponível. Instale com: pip install pyqtgraph")
            self.lbl_no_pg.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.lbl_no_pg)

        layout.addStretch(1)

    def update_data(self, data: dict) -> None:
        """
        Update the dashboard with new campaign data.

        Args:
            data (dict): The processed campaign data.
        """
        if not data:
            return

        self.all_data = data
        missions = data.get("missions", []) or []
        aces = data.get("aces", []) or []

        total_missions = len(missions)
        total_kills = sum(int(m.get("kills", 0) or 0) for m in missions)
        total_losses = sum(int(m.get("losses", 0) or 0) for m in missions)

        only_aces = sorted(
            (a for a in aces if int(a.get("victories", 0) or 0) > 5),
            key=lambda a: int(a.get("victories", 0) or 0),
            reverse=True,
        )

        self.lbl_missions.setText(str(total_missions))
        self.lbl_kills.setText(str(total_kills))
        self.lbl_aces.setText(str(len(only_aces)))
        self.lbl_losses.setText(str(total_losses))

        self.aces_list_widget.clear()
        for ace in only_aces:
            v = int(ace.get("victories", 0) or 0)
            self.aces_list_widget.addItem(QListWidgetItem(f"{ace.get('name', 'N/A')} ({v} vitórias)"))

        if PG_AVAILABLE:
            self._update_trend_chart(missions)

    def _update_trend_chart(self, missions: list) -> None:
        """
        Update the cumulative victories trend chart.

        Args:
            missions (list): A list of mission data dictionaries.
        """
        self.plot_trend.clear()
        if not missions:
            return
        kills_per_mission = [int(m.get("kills", 0) or 0) for m in missions]
        cumulative, total = [], 0
        for k in kills_per_mission:
            total += k
            cumulative.append(total)
        self.plot_trend.plot(
            list(range(1, len(cumulative) + 1)),
            cumulative,
            pen=pg.mkPen(color="#2a9df4", width=2),
            symbol="o",
            symbolBrush="#2a9df4",
        )
