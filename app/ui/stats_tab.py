# app/ui/stats_tab.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout,
    QComboBox, QHBoxLayout, QPushButton, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt
import csv

from app.core.report_generator import IL2ReportGenerator

try:
    import pyqtgraph as pg
    import pyqtgraph.exporters
    PG_AVAILABLE = True
except Exception:
    PG_AVAILABLE = False


class StatsTab(QWidget):
    """
    Aba de Estatísticas com gráficos e exportação.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_data = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # ----------- Filtros
        filters_group = QGroupBox("Filtros")
        filters_layout = QHBoxLayout()

        self.cmb_range = QComboBox()
        self.cmb_range.addItems(["Últimas 5", "Últimas 10", "Todas"])
        self.cmb_range.currentIndexChanged.connect(self._apply_filters)
        filters_layout.addWidget(QLabel("Intervalo:"))
        filters_layout.addWidget(self.cmb_range)

        self.cmb_type = QComboBox()
        self.cmb_type.addItems(["Todos", "Escolta", "Ataque", "Patrulha", "Outros"])
        self.cmb_type.currentIndexChanged.connect(self._apply_filters)
        filters_layout.addWidget(QLabel("Tipo de missão:"))
        filters_layout.addWidget(self.cmb_type)

        filters_group.setLayout(filters_layout)
        layout.addWidget(filters_group)

        # ----------- Botões de exportação
        export_layout = QHBoxLayout()
        self.btn_export_png = QPushButton("Exportar gráficos (PNG)")
        self.btn_export_csv = QPushButton("Exportar estatísticas (CSV)")
        self.btn_export_pdf = QPushButton("Exportar relatório PDF")

        self.btn_export_png.clicked.connect(self._export_png)
        self.btn_export_csv.clicked.connect(self._export_csv)
        self.btn_export_pdf.clicked.connect(self._export_pdf)

        export_layout.addWidget(self.btn_export_png)
        export_layout.addWidget(self.btn_export_csv)
        export_layout.addWidget(self.btn_export_pdf)
        layout.addLayout(export_layout)

        # ----------- Info piloto
        self.group_pilot = QGroupBox("Piloto")
        pilot_layout = QFormLayout()
        self.lbl_pilot_missions = QLabel("0")
        self.lbl_pilot_kills = QLabel("0")
        self.lbl_pilot_aircraft = QLabel("N/A")
        pilot_layout.addRow("Missões voadas:", self.lbl_pilot_missions)
        pilot_layout.addRow("Vitórias aéreas:", self.lbl_pilot_kills)
        pilot_layout.addRow("Aeronave principal:", self.lbl_pilot_aircraft)
        self.group_pilot.setLayout(pilot_layout)
        layout.addWidget(self.group_pilot)

        # ----------- Gráficos
        self.group_charts = QGroupBox("Gráficos")
        charts_layout = QVBoxLayout()
        self.group_charts.setLayout(charts_layout)
        layout.addWidget(self.group_charts)

        if PG_AVAILABLE:
            self.plot_kills = pg.PlotWidget(title="Vitórias por missão")
            self.plot_kills.showGrid(x=True, y=True)
            charts_layout.addWidget(self.plot_kills)

            self.plot_aces = pg.PlotWidget(title="Vitórias por ás (barra horizontal)")
            self.plot_aces.showGrid(x=True, y=True)
            charts_layout.addWidget(self.plot_aces)
        else:
            self.lbl_no_pg = QLabel(
                "pyqtgraph não disponível. Instale com: pip install pyqtgraph"
            )
            self.lbl_no_pg.setAlignment(Qt.AlignCenter)
            charts_layout.addWidget(self.lbl_no_pg)

        # ----------- Esquadrão
        self.group_squadron = QGroupBox("Esquadrão")
        squad_layout = QFormLayout()
        self.lbl_squadron_missions = QLabel("0")
        self.lbl_squadron_kills = QLabel("0")
        self.lbl_squadron_losses = QLabel("0")
        squad_layout.addRow("Missões registradas:", self.lbl_squadron_missions)
        squad_layout.addRow("Vitórias totais:", self.lbl_squadron_kills)
        squad_layout.addRow("Perdas em combate:", self.lbl_squadron_losses)
        self.group_squadron.setLayout(squad_layout)
        layout.addWidget(self.group_squadron)

        # ----------- Campanha
        self.group_campaign = QGroupBox("Campanha")
        camp_layout = QFormLayout()
        self.lbl_total_missions = QLabel("0")
        self.lbl_total_aces = QLabel("0")
        camp_layout.addRow("Total de missões:", self.lbl_total_missions)
        camp_layout.addRow("Número de ases:", self.lbl_total_aces)
        self.group_campaign.setLayout(camp_layout)
        layout.addWidget(self.group_campaign)

        layout.addStretch(1)

    # ------------------------
    # Atualização de dados
    # ------------------------
    def update_data(self, data: dict):
        if not data:
            return
        self.all_data = data
        self._apply_filters()

    # ------------------------
    # Aplicar filtros
    # ------------------------
    def _apply_filters(self):
        if not self.all_data:
            return

        pilot = self.all_data.get("pilot", {})
        missions = self.all_data.get("missions", []) or []
        aces = self.all_data.get("aces", []) or []

        # Filtro tipo
        selected_type = self.cmb_type.currentText()
        if selected_type != "Todos":
            missions = [m for m in missions if m.get("duty", "Outros") == selected_type]

        # Filtro intervalo
        selected_range = self.cmb_range.currentText()
        if selected_range == "Últimas 5":
            missions = missions[-5:]
        elif selected_range == "Últimas 10":
            missions = missions[-10:]

        # Atualiza números
        self.lbl_pilot_missions.setText(str(pilot.get("total_missions", len(missions))))
        self.lbl_pilot_kills.setText(str(pilot.get("kills", 0)))
        self.lbl_pilot_aircraft.setText(pilot.get("aircraft", "N/A"))

        self.lbl_squadron_missions.setText(str(len(missions)))
        total_kills = sum(int(m.get("kills", 0)) for m in missions)
        self.lbl_squadron_kills.setText(str(total_kills))
        losses = sum(int(m.get("losses", 0)) for m in missions)
        self.lbl_squadron_losses.setText(str(losses))

        self.lbl_total_missions.setText(str(len(missions)))
        self.lbl_total_aces.setText(str(len(aces)))

        # Atualiza gráficos
        if PG_AVAILABLE:
            self._update_charts(missions, aces)

    def _update_charts(self, missions, aces):
        # Kills por missão
        self.plot_kills.clear()
        if missions:
            x_vals = list(range(len(missions)))
            y_vals = [int(m.get("kills", 0)) for m in missions]
            bar_item = pg.BarGraphItem(x=x_vals, height=y_vals, width=0.6, brush="#2a9df4")
            self.plot_kills.addItem(bar_item)
            self.plot_kills.getAxis("bottom").setTicks(
                [[(i, m.get("date", f"M{i+1}")) for i, m in enumerate(missions)]]
            )
        else:
            self.plot_kills.addItem(pg.TextItem("Sem missões", anchor=(0.5, 0.5)))

        # Vitórias por ás
        self.plot_aces.clear()
        if aces:
            names = [a.get("name", "N/A") for a in aces]
            vals = [int(a.get("victories", 0)) for a in aces]
            y_vals = list(range(len(aces)))
            bar_item = pg.BarGraphItem(
                x0=[0] * len(vals), y=y_vals, height=0.6, width=vals, brush="#ff9933"
            )
            self.plot_aces.addItem(bar_item)
            self.plot_aces.setYRange(-1, len(aces))
            self.plot_aces.getAxis("left").setTicks([[(i, names[i]) for i in y_vals]])
        else:
            self.plot_aces.addItem(pg.TextItem("Nenhum ás", anchor=(0.5, 0.5)))

    # ------------------------
    # Exportações
    # ------------------------
    def _export_png(self):
        if not PG_AVAILABLE:
            QMessageBox.warning(self, "Aviso", "pyqtgraph não está disponível.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salvar gráficos", "stats.png", "PNG Files (*.png)"
        )
        if not file_path:
            return

        try:
            exporter1 = pg.exporters.ImageExporter(self.plot_kills.plotItem)
            exporter1.export(file_path.replace(".png", "_kills.png"))

            exporter2 = pg.exporters.ImageExporter(self.plot_aces.plotItem)
            exporter2.export(file_path.replace(".png", "_aces.png"))

            QMessageBox.information(self, "Sucesso", "Gráficos exportados com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao exportar gráficos: {e}")

    def _export_csv(self):
        if not self.all_data:
            QMessageBox.warning(self, "Aviso", "Nenhum dado carregado.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salvar estatísticas", "stats.csv", "CSV Files (*.csv)"
        )
        if not file_path:
            return

        try:
            with open(file_path, mode="w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Categoria", "Valor"])
                writer.writerow(["Missões do piloto", self.lbl_pilot_missions.text()])
                writer.writerow(["Vitórias do piloto", self.lbl_pilot_kills.text()])
                writer.writerow(["Aeronave principal", self.lbl_pilot_aircraft.text()])
                writer.writerow(["Missões do esquadrão", self.lbl_squadron_missions.text()])
                writer.writerow(["Vitórias do esquadrão", self.lbl_squadron_kills.text()])
                writer.writerow(["Perdas do esquadrão", self.lbl_squadron_losses.text()])
                writer.writerow(["Total de missões", self.lbl_total_missions.text()])
                writer.writerow(["Número de ases", self.lbl_total_aces.text()])

            QMessageBox.information(self, "Sucesso", "Estatísticas exportadas em CSV!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar CSV: {e}")

    def _export_pdf(self):
        if not self.all_data:
            QMessageBox.warning(self, "Aviso", "Nenhum dado carregado.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salvar relatório PDF", "stats.pdf", "PDF Files (*.pdf)"
        )
        if not file_path:
            return

        try:
            plots = {
                "Vitórias por missão": self.plot_kills,
                "Vitórias por ás": self.plot_aces
            }
            generator = IL2ReportGenerator()
            generator.generate_stats_report_pdf(self.all_data, plots, file_path)
            QMessageBox.information(self, "Sucesso", f"Relatório salvo em {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao gerar PDF: {e}")
