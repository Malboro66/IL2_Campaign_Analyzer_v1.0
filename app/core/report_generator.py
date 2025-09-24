"""
Generates reports from processed campaign data.

This module provides functionality to create various types of reports,
including plain text campaign diaries and detailed PDF summaries for
missions and overall statistics, optionally including plots.
"""
from __future__ import annotations
import tempfile
from typing import Dict, Any, List
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

try:
    import pyqtgraph as pg  # noqa: F401
    from pyqtgraph.exporters import ImageExporter
    PG_AVAILABLE = True
except Exception:
    PG_AVAILABLE = False

class IL2ReportGenerator:
    """
    Generates reports from processed IL-2 campaign data.
    """
    def generate_campaign_diary_txt(self, data: Dict[str, Any]) -> str:
        """
        Generate a plain text campaign diary.

        Args:
            data (Dict[str, Any]): The processed campaign data.

        Returns:
            str: The generated diary as a single string.
        """
        pilot = data.get("pilot", {}); missions = data.get("missions", [])
        lines: List[str] = []
        lines.append(f"Diário de Bordo - {pilot.get('name', 'Piloto')}")
        lines.append(f"Esquadrão: {pilot.get('squadron', 'N/A')}")
        lines.append(f"Total de Missões: {pilot.get('total_missions', 0)}")
        lines.append(f"Vitórias: {pilot.get('kills', 0)}")
        lines.append("=" * 50); lines.append("")
        for idx, mission in enumerate(missions, start=1):
            lines.append(f"Missão {idx} - {mission.get('date', 'N/A')}")
            lines.append(f" Aeronave: {mission.get('aircraft', 'N/A')}")
            lines.append(f" Status: {mission.get('status', 'N/A')}")
            lines.append(f" Vitórias: {mission.get('kills', 0)}")
            lines.append(f" Perdas: {mission.get('losses', 0)}")
            lines.append("")
        return "\n".join(lines)

    def generate_mission_report_pdf(self, mission_data: Dict[str, Any], all_missions: List[Dict[str, Any]], mission_index: int, output_path: str) -> bool:
        """
        Generate a detailed PDF report for a single mission.

        Args:
            mission_data (Dict[str, Any]): Data for the specific mission.
            all_missions (List[Dict[str, Any]]): List of all missions for context.
            mission_index (int): The index of the mission in `all_missions`.
            output_path (str): The file path to save the generated PDF.

        Returns:
            bool: True if the PDF was generated successfully, False otherwise.
        """
        if not mission_data: return False
        try:
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            styles = getSampleStyleSheet(); story: List[Any] = []
            story.append(Paragraph("Relatório de Missão", styles["Title"]))
            story.append(Spacer(1, 20))
            story.append(Paragraph(f"Data: {mission_data.get('date', 'N/A')}", styles["Normal"]))
            story.append(Paragraph(f"Aeronave: {mission_data.get('aircraft', 'N/A')}", styles["Normal"]))
            story.append(Paragraph(f"Tipo: {mission_data.get('type', 'N/A')}", styles["Normal"]))
            story.append(Paragraph(f"Esquadrão: {mission_data.get('squadron', 'N/A')}", styles["Normal"]))
            story.append(Paragraph(f"Aeródromo: {mission_data.get('airfield', 'N/A')}", styles["Normal"]))
            if mission_data.get("altitude_m") is not None:
                story.append(Paragraph(f"Altitude: {mission_data['altitude_m']} m", styles["Normal"]))
            story.append(Spacer(1, 10))
            stats_table = Table([
                ["Companheiros de esquadrão", ", ".join(mission_data.get("squadmates", [])) or "-"],
                ["Vitórias", mission_data.get("kills", 0)],
                ["Perdas", mission_data.get("losses", 0)],
            ], colWidths=[200, 300])
            stats_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), colors.lightgrey),
                ("BACKGROUND", (0, 1), (0, 2), colors.whitesmoke),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
            ]))
            story.append(stats_table); story.append(Spacer(1, 20))
            report = mission_data.get("report", {}) or {}
            if report.get("haReport") or report.get("narrative"):
                story.append(Paragraph("Debriefing", styles["Heading2"]))
                if report.get("haReport"):
                    story.append(Paragraph(report["haReport"].replace("\n", "<br/>"), styles["Normal"]))
                    story.append(Spacer(1, 10))
                if report.get("narrative"):
                    story.append(Paragraph(report["narrative"].replace("\n", "<br/>"), styles["Normal"]))
                    story.append(Spacer(1, 10))
            if mission_index > 0:
                prev = all_missions[mission_index - 1]
                story.append(Paragraph(f"Missão anterior: {prev.get('date', 'N/A')}", styles["Italic"]))
            if mission_index < len(all_missions) - 1:
                nxt = all_missions[mission_index + 1]
                story.append(Paragraph(f"Próxima missão: {nxt.get('date', 'N/A')}", styles["Italic"]))
            doc.build(story)
            return True
        except Exception as e:
            print(f"[ERRO] Falha ao gerar PDF de missão: {e}")
            return False

    def generate_stats_report_pdf(self, stats_data: Dict[str, Any], plots: Dict[str, Any], output_path: str) -> bool:
        """
        Generate a PDF report with overall campaign statistics and plots.

        Args:
            stats_data (Dict[str, Any]): The processed campaign statistics data.
            plots (Dict[str, Any]): A dictionary of pyqtgraph plot widgets to include.
            output_path (str): The file path to save the generated PDF.

        Returns:
            bool: True if the PDF was generated successfully, False otherwise.
        """
        if not stats_data: return False
        try:
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            styles = getSampleStyleSheet(); story: List[Any] = []
            story.append(Paragraph("Relatório de Estatísticas da Campanha", styles["Title"]))
            story.append(Spacer(1, 20))
            pilot = stats_data.get("pilot", {}) or {}
            story.append(Paragraph("Piloto", styles["Heading2"]))
            pilot_table = Table([
                ["Nome", pilot.get("name", "N/A")],
                ["Esquadrão", pilot.get("squadron", "N/A")],
                ["Missões voadas", pilot.get("total_missions", 0)],
                ["Vitórias", pilot.get("kills", 0)],
                ["Aeronave principal", pilot.get("aircraft", "N/A")],
            ], colWidths=[200, 300])
            pilot_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
            ]))
            story.append(pilot_table); story.append(Spacer(1, 20))
            squad = stats_data.get("squadron", {}) or {}
            story.append(Paragraph("Esquadrão", styles["Heading2"]))
            squad_table = Table([
                ["Missões registradas", squad.get("total_missions", 0)],
                ["Vitórias totais", squad.get("total_kills", 0)],
            ], colWidths=[200, 300])
            squad_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
            ]))
            story.append(squad_table); story.append(Spacer(1, 20))
            campaign = stats_data.get("campaign", {}) or {}
            story.append(Paragraph("Campanha", styles["Heading2"]))
            camp_table = Table([
                ["Total de missões", campaign.get("missions", len(stats_data.get("missions", [])))],
                ["Número de ases", campaign.get("aces", len(stats_data.get("aces", [])))],
            ], colWidths=[200, 300])
            camp_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
            ]))
            story.append(camp_table); story.append(Spacer(1, 20))
            if PG_AVAILABLE and plots:
                for name, plot_widget in plots.items():
                    try:
                        tmp_file = tempfile.mktemp(suffix=".png")
                        exporter = ImageExporter(plot_widget.plotItem)
                        exporter.export(tmp_file)
                        story.append(Paragraph(f"{name}", styles["Heading3"]))
                        story.append(Image(tmp_file, width=400, height=200))
                        story.append(Spacer(1, 20))
                    except Exception as e:
                        story.append(Paragraph(f"Erro ao exportar gráfico {name}: {e}", styles["Normal"]))
            doc.build(story)
            return True
        except Exception as e:
            print(f"[ERRO] Falha ao gerar PDF de estatísticas: {e}")
            return False
