import sys
import os
import json
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QFileDialog, QLabel, QTabWidget, QTextEdit, QLineEdit, 
    QFormLayout, QScrollArea, QGroupBox, QGridLayout, QComboBox,
    QMessageBox, QTableWidget, QTableWidgetItem, QSplitter, QFrame,
    QProgressBar, QStatusBar, QSpinBox, QDateEdit, QHeaderView
)
from PyQt5.QtCore import Qt, QSettings, QThread, pyqtSignal, QTimer, QDate
from PyQt5.QtGui import QPixmap, QFont, QIcon
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
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
            'squadron_info': {}
        }
        
        try:
            # Simula carregamento progressivo
            self.progress.emit(25)
            
            # Carrega informações do piloto
            pilot_file = os.path.join(self.campaign_path, 'pilot.json')
            if os.path.exists(pilot_file):
                with open(pilot_file, 'r', encoding='utf-8') as f:
                    pilot_data = json.load(f)
                    data['pilot_info'] = PilotInfo(**pilot_data)
            
            self.progress.emit(50)
            
            # Carrega missões
            missions_file = os.path.join(self.campaign_path, 'missions.json')
            if os.path.exists(missions_file):
                with open(missions_file, 'r', encoding='utf-8') as f:
                    missions_data = json.load(f)
                    data['missions'] = [MissionData(**m) for m in missions_data]
            
            self.progress.emit(75)
            
            # Carrega ases
            aces_file = os.path.join(self.campaign_path, 'aces.json')
            if os.path.exists(aces_file):
                with open(aces_file, 'r', encoding='utf-8') as f:
                    aces_data = json.load(f)
                    data['aces'] = [AceData(**a) for a in aces_data]
            
            self.progress.emit(100)
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados da campanha: {e}")
            raise
            
        return data

class IL2CampaignAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings('IL2CampaignAnalyzer', 'Settings')
        self.pwcgfc_path = ""
        self.campaign_data = {}
        self.pilot_data = PilotInfo()
        self.missions_data = []
        self.aces_data = []
        
        self.setup_ui()
        self.setup_status_bar()
        self.load_saved_settings()
        self.setup_auto_save()
        
    def setup_ui(self):
        """Inicializa a interface do usuário"""
        self.setWindowTitle('IL-2 Sturmovik Campaign Analyzer v2.0')
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1000, 700)
        
        # Ícone da aplicação (opcional)
        # self.setWindowIcon(QIcon('icon.png'))
        
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
        main_layout.addWidget(self.create_path_selection_section())
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

    def create_path_selection_section(self):
        """Cria seção de seleção de pasta"""
        group_box = QGroupBox("Configuração de Pasta")
        layout = QVBoxLayout()
        
        self.path_label = QLabel('Nenhum caminho selecionado')
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 5px; }")
        layout.addWidget(self.path_label)
        
        button_layout = QHBoxLayout()
        select_button = QPushButton('Selecionar Pasta PWCGFC')
        select_button.clicked.connect(self.select_pwcgfc_folder)
        
        clear_button = QPushButton('Limpar')
        clear_button.clicked.connect(self.clear_path)
        
        button_layout.addWidget(select_button)
        button_layout.addWidget(clear_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
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
        self.create_squad_tab()
        self.create_aces_tab()
        self.create_missions_tab()
        self.create_statistics_tab()

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
        # Conectar o sinal após definir todos os métodos
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
        
        self.tabs.addTab(widget, 'Pilot Profile')

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
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        
        self.missions_table.setAlternatingRowColors(True)
        self.missions_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.missions_table)
        
        widget.setLayout(layout)
        self.tabs.addTab(widget, 'Missions')

    def create_statistics_tab(self):
        """Cria aba de estatísticas"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Estatísticas gerais
        stats_group = QGroupBox("Estatísticas Gerais")
        stats_layout = QGridLayout()
        
        self.total_missions_label = QLabel("0")
        self.total_flight_time_label = QLabel("0h 0m")
        self.favorite_aircraft_label = QLabel("N/A")
        self.success_rate_label = QLabel("0%")
        
        stats_layout.addWidget(QLabel("Total de Missões:"), 0, 0)
        stats_layout.addWidget(self.total_missions_label, 0, 1)
        stats_layout.addWidget(QLabel("Tempo Total de Voo:"), 1, 0)
        stats_layout.addWidget(self.total_flight_time_label, 1, 1)
        stats_layout.addWidget(QLabel("Aeronave Favorita:"), 2, 0)
        stats_layout.addWidget(self.favorite_aircraft_label, 2, 1)
        stats_layout.addWidget(QLabel("Taxa de Sucesso:"), 3, 0)
        stats_layout.addWidget(self.success_rate_label, 3, 1)
        
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

    def select_pwcgfc_folder(self):
        """Seleciona pasta PWCGFC"""
        folder_path = QFileDialog.getExistingDirectory(
            self, 'Selecionar Pasta PWCGFC', self.pwcgfc_path
        )
        if folder_path:
            self.pwcgfc_path = folder_path
            self.path_label.setText(f'Caminho: {folder_path}')
            self.save_settings()
            self.load_campaigns()
            self.sync_button.setEnabled(True)
            self.status_bar.showMessage(f'Pasta selecionada: {folder_path}')
            logger.info(f"Pasta PWCGFC selecionada: {folder_path}")

    def clear_path(self):
        """Limpa o caminho selecionado"""
        self.pwcgfc_path = ""
        self.path_label.setText('Nenhum caminho selecionado')
        self.campaign_combo.clear()
        self.sync_button.setEnabled(False)
        self.clear_all_data()
        self.save_settings()

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
        
        self.update_ui_with_data()
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage('Dados carregados com sucesso')

    def on_data_load_error(self, error_message: str):
        """Callback quando há erro no carregamento"""
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage('Erro ao carregar dados')
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
        
        # Atualiza estatísticas
        self.missions_flown_label.setText(str(self.pilot_data.missions_flown))
        self.victories_label.setText(str(self.pilot_data.victories))
        self.losses_label.setText(str(self.pilot_data.losses))
        
        # Atualiza tabelas
        self.populate_missions_table()
        self.populate_aces_table()
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
                
                # Cria diretório se não existir
                campaign_path.mkdir(parents=True, exist_ok=True)
                
                with open(pilot_file, 'w', encoding='utf-8') as f:
                    json.dump(asdict(self.pilot_data), f, indent=2, ensure_ascii=False)
                
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
                    <div class="photo">
                        <h3>Foto do Piloto</h3>
                        <!-- Foto seria inserida aqui se disponível -->
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
                <h3>Histórico de Missões</h3>
                <table>
                    <tr>
                        <th>Data</th><th>Hora</th><th>Aeronave</th><th>Tipo</th><th>Resultado</th>
                    </tr>
        """
        
        # Adiciona missões à tabela
        for mission in self.missions_data[:10]:  # Limita a 10 missões mais recentes
            html += f"""
                    <tr>
                        <td>{mission.date}</td>
                        <td>{mission.time}</td>
                        <td>{mission.aircraft}</td>
                        <td>{mission.mission_type}</td>
                        <td>{mission.result}</td>
                    </tr>
            """
        
        html += """
                </table>
            </div>
            
            <div class="section">
                <p><small>Relatório gerado em: """ + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + """</small></p>
            </div>
        </body>
        </html>
        """
        
        return html

    def sync_data(self):
        """Sincroniza dados com arquivos da campanha"""
        if not self.pwcgfc_path:
            QMessageBox.warning(self, "Aviso", "Selecione primeiro a pasta PWCGFC!")
            return
        
        current_campaign = self.campaign_combo.currentText()
        if not current_campaign:
            QMessageBox.warning(self, "Aviso", "Selecione uma campanha!")
            return
        
        try:
            self.status_bar.showMessage('Sincronizando dados...')
            
            # Simula processo de sincronização
            QTimer.singleShot(2000, lambda: self.finish_sync())
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro na sincronização: {e}")
            logger.error(f"Erro na sincronização: {e}")

    def finish_sync(self):
        """Finaliza processo de sincronização"""
        QMessageBox.information(self, "Sucesso", "Dados sincronizados com sucesso!")
        self.status_bar.showMessage('Sincronização concluída')
        self.load_campaign_data_async(self.campaign_combo.currentText())

    def create_backup(self):
        """Cria backup dos dados da campanha"""
        if not self.campaign_combo.currentText():
            QMessageBox.warning(self, "Aviso", "Selecione uma campanha!")
            return
        
        try:
            backup_dir = QFileDialog.getExistingDirectory(self, 'Selecionar Pasta para Backup')
            if backup_dir:
                campaign_name = self.campaign_combo.currentText()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{campaign_name}_backup_{timestamp}.json"
                backup_path = Path(backup_dir) / backup_name
                
                backup_data = {
                    'pilot_info': asdict(self.pilot_data),
                    'missions': [asdict(m) for m in self.missions_data],
                    'aces': [asdict(a) for a in self.aces_data],
                    'campaign_name': campaign_name,
                    'backup_date': datetime.now().isoformat()
                }
                
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, ensure_ascii=False)
                
                QMessageBox.information(self, "Sucesso", f"Backup criado: {backup_path}")
                self.status_bar.showMessage('Backup criado com sucesso')
                logger.info(f"Backup criado: {backup_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao criar backup: {e}")
            logger.error(f"Erro ao criar backup: {e}")

    def restore_backup(self):
        """Restaura backup dos dados"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, 'Selecionar Backup', '', 
                'JSON files (*.json);;Todos os arquivos (*)'
            )
            
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                
                # Restaura dados
                self.pilot_data = PilotInfo(**backup_data['pilot_info'])
                self.missions_data = [MissionData(**m) for m in backup_data['missions']]
                self.aces_data = [AceData(**a) for a in backup_data['aces']]
                
                self.update_ui_with_data()
                
                QMessageBox.information(self, "Sucesso", "Backup restaurado com sucesso!")
                self.status_bar.showMessage('Backup restaurado')
                logger.info(f"Backup restaurado: {file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao restaurar backup: {e}")
            logger.error(f"Erro ao restaurar backup: {e}")

    def clear_all_data(self):
        """Limpa todos os dados da interface"""
        # Reset pilot data
        self.pilot_data = PilotInfo()
        self.missions_data = []
        self.aces_data = []
        
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
        
        self.missions_flown_label.setText("0")
        self.victories_label.setText("0")
        self.losses_label.setText("0")
        
        # Clear tables
        self.missions_table.setRowCount(0)
        self.aces_table.setRowCount(0)
        
        # Clear text areas
        self.squad_text.clear()

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
            self.path_label.setText(f'Caminho: {saved_path}')
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
        app.setApplicationVersion("0.1")
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
