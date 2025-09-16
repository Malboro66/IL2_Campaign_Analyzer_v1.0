# app/core/report_generator.py
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
import tempfile
import os

try:
    import pyqtgraph as pg
except Exception:
    pg = None


class IL2ReportGenerator:
    ...
    def generate_stats_report_pdf(self, stats_data, plots, output_path):
        """
        Gera PDF consolidado de estatísticas + gráficos.
        stats_data: dict com 'pilot', 'squadron', 'campaign'
        plots: dict com { "kills_plot": PlotWidget, "aces_plot": PlotWidget }
        """
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Título
        story.append(Paragraph("<b>Relatório de Estatísticas da Campanha</b>", styles["Title"]))
        story.append(Spacer(1, 20))

        # --- Resumo piloto
        pilot = stats_data.get("pilot", {})
        story.append(Paragraph("<b>Piloto</b>", styles["Heading2"]))
        pilot_table = Table([
            ["Nome", pilot.get("name", "N/A")],
            ["Esquadrão", pilot.get("squadron", "N/A")],
            ["Missões voadas", pilot.get("total_missions", "0")],
            ["Vitórias", pilot.get("kills", "0")],
            ["Aeronave principal", pilot.get("aircraft", "N/A")],
        ], colWidths=[150, 300])
        pilot_table.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), colors.lightgrey)]))
        story.append(pilot_table)
        story.append(Spacer(1, 20))

        # --- Resumo esquadrão
        squad = stats_data.get("squadron", {})
        story.append(Paragraph("<b>Esquadrão</b>", styles["Heading2"]))
        squad_table = Table([
            ["Missões registradas", squad.get("missions", "0")],
            ["Vitórias totais", squad.get("kills", "0")],
            ["Perdas em combate", squad.get("losses", "0")],
        ], colWidths=[150, 300])
        squad_table.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), colors.lightgrey)]))
        story.append(squad_table)
        story.append(Spacer(1, 20))

        # --- Resumo campanha
        camp = stats_data.get("campaign", {})
        story.append(Paragraph("<b>Campanha</b>", styles["Heading2"]))
        camp_table = Table([
            ["Total de missões", camp.get("missions", "0")],
            ["Número de ases", camp.get("aces", "0")],
        ], colWidths=[150, 300])
        camp_table.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), colors.lightgrey)]))
        story.append(camp_table)
        story.append(Spacer(1, 20))

        # --- Gráficos (salvos como PNG temporários e embutidos no PDF)
        if pg and plots:
            for name, plot_widget in plots.items():
                try:
                    tmp_file = tempfile.mktemp(suffix=".png")
                    exporter = pg.exporters.ImageExporter(plot_widget.plotItem)
                    exporter.export(tmp_file)
                    story.append(Paragraph(f"<b>{name}</b>", styles["Heading3"]))
                    story.append(Image(tmp_file, width=400, height=200))
                    story.append(Spacer(1, 20))
                except Exception as e:
                    story.append(Paragraph(f"Erro ao exportar gráfico {name}: {e}", styles["Normal"]))

        doc.build(story)
        return True
