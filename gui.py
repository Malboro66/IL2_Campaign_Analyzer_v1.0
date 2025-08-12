import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QFileDialog, QLabel, 
                             QTabWidget, QTextEdit, QLineEdit, QFormLayout,
                             QScrollArea, QGroupBox, QGridLayout, QComboBox,
                             QMessageBox, QTableWidget, QTableWidgetItem,
                             QSplitter, QFrame)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QPixmap, QFont

class IL2CampaignAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings('IL2CampaignAnalyzer', 'Settings')
        self.pwcgfc_path = ""
        self.campaign_data = {}
        self.pilot_data = {}
        self.initUI()
        self.load_saved_path()

    def initUI(self):
        self.setWindowTitle('IL-2 Sturmovik Campaign Analyzer')
        self.setGeometry(100, 100, 1200, 800)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Seção de seleção de pasta
        path_section = self.create_path_selection_section()
        main_layout.addWidget(path_section)

        # Seção de seleção de campanha
        campaign_section = self.create_campaign_selection_section()
        main_layout.addWidget(campaign_section)

        # Abas principais
        self.tabs = QTabWidget()
        self.create_tabs()
        main_layout.addWidget(self.tabs)

        # Botão de sincronização
        sync_button = QPushButton('Sincronizar Dados')
        sync_button.clicked.connect(self.sync_data)
        main_layout.addWidget(sync_button)

    def create_path_selection_section(self):
        group_box = QGroupBox("Configuração de Pasta")
        layout = QVBoxLayout()

        # Label para mostrar o caminho atual
        self.path_label = QLabel('Nenhum caminho selecionado')
        self.path_label.setWordWrap(True)
        layout.addWidget(self.path_label)

        # Botão para selecionar pasta
        select_button = QPushButton('Selecionar Pasta PWCGFC')
        select_button.clicked.connect(self.select_pwcgfc_folder)
        layout.addWidget(select_button)

        group_box.setLayout(layout)
        return group_box

    def create_campaign_selection_section(self):
        group_box = QGroupBox("Seleção de Campanha")
        layout = QHBoxLayout()

        self.campaign_combo = QComboBox()
        self.campaign_combo.currentTextChanged.connect(self.on_campaign_selected)
        layout.addWidget(QLabel("Campanha:"))
        layout.addWidget(self.campaign_combo)

        group_box.setLayout(layout)
        return group_box

    def create_tabs(self):
        # Aba Pilot Profile
        self.tab_pilot_profile = self.create_pilot_profile_tab()
        self.tabs.addTab(self.tab_pilot_profile, 'Pilot Profile')

        # Aba Squad
        self.tab_squad = self.create_squad_tab()
        self.tabs.addTab(self.tab_squad, 'Squad')

        # Aba Aces
        self.tab_aces = self.create_aces_tab()
        self.tabs.addTab(self.tab_aces, 'Aces')

        # Aba Missions
        self.tab_missions = self.create_missions_tab()
        self.tabs.addTab(self.tab_missions, 'Missions')

    def create_pilot_profile_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # Scroll area para o conteúdo
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()

        # Informações básicas do piloto
        basic_info_group = QGroupBox("Informações Básicas")
        basic_info_layout = QFormLayout()

        self.pilot_name_label = QLabel("N/A")
        self.pilot_serial_label = QLabel("N/A")
        self.campaign_date_label = QLabel("N/A")

        basic_info_layout.addRow("Nome do Piloto:", self.pilot_name_label)
        basic_info_layout.addRow("Número Serial:", self.pilot_serial_label)
        basic_info_layout.addRow("Data da Campanha:", self.campaign_date_label)

        basic_info_group.setLayout(basic_info_layout)
        scroll_layout.addWidget(basic_info_group)

        # Informações complementares
        complement_info_group = QGroupBox("Informações Complementares")
        complement_layout = QFormLayout()

        self.birth_date_edit = QLineEdit()
        self.birth_place_edit = QLineEdit()
        self.age_label = QLabel("N/A")

        complement_layout.addRow("Data de Nascimento:", self.birth_date_edit)
        complement_layout.addRow("Local de Nascimento:", self.birth_place_edit)
        complement_layout.addRow("Idade:", self.age_label)

        # Botão para anexar foto
        photo_button = QPushButton("Anexar Foto")
        photo_button.clicked.connect(self.attach_photo)
        complement_layout.addRow("Foto:", photo_button)

        # Label para mostrar a foto
        self.photo_label = QLabel("Nenhuma foto anexada")
        self.photo_label.setMinimumSize(200, 200)
        self.photo_label.setStyleSheet("border: 1px solid gray;")
        self.photo_label.setAlignment(Qt.AlignCenter)
        complement_layout.addRow("", self.photo_label)

        complement_info_group.setLayout(complement_layout)
        scroll_layout.addWidget(complement_info_group)

        # Botão para salvar informações complementares
        save_button = QPushButton("Salvar Informações Complementares")
        save_button.clicked.connect(self.save_pilot_info)
        scroll_layout.addWidget(save_button)

        # Botão para exportar PDF
        export_button = QPushButton("Exportar para PDF")
        export_button.clicked.connect(self.export_to_pdf)
        scroll_layout.addWidget(export_button)

        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)

        layout.addWidget(scroll)
        widget.setLayout(layout)
        return widget

    def create_squad_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.squad_text = QTextEdit()
        self.squad_text.setReadOnly(True)
        layout.addWidget(self.squad_text)

        widget.setLayout(layout)
        return widget

    def create_aces_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.aces_table = QTableWidget()
        self.aces_table.setColumnCount(3)
        self.aces_table.setHorizontalHeaderLabels(["Nome", "Esquadrão", "Abates"])
        layout.addWidget(self.aces_table)

        widget.setLayout(layout)
        return widget

    def create_missions_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.missions_table = QTableWidget()
        self.missions_table.setColumnCount(6)
        self.missions_table.setHorizontalHeaderLabels(["Data", "Hora", "Aeronave", "Missão", "Local", "Altitude"])
        layout.addWidget(self.missions_table)

        widget.setLayout(layout)
        return widget

    def select_pwcgfc_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, 'Selecionar Pasta PWCGFC')
        if folder_path:
            self.pwcgfc_path = folder_path
            self.path_label.setText(f'Caminho selecionado: {folder_path}')
            self.save_path()
            self.load_campaigns()

    def save_path(self):
        self.settings.setValue('pwcgfc_path', self.pwcgfc_path)

    def load_saved_path(self):
        saved_path = self.settings.value('pwcgfc_path', '')
        if saved_path and os.path.exists(saved_path):
            self.pwcgfc_path = saved_path
            self.path_label.setText(f'Caminho selecionado: {saved_path}')
            self.load_campaigns()

    def load_campaigns(self):
        if not self.pwcgfc_path:
            return

        campaigns_path = os.path.join(self.pwcgfc_path, 'User', 'Campaigns')
        if not os.path.exists(campaigns_path):
            QMessageBox.warning(self, "Aviso", "Pasta de campanhas não encontrada!")
            return

        self.campaign_combo.clear()
        for item in os.listdir(campaigns_path):
            item_path = os.path.join(campaigns_path, item)
            if os.path.isdir(item_path):
                self.campaign_combo.addItem(item)

    def on_campaign_selected(self, campaign_name):
        if not campaign_name:
            return
        # TODO: Carregar dados da campanha selecionada

    def sync_data(self):
        if not self.pwcgfc_path:
            QMessageBox.warning(self, "Aviso", "Selecione primeiro a pasta PWCGFC!")
            return

        current_campaign = self.campaign_combo.currentText()
        if not current_campaign:
            QMessageBox.warning(self, "Aviso", "Selecione uma campanha!")
            return

        # TODO: Implementar sincronização de dados
        QMessageBox.information(self, "Info", "Sincronização de dados será implementada!")

    def attach_photo(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Selecionar Foto', '', 'Imagens (*.png *.jpg *.jpeg)')
        if file_path:
            pixmap = QPixmap(file_path)
            scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.photo_label.setPixmap(scaled_pixmap)

    def save_pilot_info(self):
        # TODO: Implementar salvamento das informações complementares
        QMessageBox.information(self, "Info", "Salvamento de informações será implementado!")

    def export_to_pdf(self):
        # TODO: Implementar exportação para PDF
        QMessageBox.information(self, "Info", "Exportação para PDF será implementada!")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = IL2CampaignAnalyzer()
    ex.show()
    sys.exit(app.exec_())

