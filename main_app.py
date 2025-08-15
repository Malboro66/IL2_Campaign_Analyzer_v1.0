# ===================================================================
#  1. IMPORTS PRINCIPAIS
# ===================================================================
import sys
import os
import json
import re
import logging
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QFileDialog, QLabel, QTabWidget, QTextEdit, 
    QFormLayout, QGroupBox, QComboBox, QMessageBox, QTableWidget, 
    QTableWidgetItem, QHeaderView, QProgressBar, QStatusBar, QSplitter
)
from PyQt5.QtCore import Qt, QSettings, QThread, pyqtSignal
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# ===================================================================
#  2. CONFIGURAÇÃO DE LOGGING
# ===================================================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

# ===================================================================
#  3. CLASSES DE DADOS E LÓGICA (Parser, Processor, PDF)
# ===================================================================

class IL2DataParser:
    """Lê e extrai dados brutos dos arquivos da campanha PWCGFC."""
    def __init__(self, pwcgfc_path):
        self.pwcgfc_path = Path(pwcgfc_path)
        self.campaigns_path = self.pwcgfc_path / 'User' / 'Campaigns'

    def get_json_data(self, file_path: Path) -> Any:
        if not file_path.exists():
            logger.warning(f"Arquivo não encontrado: {file_path}")
            return None
        try:
            with file_path.open('r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Erro ao ler o arquivo JSON {file_path}: {e}")
            return None

    def get_campaigns(self) -> List[str]:
        if not self.campaigns_path.exists():
            return []
        return sorted([p.name for p in self.campaigns_path.iterdir() if p.is_dir()])

    def get_campaign_info(self, campaign_name: str) -> Dict:
        return self.get_json_data(self.campaigns_path / campaign_name / 'Campaign.json') or {}

    def get_squadron_personnel(self, campaign_name: str, squadron_id: int) -> Dict:
        """Carrega o arquivo de pessoal do esquadrão específico."""
        personnel_path = self.campaigns_path / campaign_name / 'Personnel' / f'{squadron_id}.json'
        return self.get_json_data(personnel_path) or {}

    def get_combat_reports(self, campaign_name: str, player_serial: str) -> List[Dict]:
        reports_path = self.campaigns_path / campaign_name / 'CombatReports' / player_serial
        if not reports_path.exists():
            return []
        reports = []
        for report_file in sorted(reports_path.glob('*.json'), reverse=True):
            report_data = self.get_json_data(report_file)
            if report_data:
                reports.append(report_data)
        return reports

    def get_mission_data(self, campaign_name: str, report: Dict) -> Dict:
        mission_data_dir = self.campaigns_path / campaign_name / 'MissionData'
        if not mission_data_dir.exists():
            logger.warning(f"Diretório de dados da missão não encontrado: {mission_data_dir}")
            return {}

        pilot_name = report.get("reportPilotName", "")
        pilot_name_clean = re.sub(r'^(Ltn|Fw|Obltn|Cne|S/Lt|Sergt)\s+', '', pilot_name)
        
        date_str_yyyymmdd = report.get("date", "")
        if not date_str_yyyymmdd:
            return {}

        try:
            date_obj = datetime.strptime(date_str_yyyymmdd, '%Y%m%d')
            date_str_dashed = date_obj.strftime('%Y-%m-%d')
        except ValueError:
            logger.error(f"Formato de data inválido no relatório: {date_str_yyyymmdd}")
            return {}

        for mission_file in mission_data_dir.glob('*.MissionData.json'):
            if pilot_name_clean in mission_file.name and date_str_dashed in mission_file.name:
                logger.info(f"Arquivo de missão correspondente encontrado: {mission_file.name}")
                return self.get_json_data(mission_file) or {}
        
        logger.warning(f"Nenhum arquivo de dados da missão encontrado para {pilot_name_clean} na data {date_str_dashed}")
        return {}


class IL2DataProcessor:
    """Processa os dados brutos, organizando e enriquecendo as informações."""
    def __init__(self, pwcgfc_path):
        self.parser = IL2DataParser(pwcgfc_path)

    def process_campaign(self, campaign_name: str) -> Dict:
        campaign_info = self.parser.get_campaign_info(campaign_name)
        if not campaign_info:
            return {}

        player_serial = str(campaign_info.get('referencePlayerSerialNumber', ''))
        combat_reports = self.parser.get_combat_reports(campaign_name, player_serial)
        
        missions_data, player_squadron_id = self._process_missions_data(campaign_name, combat_reports, player_serial)
        
        pilot_data = self._process_pilot_data(campaign_info, combat_reports)
        
        # Carrega os dados do esquadrão usando o ID encontrado
        squadron_personnel = self.parser.get_squadron_personnel(campaign_name, player_squadron_id)
        squadron_data = self._process_squadron_data(squadron_personnel)

        return {
            'pilot': pilot_data,
            'missions': missions_data,
            'squadron': squadron_data
        }

    def _process_pilot_data(self, campaign_info, combat_reports):
        return {
            'name': campaign_info.get('name', 'N/A'),
            'squadron': combat_reports[0].get('squadron', 'N/A') if combat_reports else 'N/A',
            'total_missions': len(combat_reports),
            'campaign_date': self._format_date(campaign_info.get('date', 'N/A')),
        }

    def _process_missions_data(self, campaign_name, combat_reports, player_serial):
        missions = []
        player_squadron_id = None

        for report in combat_reports:
            mission_details = self.parser.get_mission_data(campaign_name, report)
            
            # Pega a hora incorreta do report como um valor padrão
            mission_time = report.get('time', 'N/A')

            pilots_in_mission = []
            if report.get('haReport'):
                pilots_in_mission = re.findall(r'^(?:Ltn|Fw|Obltn|Cne|S/Lt|Sergt)\s+.*', report['haReport'], re.MULTILINE)

            weather_text = "Não disponível"
            description_text = "Descrição da missão não encontrada."
            if mission_details:
                description_text = mission_details.get('missionDescription', description_text)
                
                # Extrai a hora correta da descrição
                time_match = re.search(r'Time\s+([0-9]{2}:[0-9]{2}:[0-9]{2})', description_text)
                if time_match:
                    mission_time = time_match.group(1) # Sobrescreve com a hora correta

                # Extrai o tempo
                match = re.search(r'Weather Report\s*\n(.*?)\n\nPrimary Objective', description_text, re.DOTALL)
                if match:
                    weather_text = match.group(1).strip()
                
                if not player_squadron_id:
                    mission_planes = mission_details.get('missionPlanes', {})
                    if player_serial in mission_planes:
                        player_squadron_id = mission_planes[player_serial].get('squadronId')

            mission_entry = {
                'date': self._format_date(report.get('date', 'N/A')),
                'time': mission_time, # <-- Usa a variável que agora contém a hora correta
                'aircraft': report.get('type', 'N/A'),
                'duty': report.get('duty', 'N/A'),
                'airfield': mission_details.get('missionHeader', {}).get('airfield', 'N/A'),
                'pilots': pilots_in_mission,
                'weather': weather_text,
                'description': description_text,
            }
            missions.append(mission_entry)
        
        return missions, player_squadron_id


    def _process_squadron_data(self, squadron_personnel):
        squad_members = []
        if not squadron_personnel:
            logger.warning("Arquivo de pessoal do esquadrão não encontrado ou vazio.")
            return squad_members

        squad_collection = squadron_personnel.get('squadronMemberCollection', {})
        for pilot_serial, pilot_info in squad_collection.items():
            squad_members.append({
                'name': pilot_info.get('name', 'N/A'),
                'rank': pilot_info.get('rank', 'N/A'),
                'victories': len(pilot_info.get('victories', [])),
                'missions_flown': pilot_info.get('missionFlown', 0), # <-- NOVA LINHA AQUI
                'status': self._get_pilot_status(pilot_info.get('pilotActiveStatus', -1))
            })

        # Ordenar por missões voadas (mais experientes primeiro)
        squad_members.sort(key=lambda x: x['missions_flown'], reverse=True)
        return squad_members


    def _get_pilot_status(self, status_code):
        return {0: "Ativo", 1: "Ativo", 2: "Morto em Combate (KIA)", 3: "Gravemente Ferido (WIA)", 4: "Capturado (POW)", 5: "Desaparecido em Combate (MIA)"}.get(status_code, "Desconhecido")

    def _format_date(self, date_str):
        if not date_str or len(date_str) != 8:
            return date_str
        try:
            return datetime.strptime(date_str, '%Y%m%d').strftime('%d/%m/%Y')
        except ValueError:
            return date_str


class IL2PDFGenerator:
    """Gera relatórios em PDF para a campanha ou missões específicas."""
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.styles['Title'].fontSize = 20
        self.styles['Title'].alignment = TA_CENTER
        self.styles['Title'].spaceAfter = 20
        self.styles['Title'].textColor = colors.darkblue
        self.styles.add(ParagraphStyle(name='CustomHeading', parent=self.styles['h2'], fontSize=16, alignment=TA_LEFT, spaceAfter=12, spaceBefore=12, textColor=colors.darkslateblue))

    def generate_mission_report(self, mission_data, output_path):
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []
        story.append(Paragraph(f"Relatório de Missão - {mission_data['date']}", self.styles['Title']))
        story.append(Spacer(1, 0.2 * inch))
        info_data = [['Data:', mission_data.get('date', 'N/A')], ['Hora:', mission_data.get('time', 'N/A')], ['Aeronave:', mission_data.get('aircraft', 'N/A')], ['Tipo de Missão:', mission_data.get('duty', 'N/A')], ['Aeródromo de Partida:', mission_data.get('airfield', 'N/A')]]
        info_table = Table(info_data, colWidths=[1.5 * inch, 4.5 * inch])
        info_table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        story.append(info_table)
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph("Condições Meteorológicas", self.styles['CustomHeading']))
        story.append(Paragraph(mission_data.get('weather', 'Não disponível.').replace('\n', ''), self.styles['Normal']))  
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph("Pilotos na Missão", self.styles['CustomHeading']))
        pilots = mission_data.get('pilots', [])
        if pilots:
            list_style = ParagraphStyle(name='list', parent=self.styles['Normal'], leftIndent=15)
            pilot_list = [Paragraph(f"• {name}", list_style) for name in pilots]
            story.extend(pilot_list)
        else:
            story.append(Paragraph("Lista de pilotos não disponível no relatório.", self.styles['Normal']))
        try:
            doc.build(story)
            return True
        except Exception as e:
            logger.error(f"Erro ao gerar PDF da missão: {e}")
            return False

# ===================================================================
#  4. CLASSES DA APLICAÇÃO (Thread, Janela Principal)
# ===================================================================
class DataSyncThread(QThread):
    data_loaded = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    def __init__(self, pwcgfc_path, campaign_name):
        super().__init__()
        self.pwcgfc_path = pwcgfc_path
        self.campaign_name = campaign_name
    def run(self):
        try:
            processor = IL2DataProcessor(self.pwcgfc_path)
            processed_data = processor.process_campaign(self.campaign_name)
            if processed_data:
                self.data_loaded.emit(processed_data)
            else:
                self.error_occurred.emit("Não foi possível carregar os dados da campanha.")
        except Exception as e:
            logger.error(f"Erro na thread de sincronização: {e}")
            self.error_occurred.emit(str(e))

class IL2CampaignAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings('IL2CampaignAnalyzer', 'Settings')
        self.pwcgfc_path = ""
        self.current_data = {}
        self.selected_mission_index = -1
        self.pdf_generator = IL2PDFGenerator()
        self.sync_thread = None
        self.setup_ui()
        self.load_saved_settings()

    def setup_ui(self):
        self.setWindowTitle('IL-2 Campaign Analyzer v1.8 (Final)')
        self.setGeometry(100, 100, 1200, 800)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        self.path_label = QLabel('Nenhum caminho selecionado')
        main_layout.addWidget(self.path_label)
        select_path_button = QPushButton('Selecionar Pasta PWCGFC')
        select_path_button.clicked.connect(self.select_pwcgfc_folder)
        main_layout.addWidget(select_path_button)
        campaign_layout = QHBoxLayout()
        campaign_layout.addWidget(QLabel("Campanha:"))
        self.campaign_combo = QComboBox()
        campaign_layout.addWidget(self.campaign_combo)
        main_layout.addLayout(campaign_layout)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        self.tabs = QTabWidget()
        self.create_tabs()
        main_layout.addWidget(self.tabs)
        buttons_layout = QHBoxLayout()
        sync_button = QPushButton('Sincronizar Dados')
        sync_button.clicked.connect(self.sync_data)
        buttons_layout.addWidget(sync_button)
        self.export_button = QPushButton('Exportar Relatório para PDF')
        self.export_button.clicked.connect(self.export_to_pdf)
        buttons_layout.addWidget(self.export_button)
        main_layout.addLayout(buttons_layout)
        self.setStatusBar(QStatusBar())

    def create_tabs(self):
        self.tab_pilot_profile = QWidget()
        profile_layout = QFormLayout(self.tab_pilot_profile)
        self.pilot_name_label = QLabel("N/A")
        self.squadron_name_label = QLabel("N/A")
        self.total_missions_label = QLabel("N/A")
        profile_layout.addRow("Nome:", self.pilot_name_label)
        profile_layout.addRow("Esquadrão:", self.squadron_name_label)
        profile_layout.addRow("Missões Voadas:", self.total_missions_label)
        self.tabs.addTab(self.tab_pilot_profile, 'Perfil do Piloto')

        self.tab_squadron = QWidget()
        squadron_layout = QVBoxLayout(self.tab_squadron)
        self.squadron_table = QTableWidget()
        # --- ALTERAÇÃO AQUI: de 4 para 5 colunas ---
        self.squadron_table.setColumnCount(5)
        self.squadron_table.setHorizontalHeaderLabels(["Nome", "Patente", "Abates", "Missões Voadas", "Status"])
        self.squadron_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.squadron_table.setSelectionBehavior(QTableWidget.SelectRows)
        squadron_layout.addWidget(self.squadron_table)
        self.tabs.addTab(self.tab_squadron, 'Esquadrão')

        self.tab_missions = QWidget()
        missions_layout = QVBoxLayout(self.tab_missions)
        splitter = QSplitter(Qt.Vertical)
        self.missions_table = QTableWidget()
        self.missions_table.setColumnCount(4)
        self.missions_table.setHorizontalHeaderLabels(["Data", "Hora", "Aeronave", "Tipo de Missão"])
        self.missions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.missions_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.missions_table.setSelectionMode(QTableWidget.SingleSelection)
        self.missions_table.itemSelectionChanged.connect(self.on_mission_selected)
        details_group = QGroupBox("Detalhes da Missão Selecionada")
        details_layout = QVBoxLayout()
        self.mission_details_text = QTextEdit()
        self.mission_details_text.setReadOnly(True)
        details_layout.addWidget(self.mission_details_text)
        details_group.setLayout(details_layout)
        splitter.addWidget(self.missions_table)
        splitter.addWidget(details_group)
        splitter.setSizes([400, 200])
        missions_layout.addWidget(splitter)
        self.tabs.addTab(self.tab_missions, 'Missões')


    def select_pwcgfc_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, 'Selecionar Pasta PWCGFC')
        if folder_path:
            self.pwcgfc_path = folder_path
            self.path_label.setText(f'Caminho: {folder_path}')
            self.settings.setValue('pwcgfc_path', self.pwcgfc_path)
            self.load_campaigns()

    def load_campaigns(self):
        if not self.pwcgfc_path:
            return
        parser = IL2DataParser(self.pwcgfc_path)
        campaigns = parser.get_campaigns()
        self.campaign_combo.clear()
        self.campaign_combo.addItems(campaigns)

    def sync_data(self):
        current_campaign = self.campaign_combo.currentText()
        if not self.pwcgfc_path or not current_campaign:
            QMessageBox.warning(self, "Aviso", "Selecione a pasta e uma campanha primeiro!")
            return
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.sync_thread = DataSyncThread(self.pwcgfc_path, current_campaign)
        self.sync_thread.data_loaded.connect(self.on_data_loaded)
        self.sync_thread.error_occurred.connect(self.on_sync_error)
        self.sync_thread.start()

    def on_data_loaded(self, data):
        self.current_data = data
        self.update_ui_with_data()
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("Dados carregados com sucesso!", 5000)

    def on_sync_error(self, error_message):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Erro de Sincronização", error_message)
        self.statusBar().showMessage("Falha ao carregar dados.", 5000)

    def update_ui_with_data(self):
        self.selected_mission_index = -1
        self.export_button.setText("Exportar Relatório para PDF")
        self.mission_details_text.clear()

        pilot_data = self.current_data.get('pilot', {})
        self.pilot_name_label.setText(pilot_data.get('name', 'N/A'))
        self.squadron_name_label.setText(pilot_data.get('squadron', 'N/A'))
        self.total_missions_label.setText(str(pilot_data.get('total_missions', '0')))

        squadron_data = self.current_data.get('squadron', [])
        self.squadron_table.setRowCount(len(squadron_data))
        for row, member in enumerate(squadron_data):
            name_item = QTableWidgetItem(member.get('name'))
            rank_item = QTableWidgetItem(member.get('rank'))
            victories_item = QTableWidgetItem(str(member.get('victories')))
            # --- NOVA LINHA AQUI ---
            missions_item = QTableWidgetItem(str(member.get('missions_flown')))
            status_item = QTableWidgetItem(member.get('status'))

            # Torna cada item não editável
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            rank_item.setFlags(rank_item.flags() & ~Qt.ItemIsEditable)
            victories_item.setFlags(victories_item.flags() & ~Qt.ItemIsEditable)
            missions_item.setFlags(missions_item.flags() & ~Qt.ItemIsEditable) # <-- NOVA LINHA AQUI
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)

            # Adiciona os itens à tabela
            self.squadron_table.setItem(row, 0, name_item)
            self.squadron_table.setItem(row, 1, rank_item)
            self.squadron_table.setItem(row, 2, victories_item)
            self.squadron_table.setItem(row, 3, missions_item) # <-- NOVA LINHA AQUI
            self.squadron_table.setItem(row, 4, status_item)   # <-- Índice da coluna mudou de 3 para 4

        missions_data = self.current_data.get('missions', [])
        self.missions_table.setRowCount(len(missions_data))
        for row, mission in enumerate(missions_data):
            date_item = QTableWidgetItem(mission.get('date'))
            time_item = QTableWidgetItem(mission.get('time'))
            aircraft_item = QTableWidgetItem(mission.get('aircraft'))
            duty_item = QTableWidgetItem(mission.get('duty'))

            # Torna cada item não editável
            date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
            time_item.setFlags(time_item.flags() & ~Qt.ItemIsEditable)
            aircraft_item.setFlags(aircraft_item.flags() & ~Qt.ItemIsEditable)
            duty_item.setFlags(duty_item.flags() & ~Qt.ItemIsEditable)

            self.missions_table.setItem(row, 0, date_item)
            self.missions_table.setItem(row, 1, time_item)
            self.missions_table.setItem(row, 2, aircraft_item)
            self.missions_table.setItem(row, 3, duty_item)


    def on_mission_selected(self):
        selected_items = self.missions_table.selectedItems()
        if selected_items:
            self.selected_mission_index = selected_items[0].row()
            self.export_button.setText(f"Exportar Missão de {self.missions_table.item(self.selected_mission_index, 0).text()} para PDF")
            mission_data = self.current_data['missions'][self.selected_mission_index]
            self.mission_details_text.setText(mission_data.get('description', ''))
        else:
            self.selected_mission_index = -1
            self.export_button.setText("Exportar Relatório para PDF")
            self.mission_details_text.clear()

    def export_to_pdf(self):
        if not self.current_data:
            QMessageBox.warning(self, "Aviso", "Sincronize os dados primeiro!")
            return
        if self.selected_mission_index != -1:
            mission_to_export = self.current_data['missions'][self.selected_mission_index]
            default_filename = f"Missao_{mission_to_export['date'].replace('/', '-')}.pdf"
            file_path, _ = QFileDialog.getSaveFileName(self, 'Salvar Relatório da Missão', default_filename, 'PDF (*.pdf)')
            if file_path:
                success = self.pdf_generator.generate_mission_report(mission_to_export, file_path)
                if success:
                    QMessageBox.information(self, "Sucesso", f"Relatório da missão salvo em: {file_path}")
                else:
                    QMessageBox.critical(self, "Erro", "Não foi possível gerar o PDF da missão.")
        else:
            QMessageBox.information(self, "Aviso", "Selecione uma missão na tabela para exportar seu relatório detalhado.")

    def load_saved_settings(self):
        saved_path = self.settings.value('pwcgfc_path', '')
        if saved_path and os.path.exists(saved_path):
            self.pwcgfc_path = saved_path
            self.path_label.setText(f'Caminho: {saved_path}')
            self.load_campaigns()

    def closeEvent(self, event):
        self.settings.setValue('pwcgfc_path', self.pwcgfc_path)
        event.accept()

# ===================================================================
#  5. PONTO DE ENTRADA DA APLICAÇÃO
# ===================================================================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = IL2CampaignAnalyzer()
    ex.show()
    sys.exit(app.exec_())
