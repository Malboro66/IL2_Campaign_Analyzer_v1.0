import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QFileDialog, QLabel, 
                             QTabWidget, QTextEdit, QLineEdit, QFormLayout,
                             QScrollArea, QGroupBox, QGridLayout, QComboBox,
                             QMessageBox, QTableWidget, QTableWidgetItem,
                             QSplitter, QFrame, QProgressBar)
from PyQt5.QtCore import Qt, QSettings, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont

from data_parser import IL2DataParser
from data_processor import IL2DataProcessor
from pdf_generator import IL2PDFGenerator

class DataSyncThread(QThread):
    """Thread para sincronização de dados em background"""
    progress_updated = pyqtSignal(int)
    data_loaded = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, pwcgfc_path, campaign_name):
        super().__init__()
        self.pwcgfc_path = pwcgfc_path
        self.campaign_name = campaign_name

    def run(self):
        try:
            self.progress_updated.emit(10)
            processor = IL2DataProcessor(self.pwcgfc_path)
            
            self.progress_updated.emit(30)
            processed_data = processor.process_campaign_data(self.campaign_name)
            
            self.progress_updated.emit(80)
            
            if processed_data:
                self.data_loaded.emit(processed_data)
                self.progress_updated.emit(100)
            else:
                self.error_occurred.emit("Não foi possível carregar os dados da campanha.")
                
        except Exception as e:
            self.error_occurred.emit(f"Erro durante a sincronização: {str(e)}")

class IL2CampaignAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings('IL2CampaignAnalyzer', 'Settings')
        self.pwcgfc_path = ""
        self.current_data = {}
        self.pdf_generator = IL2PDFGenerator()
        self.sync_thread = None
        self.initUI()
        self.load_saved_path()

    def initUI(self):
        self.setWindowTitle('IL-2 Sturmovik Campaign Analyzer v1.0')
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

        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Abas principais
        self.tabs = QTabWidget()
        self.create_tabs()
        main_layout.addWidget(self.tabs)

        # Botões de ação
        buttons_layout = QHBoxLayout()
        
        sync_button = QPushButton('Sincronizar Dados')
        sync_button.clicked.connect(self.sync_data)
        buttons_layout.addWidget(sync_button)

        export_button = QPushButton('Exportar para PDF')
        export_button.clicked.connect(self.export_to_pdf)
        buttons_layout.addWidget(export_button)

        main_layout.addLayout(buttons_layout)

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
        self.squadron_label = QLabel("N/A")
        self.total_missions_label = QLabel("N/A")

        basic_info_layout.addRow("Nome do Piloto:", self.pilot_name_label)
        basic_info_layout.addRow("Número Serial:", self.pilot_serial_label)
        basic_info_layout.addRow("Esquadrão:", self.squadron_label)
        basic_info_layout.addRow("Data da Campanha:", self.campaign_date_label)
        basic_info_layout.addRow("Total de Missões:", self.total_missions_label)

        basic_info_group.setLayout(basic_info_layout)
        scroll_layout.addWidget(basic_info_group)

        # Informações complementares
        complement_info_group = QGroupBox("Informações Complementares")
        complement_layout = QFormLayout()

        self.birth_date_edit = QLineEdit()
        self.birth_date_edit.setPlaceholderText("DD/MM/AAAA")
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

        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)

        layout.addWidget(scroll)
        widget.setLayout(layout)
        return widget

    def create_squad_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # Informações do esquadrão
        self.squad_info_label = QLabel("Selecione uma campanha e sincronize os dados")
        layout.addWidget(self.squad_info_label)

        # Área de texto para atividades
        self.squad_text = QTextEdit()
        self.squad_text.setReadOnly(True)
        layout.addWidget(self.squad_text)

        widget.setLayout(layout)
        return widget

    def create_aces_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.aces_table = QTableWidget()
        self.aces_table.setColumnCount(4)
        self.aces_table.setHorizontalHeaderLabels(["Posição", "Nome", "Esquadrão", "Vitórias"])
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
        # Limpar dados anteriores
        self.clear_all_data()

    def sync_data(self):
        if not self.pwcgfc_path:
            QMessageBox.warning(self, "Aviso", "Selecione primeiro a pasta PWCGFC!")
            return

        current_campaign = self.campaign_combo.currentText()
        if not current_campaign:
            QMessageBox.warning(self, "Aviso", "Selecione uma campanha!")
            return

        # Iniciar sincronização em thread separada
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.sync_thread = DataSyncThread(self.pwcgfc_path, current_campaign)
        self.sync_thread.progress_updated.connect(self.progress_bar.setValue)
        self.sync_thread.data_loaded.connect(self.on_data_loaded)
        self.sync_thread.error_occurred.connect(self.on_sync_error)
        self.sync_thread.start()

    def on_data_loaded(self, processed_data):
        self.current_data = processed_data
        self.update_all_tabs()
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "Sucesso", "Dados sincronizados com sucesso!")

    def on_sync_error(self, error_message):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Erro", error_message)

    def update_all_tabs(self):
        if not self.current_data:
            return

        self.update_pilot_profile_tab()
        self.update_squad_tab()
        self.update_aces_tab()
        self.update_missions_tab()

    def update_pilot_profile_tab(self):
        pilot_data = self.current_data.get('pilot', {})
        
        self.pilot_name_label.setText(pilot_data.get('name', 'N/A'))
        self.pilot_serial_label.setText(str(pilot_data.get('serial_number', 'N/A')))
        self.squadron_label.setText(pilot_data.get('squadron', 'N/A'))
        self.campaign_date_label.setText(pilot_data.get('campaign_date', 'N/A'))
        self.total_missions_label.setText(str(pilot_data.get('total_missions', 0)))

        # Carregar informações complementares salvas
        if pilot_data.get('birth_date'):
            self.birth_date_edit.setText(pilot_data['birth_date'])
        if pilot_data.get('birth_place'):
            self.birth_place_edit.setText(pilot_data['birth_place'])
        if pilot_data.get('age'):
            self.age_label.setText(f"{pilot_data['age']} anos")

    def update_squad_tab(self):
        squad_data = self.current_data.get('squad', {})
        
        info_text = f"Esquadrão: {squad_data.get('name', 'N/A')}\n"
        info_text += f"Total de Vitórias: {squad_data.get('total_victories', 0)}\n"
        info_text += f"Membros Conhecidos: {len(squad_data.get('members', []))}"
        
        self.squad_info_label.setText(info_text)

        # Atividades recentes
        activities_text = "Atividades Recentes:\n\n"
        for activity in squad_data.get('recent_activities', []):
            activities_text += f"{activity.get('date', 'N/A')}: {activity.get('activity', 'N/A')}\n\n"
        
        self.squad_text.setText(activities_text)

    def update_aces_tab(self):
        aces_data = self.current_data.get('aces', [])
        
        self.aces_table.setRowCount(len(aces_data))
        
        for row, ace in enumerate(aces_data):
            self.aces_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.aces_table.setItem(row, 1, QTableWidgetItem(ace.get('name', 'N/A')))
            self.aces_table.setItem(row, 2, QTableWidgetItem(ace.get('squadron', 'N/A')))
            self.aces_table.setItem(row, 3, QTableWidgetItem(str(ace.get('victories', 0))))

        self.aces_table.resizeColumnsToContents()

    def update_missions_tab(self):
        missions_data = self.current_data.get('missions', [])
        
        self.missions_table.setRowCount(len(missions_data))
        
        for row, mission in enumerate(missions_data):
            self.missions_table.setItem(row, 0, QTableWidgetItem(mission.get('date', 'N/A')))
            self.missions_table.setItem(row, 1, QTableWidgetItem(mission.get('time', 'N/A')))
            self.missions_table.setItem(row, 2, QTableWidgetItem(mission.get('aircraft', 'N/A')))
            self.missions_table.setItem(row, 3, QTableWidgetItem(mission.get('duty', 'N/A')))
            self.missions_table.setItem(row, 4, QTableWidgetItem(mission.get('locality', 'N/A')))
            self.missions_table.setItem(row, 5, QTableWidgetItem(mission.get('altitude', 'N/A')))

        self.missions_table.resizeColumnsToContents()

    def clear_all_data(self):
        # Limpar dados das abas
        self.pilot_name_label.setText("N/A")
        self.pilot_serial_label.setText("N/A")
        self.squadron_label.setText("N/A")
        self.campaign_date_label.setText("N/A")
        self.total_missions_label.setText("N/A")
        self.age_label.setText("N/A")
        
        self.squad_info_label.setText("Selecione uma campanha e sincronize os dados")
        self.squad_text.clear()
        
        self.aces_table.setRowCount(0)
        self.missions_table.setRowCount(0)

    def attach_photo(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Selecionar Foto', '', 'Imagens (*.png *.jpg *.jpeg)')
        if file_path:
            pixmap = QPixmap(file_path)
            scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.photo_label.setPixmap(scaled_pixmap)
            
            # Salvar caminho da foto
            self.photo_path = file_path

    def save_pilot_info(self):
        birth_date = self.birth_date_edit.text().strip()
        birth_place = self.birth_place_edit.text().strip()
        
        if not birth_date and not birth_place:
            QMessageBox.warning(self, "Aviso", "Preencha pelo menos um campo!")
            return

        # Validar formato da data
        if birth_date:
            try:
                from datetime import datetime
                datetime.strptime(birth_date, '%d/%m/%Y')
            except ValueError:
                QMessageBox.warning(self, "Aviso", "Formato de data inválido! Use DD/MM/AAAA")
                return

        # Salvar informações
        processor = IL2DataProcessor(self.pwcgfc_path)
        photo_path = getattr(self, 'photo_path', None)
        
        if processor.save_pilot_complement_info(birth_date, birth_place, photo_path):
            QMessageBox.information(self, "Sucesso", "Informações salvas com sucesso!")
            
            # Recalcular idade se possível
            if birth_date and self.current_data.get('pilot', {}).get('last_mission_date'):
                try:
                    from datetime import datetime
                    birth_date_obj = datetime.strptime(birth_date, '%d/%m/%Y')
                    last_mission = self.current_data['pilot']['last_mission_date']
                    age = last_mission.year - birth_date_obj.year
                    if last_mission.month < birth_date_obj.month or \
                       (last_mission.month == birth_date_obj.month and last_mission.day < birth_date_obj.day):
                        age -= 1
                    self.age_label.setText(f"{age} anos")
                except:
                    pass
        else:
            QMessageBox.critical(self, "Erro", "Erro ao salvar informações!")

    def export_to_pdf(self):
        if not self.current_data:
            QMessageBox.warning(self, "Aviso", "Sincronize os dados primeiro!")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, 'Salvar PDF', '', 'PDF (*.pdf)')
        if file_path:
            try:
                if self.pdf_generator.generate_pilot_report(self.current_data, file_path):
                    QMessageBox.information(self, "Sucesso", f"PDF gerado com sucesso!\n{file_path}")
                else:
                    QMessageBox.critical(self, "Erro", "Erro ao gerar PDF!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao gerar PDF: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = IL2CampaignAnalyzer()
    ex.show()
    sys.exit(app.exec_())

