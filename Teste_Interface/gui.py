import sys
import os
import json
import logging
from datetime import date
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QFileDialog, QLabel, QTabWidget, QTextEdit, QLineEdit, 
    QFormLayout, QScrollArea, QGroupBox, QComboBox,
    QMessageBox, QTableWidget, QTableWidgetItem,
    QProgressBar, QStatusBar, QDateEdit, QHeaderView, QDialog
)
from PyQt5.QtCore import Qt, QSettings, QThread, pyqtSignal, QTimer, QDate
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWebEngineWidgets import QWebEngineView

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('il2_analyzer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class PilotInfo:
    """Classe para armazenar informações do piloto"""
    name: str = ""
    serial: str = ""
    birth_date: str = ""
    birth_place: str = ""
    age: int = 0
    photo_path: str = ""
    squadron: str = ""
    rank: str = ""
    missions_flown: int = 0
    victories: int = 0
    losses: int = 0
    # Campos de aparência e equipamentos
    rank_type: str = ""
    rank_image_path: str = ""
    hat_type: str = ""
    hat_image_path: str = ""
    uniform_type: str = ""
    uniform_image_path: str = ""
    # Campo de arma pessoal
    personal_weapon: str = ""
    weapon_image_path: str = ""

@dataclass
class MissionData:
    """Classe para armazenar dados de missão"""
    date: str
    time: str
    aircraft: str
    mission_type: str
    location: str
    altitude: str
    result: str = ""
    duration: str = ""

@dataclass
class AceData:
    """Classe para armazenar dados de ases"""
    name: str
    squadron: str
    victories: int
    status: str = "Active"

@dataclass
class DecorationData:
    """Classe para armazenar dados de condecorações"""
    name: str
    description: str
    date_awarded: str = ""
    image_path: str = ""

class DataLoader(QThread):
    """Thread para carregamento de dados em background"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, campaign_path: str):
        super().__init__()
        self.campaign_path = campaign_path

    def run(self):
        try:
            data = self.load_campaign_data()
            self.finished.emit(data)
        except Exception as e:
            logger.error(f"Erro ao carregar dados: {e}")
            self.error.emit(str(e))

    def load_campaign_data(self) -> Dict[str, Any]:
        """Carrega dados da campanha"""
        data = {
            'pilot_info': PilotInfo(),
            'missions': [],
            'aces': [],
            'decorations': [],
            'squadron_info': {}
        }
        
        try:
            # Simula carregamento progressivo
            self.progress.emit(20)
            
            # Carrega informações do piloto
            pilot_file = os.path.join(self.campaign_path, 'pilot.json')
            if os.path.exists(pilot_file):
                with open(pilot_file, 'r', encoding='utf-8') as f:
                    pilot_data = json.load(f)
                    data['pilot_info'] = PilotInfo(**pilot_data)
            
            self.progress.emit(40)
            
            # Carrega missões
            missions_file = os.path.join(self.campaign_path, 'missions.json')
            if os.path.exists(missions_file):
                with open(missions_file, 'r', encoding='utf-8') as f:
                    missions_data = json.load(f)
                    data['missions'] = [MissionData(**m) for m in missions_data]
            
            self.progress.emit(60)
            
            # Carrega ases
            aces_file = os.path.join(self.campaign_path, 'aces.json')
            if os.path.exists(aces_file):
                with open(aces_file, 'r', encoding='utf-8') as f:
                    aces_data = json.load(f)
                    data['aces'] = [AceData(**a) for a in aces_data]
            
            self.progress.emit(80)
            
            # Carrega condecorações
            decorations_file = os.path.join(self.campaign_path, 'decorations.json')
            if os.path.exists(decorations_file):
                with open(decorations_file, 'r', encoding='utf-8') as f:
                    decorations_data = json.load(f)
                    data['decorations'] = [DecorationData(**d) for d in decorations_data]
            
            self.progress.emit(100)
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados da campanha: {e}")
            raise
            
        return data

class PathConfigDialog(QDialog):
    """Dialog para configuração do caminho PWCGFC"""
    
    def __init__(self, parent=None, current_path=""):
        super().__init__(parent)
        self.current_path = current_path
        self.selected_path = current_path
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Configuração de Pasta PWCGFC")
        self.setModal(True)
        self.resize(500, 200)
        
        layout = QVBoxLayout()
        
        # Informações
        info_label = QLabel("Selecione a pasta raiz do PWCGFC:")
        layout.addWidget(info_label)
        
        # Caminho atual
        path_group = QGroupBox("Pasta Atual")
        path_layout = QVBoxLayout()
        
        self.path_label = QLabel(self.current_path if self.current_path else "Nenhuma pasta selecionada")
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; border: 1px solid #ccc; }")
        path_layout.addWidget(self.path_label)
        
        path_group.setLayout(path_layout)
        layout.addWidget(path_group)
        
        # Botões
        button_layout = QHBoxLayout()
        
        select_button = QPushButton("Selecionar Pasta")
        select_button.clicked.connect(self.select_folder)
        
        clear_button = QPushButton("Limpar")
        clear_button.clicked.connect(self.clear_path)
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(select_button)
        button_layout.addWidget(clear_button)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(
            self, 'Selecionar Pasta PWCGFC', self.selected_path
        )
        if folder_path:
            self.selected_path = folder_path
            self.path_label.setText(folder_path)
    
    def clear_path(self):
        self.selected_path = ""
        self.path_label.setText("Nenhuma pasta selecionada")
    
    def get_selected_path(self):
        return self.selected_path

class IL2CampaignAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings('IL2CampaignAnalyzer', 'Settings')
        self.pwcgfc_path = ""
        self.campaign_data = {}
        self.pilot_data = PilotInfo()
        self.missions_data = []
        self.aces_data = []
        self.decorations_data = []
        self.loading_overlay = QWidget(self)
        self.loading_overlay.setStyleSheet("background-color: rgba(0, 0, 0, 150);")
        self.loading_overlay.setGeometry(0, 0, self.width(), self.height())
        self.loading_overlay.hide()

        # Layout para o overlay
        overlay_layout = QVBoxLayout(self.loading_overlay)
        loading_label = QLabel("Carregando dados...", self.loading_overlay)
        loading_label.setAlignment(Qt.AlignCenter)
        loading_label.setStyleSheet("color: white; font-size: 24px;")
        overlay_layout.addWidget(loading_label)

        loading_spinner = QProgressBar(self.loading_overlay)
        loading_spinner.setRange(0, 0) # Indeterminate progress bar
        loading_spinner.setTextVisible(False)
        overlay_layout.addWidget(loading_spinner)

        self.loading_overlay.setLayout(overlay_layout)

        
        # Opções de patente
        self.rank_options = {
            "Tenente": "assets/ranks/lieutenant.png",
            "Capitão": "assets/ranks/captain.png",
            "Major": "assets/ranks/major.png",
            "Coronel": "assets/ranks/colonel.png",
            "Sargento": "assets/ranks/sergeant.png"
        }
        
        # Opções de chapéu
        self.hat_options = {
            "Nenhum": "",
            "Boné de Voo": "assets/hats/flight_cap.png",
            "Capacete de Couro": "assets/hats/leather_helmet.png",
            "Chapéu de Oficial": "assets/hats/officer_hat.png"
        }
        
        # Opções de uniforme
        self.uniform_options = {
            "Uniforme Padrão": "assets/uniforms/standard.png",
            "Uniforme de Voo": "assets/uniforms/flight_suit.png",
            "Uniforme de Gala": "assets/uniforms/dress_uniform.png",
            "Uniforme de Inverno": "assets/uniforms/winter_uniform.png"
        }
        
        # Opções de armas pessoais
        self.weapon_options = {
            "Nenhuma": "",
            "Colt .45": "assets/weapons/colt_45.png",
            "Luger P08": "assets/weapons/luger_p08.png",
            "Webley Revolver": "assets/weapons/webley_revolver.png",
            "Tokarev TT-33": "assets/weapons/tokarev_tt33.png",
            "Walther P38": "assets/weapons/walther_p38.png"
        }
        
        self.setup_ui()
        self.setup_status_bar()
        self.load_saved_settings()
        if not self.pwcgfc_path:
            QMessageBox.information(self, "Configuração Inicial", 
                                    "Bem-vindo ao IL-2 Campaign Analyzer!\n\n"\
                                    "Para começar, por favor, configure a pasta raiz do PWCGFC.\n"\
                                    "Clique em OK e selecione a pasta no próximo diálogo.")
            self.open_config_dialog()
        self.setup_auto_save()
        
    def setup_ui(self):
        """Inicializa a interface do usuário"""
        self.setWindowTitle('IL-2 Sturmovik Campaign Analyzer v3.0')
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1000, 700)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Seções da interface
        main_layout.addWidget(self.create_config_section())
        main_layout.addWidget(self.create_campaign_selection_section())
        
        # Abas principais
        self.tabs = QTabWidget()
        self.create_tabs()
        main_layout.addWidget(self.tabs)
        
        # Botões de ação
        button_layout = QHBoxLayout()
        
        self.sync_button = QPushButton('Sincronizar Dados')
        self.sync_button.clicked.connect(self.sync_data)
        self.sync_button.setEnabled(False)
        
        self.backup_button = QPushButton('Fazer Backup')
        self.backup_button.clicked.connect(self.create_backup)
        
        self.restore_button = QPushButton('Restaurar Backup')
        self.restore_button.clicked.connect(self.restore_backup)
        
        button_layout.addWidget(self.sync_button)
        button_layout.addWidget(self.backup_button)
        button_layout.addWidget(self.restore_button)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)

    def setup_status_bar(self):
        """Configura a barra de status"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('Pronto')

    def create_config_section(self):
        """Cria seção de configuração com botão de engrenagem"""
        group_box = QGroupBox("Configuração")
        layout = QHBoxLayout()
        
        # Botão de engrenagem para configuração
        config_button = QPushButton("⚙️")
        config_button.setFixedSize(40, 40)
        config_button.setToolTip("Configurar pasta PWCGFC")
        config_button.clicked.connect(self.open_config_dialog)
        
        # Label de status da configuração
        self.config_status_label = QLabel("Clique na engrenagem para configurar")
        self.config_status_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        
        layout.addWidget(config_button)
        layout.addWidget(self.config_status_label)
        layout.addStretch()
        
        group_box.setLayout(layout)
        return group_box

    def create_campaign_selection_section(self):
        """Cria seção de seleção de campanha"""
        group_box = QGroupBox("Seleção de Campanha")
        layout = QHBoxLayout()
        
        self.campaign_combo = QComboBox()
        self.campaign_combo.currentTextChanged.connect(self.on_campaign_selected)
        self.campaign_combo.setMinimumWidth(200)
        
        refresh_button = QPushButton('Atualizar')
        refresh_button.clicked.connect(self.load_campaigns)
        
        layout.addWidget(QLabel("Campanha:"))
        layout.addWidget(self.campaign_combo)
        layout.addWidget(refresh_button)
        layout.addStretch()
        
        group_box.setLayout(layout)
        return group_box

    def create_tabs(self):
        """Cria as abas principais"""
        self.create_pilot_profile_tab()
        self.create_decorations_tab()
        self.create_career_map_tab()  # Nova aba
        self.create_squad_tab()
        self.create_aces_tab()
        self.create_missions_tab()
        self.create_statistics_tab()

    def create_career_map_tab(self):
        """Cria aba do mapa da carreira"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Cabeçalho
        header_label = QLabel("Mapa da Carreira")
        header_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)
        
        # Área principal do mapa da carreira
        career_group = QGroupBox("Progressão da Carreira")
        career_layout = QVBoxLayout()
        
        # Placeholder para o mapa da carreira
        self.career_map_text = QTextEdit()
        self.career_map_text.setReadOnly(True)
        self.career_map_text.setPlainText(
            "MAPA DA CARREIRA\n\n"
            "Esta seção mostrará a progressão da carreira do piloto, incluindo:\n\n"
            "• Promoções e mudanças de patente\n"
            "• Transferências entre esquadrões\n"
            "• Marcos importantes da carreira\n"
            "• Condecorações recebidas\n"
            "• Estatísticas de combate ao longo do tempo\n\n"
            "Funcionalidade será implementada em versão futura."
        )
        self.career_map_text.setMinimumHeight(400)
        
        career_layout.addWidget(self.career_map_text)
        career_group.setLayout(career_layout)
        layout.addWidget(career_group)
        
        # Botões de ação
        button_layout = QHBoxLayout()
        
        export_career_button = QPushButton("Exportar Mapa da Carreira")
        export_career_button.clicked.connect(self.export_career_map)
        
        button_layout.addWidget(export_career_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        widget.setLayout(layout)
        self.tabs.addTab(widget, 'Mapa da Carreira')

    def create_decorations_tab(self):
        """Cria aba de condecorações"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Cabeçalho
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Condecorações do Piloto"))
        header_layout.addStretch()
        
        add_decoration_button = QPushButton("Adicionar Condecoração")
        add_decoration_button.clicked.connect(self.add_decoration)
        
        remove_decoration_button = QPushButton("Remover Condecoração")
        remove_decoration_button.clicked.connect(self.remove_decoration)
        
        header_layout.addWidget(add_decoration_button)
        header_layout.addWidget(remove_decoration_button)
        
        layout.addLayout(header_layout)
        
        # Tabela de condecorações
        self.decorations_table = QTableWidget()
        self.decorations_table.setColumnCount(4)
        self.decorations_table.setHorizontalHeaderLabels(["Nome", "Descrição", "Data", "Imagem"])
        
        # Configura redimensionamento automático
        header = self.decorations_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.decorations_table.setAlternatingRowColors(True)
        self.decorations_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.decorations_table)
        
        widget.setLayout(layout)
        self.tabs.addTab(widget, 'Condecorações')

    def create_pilot_profile_tab(self):
        """Cria aba de perfil do piloto"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Scroll area
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Informações básicas
        basic_group = QGroupBox("Informações Básicas")
        basic_layout = QFormLayout()
        
        self.pilot_name_label = QLabel("N/A")
        self.pilot_serial_label = QLabel("N/A")
        self.campaign_date_label = QLabel("N/A")
        self.squadron_label = QLabel("N/A")
        self.rank_label = QLabel("N/A")
        
        basic_layout.addRow("Nome do Piloto:", self.pilot_name_label)
        basic_layout.addRow("Número Serial:", self.pilot_serial_label)
        basic_layout.addRow("Esquadrão:", self.squadron_label)
        basic_layout.addRow("Patente:", self.rank_label)
        basic_layout.addRow("Data da Campanha:", self.campaign_date_label)
        
        basic_group.setLayout(basic_layout)
        scroll_layout.addWidget(basic_group)
        
        # Informações complementares
        complement_group = QGroupBox("Informações Complementares")
        complement_layout = QFormLayout()
        
        self.birth_date_edit = QDateEdit()
        self.birth_date_edit.setCalendarPopup(True)
        self.birth_date_edit.setDate(QDate.currentDate())
        QTimer.singleShot(0, lambda: self.birth_date_edit.dateChanged.connect(self.calculate_age))
        
        self.birth_place_edit = QLineEdit()
        self.age_label = QLabel("N/A")
        
        complement_layout.addRow("Data de Nascimento:", self.birth_date_edit)
        complement_layout.addRow("Local de Nascimento:", self.birth_place_edit)
        complement_layout.addRow("Idade:", self.age_label)
        
        # Seção de foto
        photo_layout = QHBoxLayout()
        photo_button = QPushButton("Anexar Foto")
        photo_button.clicked.connect(self.attach_photo)
        
        remove_photo_button = QPushButton("Remover Foto")
        remove_photo_button.clicked.connect(self.remove_photo)
        
        photo_layout.addWidget(photo_button)
        photo_layout.addWidget(remove_photo_button)
        
        complement_layout.addRow("Foto:", photo_layout)
        
        self.photo_label = QLabel("Nenhuma foto anexada")
        self.photo_label.setMinimumSize(200, 200)
        self.photo_label.setMaximumSize(250, 250)
        self.photo_label.setStyleSheet("border: 2px solid gray; background-color: white;")
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setScaledContents(True)
        
        complement_layout.addRow("", self.photo_label)
        complement_group.setLayout(complement_layout)
        scroll_layout.addWidget(complement_group)
        
        # Seção: Aparência e Equipamentos
        appearance_group = QGroupBox("Aparência e Equipamentos")
        appearance_layout = QFormLayout()
        
        # Campo para seleção de patente
        self.rank_combo = QComboBox()
        self.rank_combo.addItems(list(self.rank_options.keys()))
        self.rank_combo.currentTextChanged.connect(self.on_rank_changed)
        
        appearance_layout.addRow("Patente:", self.rank_combo)
        
        self.rank_image_label = QLabel("Nenhuma patente selecionada")
        self.rank_image_label.setMinimumSize(100, 100)
        self.rank_image_label.setMaximumSize(150, 150)
        self.rank_image_label.setStyleSheet("border: 2px solid gray; background-color: white;")
        self.rank_image_label.setAlignment(Qt.AlignCenter)
        self.rank_image_label.setScaledContents(True)
        
        appearance_layout.addRow("", self.rank_image_label)
        
        # Campo para seleção de chapéu
        self.hat_combo = QComboBox()
        self.hat_combo.addItems(list(self.hat_options.keys()))
        self.hat_combo.currentTextChanged.connect(self.on_hat_changed)
        
        appearance_layout.addRow("Chapéu:", self.hat_combo)
        
        self.hat_image_label = QLabel("Nenhum chapéu selecionado")
        self.hat_image_label.setMinimumSize(100, 100)
        self.hat_image_label.setMaximumSize(150, 150)
        self.hat_image_label.setStyleSheet("border: 2px solid gray; background-color: white;")
        self.hat_image_label.setAlignment(Qt.AlignCenter)
        self.hat_image_label.setScaledContents(True)
        
        appearance_layout.addRow("", self.hat_image_label)
        
        # Campo para seleção de uniforme
        self.uniform_combo = QComboBox()
        self.uniform_combo.addItems(list(self.uniform_options.keys()))
        self.uniform_combo.currentTextChanged.connect(self.on_uniform_changed)
        
        appearance_layout.addRow("Uniforme:", self.uniform_combo)
        
        self.uniform_image_label = QLabel("Nenhum uniforme selecionado")
        self.uniform_image_label.setMinimumSize(100, 100)
        self.uniform_image_label.setMaximumSize(150, 150)
        self.uniform_image_label.setStyleSheet("border: 2px solid gray; background-color: white;")
        self.uniform_image_label.setAlignment(Qt.AlignCenter)
        self.uniform_image_label.setScaledContents(True)
        
        appearance_layout.addRow("", self.uniform_image_label)
        
        # Campo para seleção de arma pessoal
        self.weapon_combo = QComboBox()
        self.weapon_combo.addItems(list(self.weapon_options.keys()))
        self.weapon_combo.currentTextChanged.connect(self.on_weapon_changed)
        
        appearance_layout.addRow("Arma Pessoal:", self.weapon_combo)
        
        self.weapon_image_label = QLabel("Nenhuma arma selecionada")
        self.weapon_image_label.setMinimumSize(100, 100)
        self.weapon_image_label.setMaximumSize(150, 150)
        self.weapon_image_label.setStyleSheet("border: 2px solid gray; background-color: white;")
        self.weapon_image_label.setAlignment(Qt.AlignCenter)
        self.weapon_image_label.setScaledContents(True)
        
        appearance_layout.addRow("", self.weapon_image_label)
        
        # Seção de armas disponíveis
        weapons_info_label = QLabel("Armas Disponíveis:")
        weapons_info_label.setFont(QFont("Arial", 10, QFont.Bold))
        appearance_layout.addRow("", weapons_info_label)
        
        weapons_list_label = QLabel("• Colt .45 - Pistola americana padrão\n• Luger P08 - Pistola alemã\n• Webley Revolver - Revólver britânico\n• Tokarev TT-33 - Pistola soviética\n• Walther P38 - Pistola alemã moderna")
        weapons_list_label.setWordWrap(True)
        weapons_list_label.setStyleSheet("QLabel { color: #666; font-size: 9pt; }")
        appearance_layout.addRow("", weapons_list_label)
        
        appearance_group.setLayout(appearance_layout)
        scroll_layout.addWidget(appearance_group)
        
        # Estatísticas do piloto
        stats_group = QGroupBox("Estatísticas")
        stats_layout = QFormLayout()
        
        self.missions_flown_label = QLabel("0")
        self.victories_label = QLabel("0")
        self.losses_label = QLabel("0")
        
        stats_layout.addRow("Missões Voadas:", self.missions_flown_label)
        stats_layout.addRow("Vitórias:", self.victories_label)
        stats_layout.addRow("Perdas:", self.losses_label)
        
        stats_group.setLayout(stats_layout)
        scroll_layout.addWidget(stats_group)
        
        # Botões de ação
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("Salvar Informações")
        save_button.clicked.connect(self.save_pilot_info)
        
        export_button = QPushButton("Exportar para PDF")
        export_button.clicked.connect(self.export_to_pdf)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(export_button)
        button_layout.addStretch()
        
        scroll_layout.addLayout(button_layout)
        
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        
        layout.addWidget(scroll)
        widget.setLayout(layout)
        
        self.tabs.addTab(widget, 'Perfil do Piloto')

    def create_squad_tab(self):
        """Cria aba do esquadrão"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Informações do esquadrão
        info_group = QGroupBox("Informações do Esquadrão")
        info_layout = QFormLayout()
        
        self.squad_name_label = QLabel("N/A")
        self.squad_base_label = QLabel("N/A")
        self.squad_aircraft_label = QLabel("N/A")
        self.squad_commander_label = QLabel("N/A")
        
        info_layout.addRow("Nome:", self.squad_name_label)
        info_layout.addRow("Base:", self.squad_base_label)
        info_layout.addRow("Aeronave Principal:", self.squad_aircraft_label)
        info_layout.addRow("Comandante:", self.squad_commander_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Texto detalhado
        details_group = QGroupBox("Detalhes")
        details_layout = QVBoxLayout()
        
        self.squad_text = QTextEdit()
        self.squad_text.setReadOnly(True)
        self.squad_text.setPlainText("Carregue uma campanha para ver as informações do esquadrão.")
        
        details_layout.addWidget(self.squad_text)
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        widget.setLayout(layout)
        self.tabs.addTab(widget, 'Squad')

    def create_aces_tab(self):
        """Cria aba dos ases"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Filtros
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filtrar por esquadrão:"))
        
        self.aces_filter_combo = QComboBox()
        self.aces_filter_combo.addItem("Todos")
        self.aces_filter_combo.currentTextChanged.connect(self.filter_aces)
        filter_layout.addWidget(self.aces_filter_combo)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Tabela de ases
        self.aces_table = QTableWidget()
        self.aces_table.setColumnCount(4)
        self.aces_table.setHorizontalHeaderLabels(["Nome", "Esquadrão", "Abates", "Status"])
        
        # Configura redimensionamento automático
        header = self.aces_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.aces_table.setAlternatingRowColors(True)
        self.aces_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.aces_table.setSortingEnabled(True)

        
        layout.addWidget(self.aces_table)
        
        widget.setLayout(layout)
        self.tabs.addTab(widget, 'Aces')

    def create_missions_tab(self):
        """Cria aba das missões"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Filtros
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filtrar por aeronave:"))
        
        self.missions_filter_combo = QComboBox()
        self.missions_filter_combo.addItem("Todas")
        self.missions_filter_combo.currentTextChanged.connect(self.filter_missions)
        filter_layout.addWidget(self.missions_filter_combo)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Tabela de missões
        self.missions_table = QTableWidget()
        self.missions_table.setColumnCount(8)
        self.missions_table.setHorizontalHeaderLabels([
            "Data", "Hora", "Aeronave", "Tipo", "Local", "Altitude", "Duração", "Resultado"
        ])
        
        # Configura redimensionamento
        header = self.missions_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        
        self.missions_table.setAlternatingRowColors(True)
        self.missions_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.missions_table.setSortingEnabled(True)

        
        layout.addWidget(self.missions_table)
        
        widget.setLayout(layout)
        self.tabs.addTab(widget, 'Missions')

    def create_statistics_tab(self):
        """Cria aba de estatísticas"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Estatísticas gerais
        stats_group = QGroupBox("Estatísticas Gerais")
        stats_layout = QFormLayout()
        
        self.total_missions_label = QLabel("0")
        self.favorite_aircraft_label = QLabel("N/A")
        self.success_rate_label = QLabel("0%")
        
        stats_layout.addRow("Total de Missões:", self.total_missions_label)
        stats_layout.addRow("Aeronave Favorita:", self.favorite_aircraft_label)
        stats_layout.addRow("Taxa de Sucesso:", self.success_rate_label)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Gráficos (placeholder)
        charts_group = QGroupBox("Gráficos")
        charts_layout = QVBoxLayout()
        
        self.charts_text = QTextEdit()
        self.charts_text.setReadOnly(True)
        self.charts_text.setPlainText("Área reservada para gráficos de estatísticas.")
        self.charts_text.setMaximumHeight(200)
        
        charts_layout.addWidget(self.charts_text)
        charts_group.setLayout(charts_layout)
        layout.addWidget(charts_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        self.tabs.addTab(widget, 'Statistics')

    # Novos métodos para funcionalidades adicionadas

    def open_config_dialog(self):
        """Abre dialog de configuração de pasta"""
        dialog = PathConfigDialog(self, self.pwcgfc_path)
        if dialog.exec_() == QDialog.Accepted:
            new_path = dialog.get_selected_path()
            if new_path != self.pwcgfc_path:
                self.pwcgfc_path = new_path
                if self.pwcgfc_path:
                    self.config_status_label.setText("Pasta configurada")
                    self.config_status_label.setStyleSheet("QLabel { color: #0a7d0a; }")
                    self.load_campaigns()
                    self.sync_button.setEnabled(True)
                    self.status_bar.showMessage(f'Pasta configurada: {self.pwcgfc_path}')
                    logger.info(f"Pasta PWCGFC configurada: {self.pwcgfc_path}")
                else:
                    self.config_status_label.setText("Nenhuma pasta configurada")
                    self.config_status_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
                    self.campaign_combo.clear()
                    self.sync_button.setEnabled(False)
                    self.clear_all_data()
                
                self.save_settings()

    def on_rank_changed(self, rank_type: str):
        """Quando o tipo de patente é alterado"""
        self.pilot_data.rank_type = rank_type
        image_path = self.rank_options.get(rank_type, "")
        
        if image_path and os.path.exists(image_path):
            try:
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    self.rank_image_label.setPixmap(scaled_pixmap)
                    self.rank_image_label.setText("")
                    self.pilot_data.rank_image_path = image_path
                else:
                    self.rank_image_label.setText("Imagem não encontrada")
                    self.pilot_data.rank_image_path = ""
            except Exception as e:
                logger.error(f"Erro ao carregar imagem da patente: {e}")
                self.rank_image_label.setText("Erro ao carregar imagem")
                self.pilot_data.rank_image_path = ""
        else:
            self.rank_image_label.clear()
            self.rank_image_label.setText("Imagem não encontrada")
            self.pilot_data.rank_image_path = ""

    def on_hat_changed(self, hat_type: str):
        """Quando o tipo de chapéu é alterado"""
        self.pilot_data.hat_type = hat_type
        image_path = self.hat_options.get(hat_type, "")
        
        if image_path and os.path.exists(image_path):
            try:
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    self.hat_image_label.setPixmap(scaled_pixmap)
                    self.hat_image_label.setText("")
                    self.pilot_data.hat_image_path = image_path
                else:
                    self.hat_image_label.setText("Imagem não encontrada")
                    self.pilot_data.hat_image_path = ""
            except Exception as e:
                logger.error(f"Erro ao carregar imagem do chapéu: {e}")
                self.hat_image_label.setText("Erro ao carregar imagem")
                self.pilot_data.hat_image_path = ""
        else:
            self.hat_image_label.clear()
            self.hat_image_label.setText("Nenhum chapéu selecionado" if hat_type == "Nenhum" else "Imagem não encontrada")
            self.pilot_data.hat_image_path = ""

    def on_uniform_changed(self, uniform_type: str):
        """Quando o tipo de uniforme é alterado"""
        self.pilot_data.uniform_type = uniform_type
        image_path = self.uniform_options.get(uniform_type, "")
        
        if image_path and os.path.exists(image_path):
            try:
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    self.uniform_image_label.setPixmap(scaled_pixmap)
                    self.uniform_image_label.setText("")
                    self.pilot_data.uniform_image_path = image_path
                else:
                    self.uniform_image_label.setText("Imagem não encontrada")
                    self.pilot_data.uniform_image_path = ""
            except Exception as e:
                logger.error(f"Erro ao carregar imagem do uniforme: {e}")
                self.uniform_image_label.setText("Erro ao carregar imagem")
                self.pilot_data.uniform_image_path = ""
        else:
            self.uniform_image_label.clear()
            self.uniform_image_label.setText("Imagem não encontrada")
            self.pilot_data.uniform_image_path = ""

    def on_weapon_changed(self, weapon_type: str):
        """Quando o tipo de arma é alterado"""
        self.pilot_data.personal_weapon = weapon_type
        image_path = self.weapon_options.get(weapon_type, "")
        
        if image_path and os.path.exists(image_path):
            try:
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    self.weapon_image_label.setPixmap(scaled_pixmap)
                    self.weapon_image_label.setText("")
                    self.pilot_data.weapon_image_path = image_path
                else:
                    self.weapon_image_label.setText("Imagem não encontrada")
                    self.pilot_data.weapon_image_path = ""
            except Exception as e:
                logger.error(f"Erro ao carregar imagem da arma: {e}")
                self.weapon_image_label.setText("Erro ao carregar imagem")
                self.pilot_data.weapon_image_path = ""
        else:
            self.weapon_image_label.clear()
            self.weapon_image_label.setText("Nenhuma arma selecionada" if weapon_type == "Nenhuma" else "Imagem não encontrada")
            self.pilot_data.weapon_image_path = ""

    def add_decoration(self):
        """Adiciona uma nova condecoração"""
        from PyQt5.QtWidgets import QDialog, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Adicionar Condecoração")
        dialog.setModal(True)
        
        layout = QFormLayout()
        
        name_edit = QLineEdit()
        description_edit = QTextEdit()
        description_edit.setMaximumHeight(100)
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDate(QDate.currentDate())
        
        layout.addRow("Nome:", name_edit)
        layout.addRow("Descrição:", description_edit)
        layout.addRow("Data:", date_edit)
        
        # Botões
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        layout.addRow(buttons)
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            decoration = DecorationData(
                name=name_edit.text(),
                description=description_edit.toPlainText(),
                date_awarded=date_edit.date().toString("yyyy-MM-dd")
            )
            self.decorations_data.append(decoration)
            self.populate_decorations_table()
            self.status_bar.showMessage('Condecoração adicionada')

    def remove_decoration(self):
        """Remove condecoração selecionada"""
        current_row = self.decorations_table.currentRow()
        if current_row >= 0:
            del self.decorations_data[current_row]
            self.populate_decorations_table()
            self.status_bar.showMessage('Condecoração removida')
        else:
            QMessageBox.warning(self, "Aviso", "Selecione uma condecoração para remover.")

    def populate_decorations_table(self):
        """Popula tabela de condecorações"""
        self.decorations_table.setRowCount(len(self.decorations_data))
        
        for row, decoration in enumerate(self.decorations_data):
            self.decorations_table.setItem(row, 0, QTableWidgetItem(decoration.name))
            self.decorations_table.setItem(row, 1, QTableWidgetItem(decoration.description))
            self.decorations_table.setItem(row, 2, QTableWidgetItem(decoration.date_awarded))
            
            # Para a imagem, mostra apenas se existe ou não
            image_status = "Sim" if decoration.image_path and os.path.exists(decoration.image_path) else "Não"
            self.decorations_table.setItem(row, 3, QTableWidgetItem(image_status))

    def export_career_map(self):
        """Exporta mapa da carreira"""
        QMessageBox.information(self, "Info", "Funcionalidade de exportação do mapa da carreira será implementada em versão futura.")

    # Métodos existentes (continuação do código original)

    def load_campaigns(self):
        """Carrega lista de campanhas"""
        if not self.pwcgfc_path:
            return
        
        campaigns_path = Path(self.pwcgfc_path) / 'User' / 'Campaigns'
        if not campaigns_path.exists():
            QMessageBox.warning(self, "Aviso", "Pasta de campanhas não encontrada!")
            return
        
        self.campaign_combo.clear()
        try:
            for item in campaigns_path.iterdir():
                if item.is_dir():
                    self.campaign_combo.addItem(item.name)
            
            if self.campaign_combo.count() > 0:
                self.status_bar.showMessage(f'{self.campaign_combo.count()} campanhas encontradas')
            else:
                self.status_bar.showMessage('Nenhuma campanha encontrada')
                
        except Exception as e:
            logger.error(f"Erro ao carregar campanhas: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao carregar campanhas: {e}")

    def on_campaign_selected(self, campaign_name: str):
        """Quando uma campanha é selecionada"""
        if not campaign_name:
            return
        
        self.status_bar.showMessage(f'Campanha selecionada: {campaign_name}')
        self.load_campaign_data_async(campaign_name)

    def load_campaign_data_async(self, campaign_name: str):
        """Carrega dados da campanha em background"""
        campaign_path = Path(self.pwcgfc_path) / 'User' / 'Campaigns' / campaign_name
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        

        self.loading_overlay.show()
        self.setDisabled(True) # Desabilita a interface principal

        self.data_loader = DataLoader(str(campaign_path))
        self.data_loader.progress.connect(self.progress_bar.setValue)
        self.data_loader.finished.connect(self.on_data_loaded)
        self.data_loader.error.connect(self.on_data_load_error)
        self.data_loader.start()

    def on_data_loaded(self, data: Dict[str, Any]):
        """Callback quando dados são carregados"""
        self.campaign_data = data
        self.pilot_data = data['pilot_info']
        self.missions_data = data['missions']
        self.aces_data = data['aces']
        self.decorations_data = data['decorations']
        
        self.update_ui_with_data()
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Dados carregados com sucesso")
        self.loading_overlay.hide()
        self.setEnabled(True) # Reabilita a interface principal

    def on_data_load_error(self, error_message: str):
        """Callback quando há erro no carregamento"""
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Erro ao carregar dados")
        self.loading_overlay.hide()
        self.setEnabled(True) # Reabilita a interface principal
        QMessageBox.critical(self, "Erro", f"Erro ao carregar dados: {error_message}")

    def update_ui_with_data(self):
        """Atualiza interface com os dados carregados"""
        # Atualiza aba do piloto
        self.pilot_name_label.setText(self.pilot_data.name or "N/A")
        self.pilot_serial_label.setText(self.pilot_data.serial or "N/A")
        self.squadron_label.setText(self.pilot_data.squadron or "N/A")
        self.rank_label.setText(self.pilot_data.rank or "N/A")
        
        if self.pilot_data.birth_place:
            self.birth_place_edit.setText(self.pilot_data.birth_place)
        
        if self.pilot_data.photo_path and os.path.exists(self.pilot_data.photo_path):
            self.load_pilot_photo(self.pilot_data.photo_path)
        
        # Atualiza novos campos
        if self.pilot_data.rank_type:
            index = self.rank_combo.findText(self.pilot_data.rank_type)
            if index >= 0:
                self.rank_combo.setCurrentIndex(index)
        
        if self.pilot_data.hat_type:
            index = self.hat_combo.findText(self.pilot_data.hat_type)
            if index >= 0:
                self.hat_combo.setCurrentIndex(index)
        
        if self.pilot_data.uniform_type:
            index = self.uniform_combo.findText(self.pilot_data.uniform_type)
            if index >= 0:
                self.uniform_combo.setCurrentIndex(index)
        
        if self.pilot_data.personal_weapon:
            index = self.weapon_combo.findText(self.pilot_data.personal_weapon)
            if index >= 0:
                self.weapon_combo.setCurrentIndex(index)
        
        # Atualiza estatísticas
        self.missions_flown_label.setText(str(self.pilot_data.missions_flown))
        self.victories_label.setText(str(self.pilot_data.victories))
        self.losses_label.setText(str(self.pilot_data.losses))
        
        # Atualiza tabelas
        self.populate_missions_table()
        self.populate_aces_table()
        self.populate_decorations_table()
        self.update_statistics()

    def populate_missions_table(self):
        """Popula tabela de missões"""
        self.missions_table.setRowCount(len(self.missions_data))
        
        # Atualiza filtro de aeronaves
        aircraft_set = set()
        for mission in self.missions_data:
            aircraft_set.add(mission.aircraft)
        
        self.missions_filter_combo.clear()
        self.missions_filter_combo.addItem("Todas")
        for aircraft in sorted(aircraft_set):
            self.missions_filter_combo.addItem(aircraft)
        
        # Popula tabela
        for row, mission in enumerate(self.missions_data):
            self.missions_table.setItem(row, 0, QTableWidgetItem(mission.date))
            self.missions_table.setItem(row, 1, QTableWidgetItem(mission.time))
            self.missions_table.setItem(row, 2, QTableWidgetItem(mission.aircraft))
            self.missions_table.setItem(row, 3, QTableWidgetItem(mission.mission_type))
            self.missions_table.setItem(row, 4, QTableWidgetItem(mission.location))
            self.missions_table.setItem(row, 5, QTableWidgetItem(mission.altitude))
            self.missions_table.setItem(row, 6, QTableWidgetItem(mission.duration))
            self.missions_table.setItem(row, 7, QTableWidgetItem(mission.result))

    def populate_aces_table(self):
        """Popula tabela de ases"""
        self.aces_table.setRowCount(len(self.aces_data))
        
        # Atualiza filtro de esquadrões
        squadrons_set = set()
        for ace in self.aces_data:
            squadrons_set.add(ace.squadron)
        
        self.aces_filter_combo.clear()
        self.aces_filter_combo.addItem("Todos")
        for squadron in sorted(squadrons_set):
            self.aces_filter_combo.addItem(squadron)
        
        # Popula tabela
        for row, ace in enumerate(self.aces_data):
            self.aces_table.setItem(row, 0, QTableWidgetItem(ace.name))
            self.aces_table.setItem(row, 1, QTableWidgetItem(ace.squadron))
            self.aces_table.setItem(row, 2, QTableWidgetItem(str(ace.victories)))
            self.aces_table.setItem(row, 3, QTableWidgetItem(ace.status))

    def update_statistics(self):
        """Atualiza estatísticas gerais"""
        total_missions = len(self.missions_data)
        self.total_missions_label.setText(str(total_missions))
        
        # Calcula aeronave favorita
        if self.missions_data:
            aircraft_count = {}
            for mission in self.missions_data:
                aircraft_count[mission.aircraft] = aircraft_count.get(mission.aircraft, 0) + 1
            
            favorite_aircraft = max(aircraft_count, key=aircraft_count.get)
            self.favorite_aircraft_label.setText(favorite_aircraft)
        
        # Calcula taxa de sucesso (simulada)
        success_count = sum(1 for mission in self.missions_data if mission.result == "Success")
        if total_missions > 0:
            success_rate = (success_count / total_missions) * 100
            self.success_rate_label.setText(f"{success_rate:.1f}%")

    def filter_missions(self, aircraft: str):
        """Filtra missões por aeronave"""
        if aircraft == "Todas":
            for row in range(self.missions_table.rowCount()):
                self.missions_table.setRowHidden(row, False)
        else:
            for row in range(self.missions_table.rowCount()):
                item = self.missions_table.item(row, 2)  # Coluna da aeronave
                if item:
                    self.missions_table.setRowHidden(row, item.text() != aircraft)

    def filter_aces(self, squadron: str):
        """Filtra ases por esquadrão"""
        if squadron == "Todos":
            for row in range(self.aces_table.rowCount()):
                self.aces_table.setRowHidden(row, False)
        else:
            for row in range(self.aces_table.rowCount()):
                item = self.aces_table.item(row, 1)  # Coluna do esquadrão
                if item:
                    self.aces_table.setRowHidden(row, item.text() != squadron)

    def calculate_age(self):
        """Calcula idade baseada na data de nascimento"""
        try:
            birth_date = self.birth_date_edit.date().toPyDate()
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            self.age_label.setText(str(age))
            self.pilot_data.age = age
        except Exception as e:
            logger.error(f"Erro ao calcular idade: {e}")
            self.age_label.setText("N/A")

    def attach_photo(self):
        """Anexa foto do piloto"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Selecionar Foto', '', 
            'Imagens (*.png *.jpg *.jpeg *.bmp *.gif);;Todos os arquivos (*)'
        )
        if file_path:
            try:
                self.load_pilot_photo(file_path)
                self.pilot_data.photo_path = file_path
                self.status_bar.showMessage('Foto anexada com sucesso')
                logger.info(f"Foto anexada: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao carregar foto: {e}")
                logger.error(f"Erro ao carregar foto: {e}")

    def load_pilot_photo(self, file_path: str):
        """Carrega e exibe foto do piloto"""
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.photo_label.setPixmap(scaled_pixmap)
            self.photo_label.setText("")
        else:
            raise ValueError("Arquivo de imagem inválido")

    def remove_photo(self):
        """Remove foto do piloto"""
        self.photo_label.clear()
        self.photo_label.setText("Nenhuma foto anexada")
        self.pilot_data.photo_path = ""
        self.status_bar.showMessage('Foto removida')

    def save_pilot_info(self):
        """Salva informações complementares do piloto"""
        try:
            # Atualiza dados do piloto
            self.pilot_data.birth_date = self.birth_date_edit.date().toString("yyyy-MM-dd")
            self.pilot_data.birth_place = self.birth_place_edit.text()
            
            # Salva em arquivo
            if self.pwcgfc_path and self.campaign_combo.currentText():
                campaign_path = Path(self.pwcgfc_path) / 'User' / 'Campaigns' / self.campaign_combo.currentText()
                pilot_file = campaign_path / 'pilot_extra.json'
                decorations_file = campaign_path / 'decorations.json'
                
                # Cria diretório se não existir
                campaign_path.mkdir(parents=True, exist_ok=True)
                
                # Salva dados do piloto
                with open(pilot_file, 'w', encoding='utf-8') as f:
                    json.dump(asdict(self.pilot_data), f, indent=2, ensure_ascii=False)
                
                # Salva condecorações
                decorations_dict = [asdict(decoration) for decoration in self.decorations_data]
                with open(decorations_file, 'w', encoding='utf-8') as f:
                    json.dump(decorations_dict, f, indent=2, ensure_ascii=False)
                
                QMessageBox.information(self, "Sucesso", "Informações salvas com sucesso!")
                self.status_bar.showMessage('Informações do piloto salvas')
                logger.info("Informações do piloto salvas com sucesso")
            else:
                QMessageBox.warning(self, "Aviso", "Selecione uma campanha primeiro!")
                
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar informações: {e}")
            logger.error(f"Erro ao salvar informações do piloto: {e}")

    def export_to_pdf(self):
        """Exporta perfil do piloto para PDF"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, 'Salvar PDF', f'{self.pilot_data.name}_profile.pdf', 
                'PDF files (*.pdf);;Todos os arquivos (*)'
            )
            
            if file_path:
                html_content = self.generate_pilot_report_html()
                
                printer = QPrinter(QPrinter.HighResolution)
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOutputFileName(file_path)
                printer.setPageSize(QPrinter.A4)
                
                # Cria um QWebEngineView temporário para renderizar o HTML
                web_view = QWebEngineView()
                web_view.setHtml(html_content)
                
                def print_finished():
                    QMessageBox.information(self, "Sucesso", "PDF exportado com sucesso!")
                    self.status_bar.showMessage('PDF exportado com sucesso')
                    web_view.deleteLater()
                
                # Aguarda o carregamento e então imprime
                def on_load_finished():
                    web_view.page().print(printer, print_finished)
                
                web_view.loadFinished.connect(on_load_finished)
                
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF: {e}")
            logger.error(f"Erro ao exportar PDF: {e}")

    def generate_pilot_report_html(self) -> str:
        """Gera HTML para relatório do piloto"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Perfil do Piloto - {self.pilot_data.name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; }}
                .section {{ margin: 20px 0; }}
                .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
                .photo {{ text-align: center; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Perfil do Piloto</h1>
                <h2>{self.pilot_data.name}</h2>
            </div>
            
            <div class="section">
                <div class="info-grid">
                    <div>
                        <h3>Informações Básicas</h3>
                        <p><strong>Nome:</strong> {self.pilot_data.name}</p>
                        <p><strong>Número Serial:</strong> {self.pilot_data.serial}</p>
                        <p><strong>Esquadrão:</strong> {self.pilot_data.squadron}</p>
                        <p><strong>Patente:</strong> {self.pilot_data.rank}</p>
                        <p><strong>Data de Nascimento:</strong> {self.pilot_data.birth_date}</p>
                        <p><strong>Local de Nascimento:</strong> {self.pilot_data.birth_place}</p>
                        <p><strong>Idade:</strong> {self.pilot_data.age} anos</p>
                    </div>
                    <div>
                        <h3>Equipamentos</h3>
                        <p><strong>Patente:</strong> {self.pilot_data.rank_type}</p>
                        <p><strong>Chapéu:</strong> {self.pilot_data.hat_type}</p>
                        <p><strong>Uniforme:</strong> {self.pilot_data.uniform_type}</p>
                        <p><strong>Arma Pessoal:</strong> {self.pilot_data.personal_weapon}</p>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h3>Estatísticas de Combate</h3>
                <table>
                    <tr><th>Estatística</th><th>Valor</th></tr>
                    <tr><td>Missões Voadas</td><td>{self.pilot_data.missions_flown}</td></tr>
                    <tr><td>Vitórias</td><td>{self.pilot_data.victories}</td></tr>
                    <tr><td>Perdas</td><td>{self.pilot_data.losses}</td></tr>
                </table>
            </div>
            
            <div class="section">
                <h3>Condecorações</h3>
                <table>
                    <tr><th>Nome</th><th>Descrição</th><th>Data</th></tr>
        """
        
        for decoration in self.decorations_data:
            html += f"""
                    <tr>
                        <td>{decoration.name}</td>
                        <td>{decoration.description}</td>
                        <td>{decoration.date_awarded}</td>
                    </tr>
            """
        
        html += """
                </table>
            </div>
        </body>
        </html>
        """
        
        return html

    def sync_data(self):
        """Sincroniza dados com PWCGFC"""
        # Implementação placeholder
        QMessageBox.information(self, "Info", "Funcionalidade de sincronização será implementada em versão futura.")

    def create_backup(self):
        """Cria backup dos dados"""
        # Implementação placeholder
        QMessageBox.information(self, "Info", "Funcionalidade de backup será implementada em versão futura.")

    def restore_backup(self):
        """Restaura backup dos dados"""
        # Implementação placeholder
        QMessageBox.information(self, "Info", "Funcionalidade de restauração será implementada em versão futura.")

    def clear_all_data(self):
        """Limpa todos os dados da interface"""
        # Reset pilot data
        self.pilot_data = PilotInfo()
        self.missions_data = []
        self.aces_data = []
        self.decorations_data = []
        
        # Clear UI elements
        self.pilot_name_label.setText("N/A")
        self.pilot_serial_label.setText("N/A")
        self.squadron_label.setText("N/A")
        self.rank_label.setText("N/A")
        self.campaign_date_label.setText("N/A")
        
        self.birth_place_edit.clear()
        self.age_label.setText("N/A")
        
        self.photo_label.clear()
        self.photo_label.setText("Nenhuma foto anexada")
        
        self.rank_image_label.clear()
        self.rank_image_label.setText("Nenhuma patente selecionada")
        
        self.hat_image_label.clear()
        self.hat_image_label.setText("Nenhum chapéu selecionado")
        
        self.uniform_image_label.clear()
        self.uniform_image_label.setText("Nenhum uniforme selecionado")
        
        self.weapon_image_label.clear()
        self.weapon_image_label.setText("Nenhuma arma selecionada")
        
        self.missions_flown_label.setText("0")
        self.victories_label.setText("0")
        self.losses_label.setText("0")
        
        # Clear tables
        self.missions_table.setRowCount(0)
        self.aces_table.setRowCount(0)
        self.decorations_table.setRowCount(0)
        
        # Clear text areas
        self.squad_text.clear()
        self.career_map_text.clear()

    def setup_auto_save(self):
        """Configura salvamento automático"""
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start(300000)  # Auto-save a cada 5 minutos

    def auto_save(self):
        """Salvamento automático"""
        if self.pilot_data.name and self.pwcgfc_path and self.campaign_combo.currentText():
            try:
                self.save_pilot_info()
                logger.info("Auto-save executado com sucesso")
            except Exception as e:
                logger.error(f"Erro no auto-save: {e}")

    def save_settings(self):
        """Salva configurações da aplicação"""
        self.settings.setValue('pwcgfc_path', self.pwcgfc_path)
        self.settings.setValue('window_geometry', self.saveGeometry())
        self.settings.setValue('window_state', self.saveState())

    def load_saved_settings(self):
        """Carrega configurações salvas"""
        saved_path = self.settings.value('pwcgfc_path', '')
        if saved_path and os.path.exists(saved_path):
            self.pwcgfc_path = saved_path
            self.config_status_label.setText("Pasta configurada")
            self.config_status_label.setStyleSheet("QLabel { color: #0a7d0a; }")
            self.load_campaigns()
            self.sync_button.setEnabled(True)
        
        # Restaura geometria da janela
        geometry = self.settings.value('window_geometry')
        if geometry:
            self.restoreGeometry(geometry)
        
        state = self.settings.value('window_state')
        if state:
            self.restoreState(state)

    def closeEvent(self, event):
        """Evento de fechamento da aplicação"""
        self.save_settings()
        
        # Para o timer de auto-save
        if hasattr(self, 'auto_save_timer'):
            self.auto_save_timer.stop()
        
        # Para thread de carregamento se estiver rodando
        if hasattr(self, 'data_loader') and self.data_loader.isRunning():
            self.data_loader.terminate()
            self.data_loader.wait()
        
        event.accept()
        logger.info("Aplicação fechada")

def main():
    """Função principal"""
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("IL-2 Campaign Analyzer")
        app.setApplicationVersion("3.0")
        app.setOrganizationName("IL2CampaignAnalyzer")
        
        # Define estilo da aplicação
        app.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
            }
            QTableWidget::item:selected {
                background-color: #3daee9;
                color: white;
            }
        """)
        
        ex = IL2CampaignAnalyzer()
        ex.show()
        
        logger.info("Aplicação iniciada")
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.critical(f"Erro fatal na aplicação: {e}")
        QMessageBox.critical(None, "Erro Fatal", f"Erro fatal na aplicação: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()




class LoadingOverlay(QWidget):
    """Widget de overlay para feedback de carregamento"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setLayout(QVBoxLayout())
        
        self.label = QLabel("Carregando dados...", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 180);
                color: white;
                font-size: 24px;
                padding: 40px;
                border-radius: 15px;
            }
        """)
        self.layout().addWidget(self.label)

    def showEvent(self, event):
        if self.parent():
            self.setGeometry(self.parent().rect())
        super().showEvent(event)


