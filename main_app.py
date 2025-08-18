# ===================================================================
#  1. IMPORTS PRINCIPAIS
# ===================================================================
import sys
import os
import json
import re
import random 
import logging
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QFileDialog, QLabel, QTabWidget, QTextEdit, 
    QFormLayout, QGroupBox, QComboBox, QMessageBox, QTableWidget, 
    QTableWidgetItem, QHeaderView, QProgressBar, QStatusBar, QSplitter,QScrollArea
)
from PyQt5.QtGui import QPixmap
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
        
        if player_squadron_id:
            squadron_personnel = self.parser.get_squadron_personnel(campaign_name, player_squadron_id)
            squadron_data = self._process_squadron_data(squadron_personnel)
        else:
            squadron_data = []
            logger.warning("Não foi possível determinar o squadronId do jogador. A aba de esquadrão ficará vazia.")

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
            # --- LÓGICA MOVIDA PARA DENTRO DO LOOP ---
            mission_details = self.parser.get_mission_data(campaign_name, report)
            mission_time = report.get('time', 'N/A')
            pilots_in_mission = []
            if report.get('haReport'):
                pilots_in_mission = re.findall(r'^(?:Ltn|Fw|Obltn|Cne|S/Lt|Sergt)\s+.*', report['haReport'], re.MULTILINE)

            weather_text = "Não disponível"
            description_text = "Descrição da missão não encontrada."
            if mission_details:
                description_text = mission_details.get('missionDescription', description_text)
                time_match = re.search(r'Time\s+([0-9]{2}:[0-9]{2}:[0-9]{2})', description_text)
                if time_match:
                    mission_time = time_match.group(1)
                match = re.search(r'Weather Report\s*\n(.*?)\n\nPrimary Objective', description_text, re.DOTALL)
                if match:
                    weather_text = match.group(1).strip()
                if not player_squadron_id:
                    mission_planes = mission_details.get('missionPlanes', {})
                    if player_serial in mission_planes:
                        player_squadron_id = mission_planes[player_serial].get('squadronId')

            mission_entry = {
                'date': self._format_date(report.get('date', 'N/A')),
                'time': mission_time,
                'aircraft': report.get('type', 'N/A'),
                'duty': report.get('duty', 'N/A'),
                'locality': report.get('locality', 'N/A'),
                'airfield': mission_details.get('missionHeader', {}).get('airfield', 'N/A'),
                'pilots': pilots_in_mission,
                'weather': weather_text,
                'description': description_text,
            }
            missions.append(mission_entry)
        
        return missions, player_squadron_id

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
            mission_time = report.get('time', 'N/A')
            pilots_in_mission = []
        if report.get('haReport'):
            pilots_in_mission = re.findall(r'^(?:Ltn|Fw|Obltn|Cne|S/Lt|Sergt)\s+.*', report['haReport'], re.MULTILINE)

        weather_text = "Não disponível"
        description_text = "Descrição da missão não encontrada."
        if mission_details:
            description_text = mission_details.get('missionDescription', description_text)
            time_match = re.search(r'Time\s+([0-9]{2}:[0-9]{2}:[0-9]{2})', description_text)
            if time_match:
                mission_time = time_match.group(1)
            match = re.search(r'Weather Report\s*\n(.*?)\n\nPrimary Objective', description_text, re.DOTALL)
            if match:
                weather_text = match.group(1).strip()
            if not player_squadron_id:
                mission_planes = mission_details.get('missionPlanes', {})
                if player_serial in mission_planes:
                    player_squadron_id = mission_planes[player_serial].get('squadronId')

        mission_entry = {
            'date': self._format_date(report.get('date', 'N/A')),
            'time': mission_time,
            'aircraft': report.get('type', 'N/A'),
            'duty': report.get('duty', 'N/A'),
            'locality': report.get('locality', 'N/A'), # <-- GARANTIR QUE ESTÁ AQUI
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

class IL2ReportGenerator:
    """Gera relatórios em PDF, texto e imagens de mapa."""
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.styles['Title'].fontSize = 20
        self.styles['Title'].alignment = TA_CENTER
        self.styles['Title'].spaceAfter = 20
        self.styles['Title'].textColor = colors.darkblue
        self.styles.add(ParagraphStyle(name='CustomHeading', parent=self.styles['h2'], fontSize=16, alignment=TA_LEFT, spaceAfter=12, spaceBefore=12, textColor=colors.darkslateblue))
        
        self.map_coordinates = self._load_map_coordinates()

    def _load_map_coordinates(self):
        """Carrega o dicionário de coordenadas do arquivo JSON."""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            coords_path = os.path.join(script_dir, "coordenadas_mapa_final_calibrado.json")
            with open(coords_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("Arquivo 'coordenadas_mapa_final_calibrado.json' não encontrado!")
            return {}
        except Exception as e:
            logger.error(f"Erro ao carregar coordenadas do mapa: {e}")
            return {}
        
    def gerar_mapa_de_carreira(self, missoes: list, output_path: str, highlight_mission_index: int = -1):
        """
        Gera a imagem do mapa.
        Se highlight_mission_index for -1, desenha a rota completa.
        Se for um número, destaca apenas a missão naquele índice.
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        mapa_base_path = os.path.join(script_dir, "mapa_base.jpg")
    
        if not os.path.exists(mapa_base_path) or not self.map_coordinates:
            return False
        
        try:
            img = Image.open(mapa_base_path).convert("RGB")
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype("arial.ttf", 40)
            
            if highlight_mission_index != -1 and highlight_mission_index < len(missoes):
                missao = missoes[highlight_mission_index]
                localidade = missao.get('locality')
                if localidade in self.map_coordinates:
                    ponto = self.map_coordinates[localidade]
                    raio = 30
                    draw.ellipse((ponto[0] - raio, ponto[1] - raio, ponto[0] + raio, ponto[1] + raio), outline="yellow", width=5)
                    draw.ellipse((ponto[0] - raio*2, ponto[1] - raio*2, ponto[0] + raio*2, ponto[1] + raio*2), outline="yellow", width=2)
                    draw.text((ponto[0] + 40, ponto[1]), f"<- {localidade}", font=font, fill="yellow", stroke_width=2, stroke_fill="black")
            else:
                ponto_anterior = None
                for i, missao in enumerate(missoes):
                    localidade = missao.get('locality')
                    if localidade in self.map_coordinates:
                        ponto_atual = self.map_coordinates[localidade]
                        if ponto_anterior:
                            draw.line([ponto_anterior, ponto_atual], fill="yellow", width=5)
                        raio = 15
                        draw.ellipse((ponto_atual[0] - raio, ponto_atual[1] - raio, ponto_atual[0] + raio, ponto_atual[1] + raio), fill="#FF0000", outline="black", width=3)
                        draw.text((ponto_atual[0] + 25, ponto_atual[1] - 25), str(i + 1), font=font, fill="white", stroke_width=2, stroke_fill="black")
                        ponto_anterior = ponto_atual
            
            img.save(output_path)
            return True
        except Exception as e:
            logger.error(f"Falha ao gerar imagem do mapa: {e}")
            return False
    
    def generate_mission_report_pdf(self, mission_data, all_missions, mission_index, output_path):
        """Gera um relatório em PDF para uma única missão, incluindo um mini-mapa."""
        mini_map_path = "mini_mapa_temp.png"
        map_success = self.gerar_mapa_de_carreira(
            missoes=all_missions,
            output_path=mini_map_path,
            highlight_mission_index=mission_index
        )
        
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

        if map_success and os.path.exists(mini_map_path):
            story.append(Spacer(1, 0.3 * inch))
            story.append(Paragraph("Localização da Missão", self.styles['CustomHeading']))
            
            # Importa as classes do ReportLab necessárias aqui para evitar conflito
            from reportlab.platypus import Image as ReportLabImage
            from reportlab.lib.utils import ImageReader

            img = ImageReader(mini_map_path)
            img_width, img_height = img.getSize()
            aspect = img_height / float(img_width)
            display_width = 6 * inch
            story.append(ReportLabImage(mini_map_path, width=display_width, height=(display_width * aspect)))

        try:
            doc.build(story)
            if os.path.exists(mini_map_path):
                os.remove(mini_map_path)
            return True
        except Exception as e:
            logger.error(f"Erro ao gerar PDF da missão: {e}")
            return False

    def _gerar_entrada_diario(self, missao: dict, piloto_nome: str) -> str:
        """Gera uma entrada de diário narrativa para uma única missão."""
        try:
            data_obj = datetime.strptime(missao['date'], '%d/%m/%Y')
            data_formatada = data_obj.strftime('%d de %B de %Y')
        except (ValueError, TypeError):
            data_formatada = missao['date']
        narrativa = f"**{data_formatada}**\n\n"
        frases_clima = [
            f"O dia começou com o tempo {missao.get('weather', 'indefinido').lower()}. Partimos de {missao.get('airfield', 'base desconhecida')} por volta das {missao.get('time', 'hora incerta')}.",
            f"As condições hoje eram de {missao.get('weather', 'tempo incerto')}. Decolamos de {missao.get('airfield', 'nossa base')} às {missao.get('time', 'hora incerta')}.",
        ]
        narrativa += random.choice(frases_clima)
        narrativa += f" Minha tarefa era uma missão de '{missao.get('duty', 'tipo desconhecido')}' no meu {missao.get('aircraft', 'aeronave')}. "
        if missao.get('pilots'):
            companheiros = [p.split()[-1] for p in missao['pilots'] if piloto_nome not in p][:3]
            if companheiros:
                narrativa += f"Voaram comigo hoje os camaradas {', '.join(companheiros)}. "
        narrativa += "A patrulha ocorreu sem grandes incidentes e retornamos em segurança."
        narrativa += "\n" + ("-" * 80) + "\n"
        return narrativa

    def generate_campaign_diary_txt(self, campaign_data: dict) -> str:
        """Gera o texto completo do diário de bordo a partir dos dados da campanha."""
        piloto = campaign_data.get('pilot', {})
        try:
            missoes = sorted(campaign_data.get('missions', []), key=lambda m: datetime.strptime(m['date'], '%d/%m/%Y'))
        except (ValueError, TypeError):
            missoes = campaign_data.get('missions', [])
            piloto_nome = piloto.get('name', 'N/A')
            diario = "================================================================================\n"
            diario += "                   DIÁRIO DE BORDO DE CAMPANHA\n"
            diario += "================================================================================\n\n"
            diario += f"Piloto: {piloto_nome}\n"
            diario += f"Esquadrão: {piloto.get('squadron', 'N/A')}\n"
            if missoes:
                diario += f"Período da Campanha: {missoes[0]['date']} a {missoes[-1]['date']}\n"
                diario += "\n================================================================================\n\n"
            for missao in missoes:
                    diario += self._gerar_entrada_diario(missao, piloto_nome)
            return diario
  
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
            
class MapViewer(QScrollArea):
    """
    Um widget que exibe uma imagem com suporte a zoom e barras de rolagem.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.zoom_factor = 1.0
        self._pixmap = QPixmap()

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.setWidget(self.image_label)
        self.setWidgetResizable(True)

    def set_pixmap(self, pixmap):
        """Define o pixmap original e ajusta a exibição inicial."""
        self._pixmap = pixmap
        self.fit_to_view() # <-- CHAMA A NOVA FUNÇÃO

    def fit_to_view(self):
        """Ajusta o zoom para que a imagem inteira caiba na área visível."""
        if self._pixmap.isNull():
            return
        
        # Obtém o tamanho da área de rolagem (a viewport)
        view_size = self.viewport().size()
        pixmap_size = self._pixmap.size()
        
        # Calcula o fator de zoom para largura e altura
        width_ratio = view_size.width() / pixmap_size.width()
        height_ratio = view_size.height() / pixmap_size.height()
        
        # Usa o menor fator para garantir que a imagem inteira caiba
        self.zoom_factor = min(width_ratio, height_ratio)
        self.update_zoom()

    def wheelEvent(self, event):
        """Captura o evento da roda do mouse para aplicar zoom."""
        if event.angleDelta().y() > 0:
            self.zoom_factor *= 1.25
        else:
            self.zoom_factor /= 1.25
        
        self.zoom_factor = max(0.1, min(self.zoom_factor, 10.0))
        self.update_zoom()

    def update_zoom(self):
        """Aplica o fator de zoom redimensionando a QLabel interna."""
        if not self._pixmap.isNull():
            # Desativa o resizable para que as barras de rolagem funcionem
            self.setWidgetResizable(False)
            scaled_pixmap = self._pixmap.scaled(self._pixmap.size() * self.zoom_factor, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.adjustSize() # Ajusta o tamanho da label para o da imagem com zoom
          
class IL2CampaignAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings('IL2CampaignAnalyzer', 'Settings')
        self.pwcgfc_path = ""
        self.current_data = {}
        self.selected_mission_index = -1
        self.report_generator = IL2ReportGenerator()
        self.sync_thread = None
        self.setup_ui()
        self.load_saved_settings()
        
    def setup_ui(self):
        self.setWindowTitle('IL-2 Campaign Analyzer v0.3')
        self.setGeometry(100, 100, 1200, 800)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # ... (o resto da sua configuração de UI continua igual) ...
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
        
        # --- LAYOUT DE BOTÕES CORRIGIDO ---
        buttons_layout = QHBoxLayout()
        sync_button = QPushButton('Sincronizar Dados')
        sync_button.clicked.connect(self.sync_data)
        buttons_layout.addWidget(sync_button)

        # Botão para o diário de bordo (começa desabilitado)
        self.diary_button = QPushButton('Gerar Diário de Bordo (.txt)')
        self.diary_button.clicked.connect(self.export_diary)
        self.diary_button.setEnabled(False) # Começa desabilitado
        buttons_layout.addWidget(self.diary_button)

        # Botão para o PDF da missão (começa desabilitado)
        self.export_pdf_button = QPushButton('Exportar Missão para PDF')
        self.export_pdf_button.clicked.connect(self.export_mission_pdf)
        self.export_pdf_button.setEnabled(False) # Começa desabilitado
        buttons_layout.addWidget(self.export_pdf_button)
        
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
        self.tab_map = QWidget()
        map_layout = QVBoxLayout(self.tab_map)
        # Usa a nova classe MapViewer
        self.map_viewer = MapViewer()
        map_layout.addWidget(self.map_viewer)
        self.tabs.addTab(self.tab_map, "Mapa da Carreira")


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
        """Chamado quando os dados da campanha são carregados com sucesso."""
        self.current_data = data
        self.update_ui_with_data()
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("Dados carregados com sucesso!", 5000)

    # --- LÓGICA ATUALIZADA PARA GERAR E EXIBIR O MAPA ---
    # O MapViewer não tem um método setText, então não mostramos a mensagem aqui.
    # Poderíamos adicionar uma label de status se quiséssemos.
        QApplication.processEvents()

        map_output_path = "Mapa_de_Carreira_Gerado.png"
        success = self.report_generator.gerar_mapa_de_carreira(
            self.current_data.get('missions', []),
            map_output_path
    )

        if  success and os.path.exists(map_output_path):
        # Usa o método set_pixmap do nosso novo MapViewer
            self.map_viewer.set_pixmap(QPixmap(map_output_path))
        else:
        # Se falhar, podemos mostrar uma mensagem na label interna do MapViewer
            self.map_viewer.image_label.setText("Não foi possível gerar o mapa de carreira.")

    def on_sync_error(self, error_message):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Erro de Sincronização", error_message)
        self.statusBar().showMessage("Falha ao carregar dados.", 5000)

    def update_ui_with_data(self):
        # Desabilitar botões no início do update para um estado limpo
        self.export_pdf_button.setEnabled(False)
        self.diary_button.setEnabled(False)
        
        self.selected_mission_index = -1
        self.mission_details_text.clear()

        # ... (o resto do código de preenchimento das tabelas permanece o mesmo) ...
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
            missions_item = QTableWidgetItem(str(member.get('missions_flown')))
            status_item = QTableWidgetItem(member.get('status'))

            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            rank_item.setFlags(rank_item.flags() & ~Qt.ItemIsEditable)
            victories_item.setFlags(victories_item.flags() & ~Qt.ItemIsEditable)
            missions_item.setFlags(missions_item.flags() & ~Qt.ItemIsEditable)
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)

            self.squadron_table.setItem(row, 0, name_item)
            self.squadron_table.setItem(row, 1, rank_item)
            self.squadron_table.setItem(row, 2, victories_item)
            self.squadron_table.setItem(row, 3, missions_item)
            self.squadron_table.setItem(row, 4, status_item)

        missions_data = self.current_data.get('missions', [])
        self.missions_table.setRowCount(len(missions_data))
        for row, mission in enumerate(missions_data):
            date_item = QTableWidgetItem(mission.get('date'))
            time_item = QTableWidgetItem(mission.get('time'))
            aircraft_item = QTableWidgetItem(mission.get('aircraft'))
            duty_item = QTableWidgetItem(mission.get('duty'))

            date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
            time_item.setFlags(time_item.flags() & ~Qt.ItemIsEditable)
            aircraft_item.setFlags(aircraft_item.flags() & ~Qt.ItemIsEditable)
            duty_item.setFlags(duty_item.flags() & ~Qt.ItemIsEditable)

            self.missions_table.setItem(row, 0, date_item)
            self.missions_table.setItem(row, 1, time_item)
            self.missions_table.setItem(row, 2, aircraft_item)
            self.missions_table.setItem(row, 3, duty_item)
            
        # Habilita o botão do diário se os dados foram carregados com sucesso
        if self.current_data:
            self.diary_button.setEnabled(True)


    def on_mission_selected(self):
        selected_items = self.missions_table.selectedItems()
        if selected_items:
            self.selected_mission_index = selected_items[0].row()
            # Habilita o botão de exportar PDF da missão
            self.export_pdf_button.setEnabled(True)
            mission_data = self.current_data['missions'][self.selected_mission_index]
            self.mission_details_text.setText(mission_data.get('description', ''))
        else:
            self.selected_mission_index = -1
            # Desabilita o botão se nenhuma missão estiver selecionada
            self.export_pdf_button.setEnabled(False)
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
            
    def export_diary(self):
        """Função para gerar e salvar o diário de bordo."""
        if not self.current_data:
            QMessageBox.warning(self, "Aviso", "Sincronize os dados de uma campanha primeiro!")
            return

        diary_content = self.report_generator.generate_campaign_diary_txt(self.current_data)
        
        pilot_name = self.current_data.get('pilot', {}).get('name', 'Piloto').replace(' ', '_')
        default_filename = f"Diario_de_Bordo_{pilot_name}.txt"
        file_path, _ = QFileDialog.getSaveFileName(self, 'Salvar Diário de Bordo', default_filename, 'Text Files (*.txt);;All Files (*)')

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(diary_content)
                QMessageBox.information(self, "Sucesso", f"Diário de bordo salvo em: {file_path}")
            except IOError as e:
                QMessageBox.critical(self, "Erro", f"Não foi possível salvar o arquivo do diário: {e}")
                
    def export_mission_pdf(self):
        """Gera e salva o relatório em PDF para a missão selecionada."""
        if self.selected_mission_index == -1:
            QMessageBox.warning(self, "Aviso", "Selecione uma missão na tabela para exportar.")
            return
        
        mission_to_export = self.current_data['missions'][self.selected_mission_index]
        default_filename = f"Missao_{mission_to_export['date'].replace('/', '-')}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(self, 'Salvar Relatório da Missão', default_filename, 'PDF (*.pdf)')
        
        if file_path:
            success = self.report_generator.generate_mission_report_pdf(
                mission_data=mission_to_export,
                all_missions=self.current_data['missions'],
                mission_index=self.selected_mission_index,
                output_path=file_path
            )
            if success:
                QMessageBox.information(self, "Sucesso", f"Relatório da missão salvo em: {file_path}")
            else:
                QMessageBox.critical(self, "Erro", "Não foi possível gerar o PDF da missão.")

    def load_saved_settings(self):
        saved_path = self.settings.value('pwcgfc_path', '')
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
