"""
Main application entry point for the IL-2 Campaign Analyzer.

This module initializes the PyQt5 application, sets up the main window,
and manages the primary user interface, including data synchronization,
UI updates, and report generation.
"""
from __future__ import annotations

import sys
import os
import tempfile
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QTabWidget, QComboBox,
    QMessageBox, QProgressBar, QStatusBar, QFormLayout
)
from PyQt5.QtCore import QSettings, QThread, pyqtSignal, QLockFile

# Preferir modo pacote
try:
    from app.ui.base_tab import BaseTab
    from app.ui.missions_tab import MissionsTab
    from app.ui.squadron_tab import SquadronTab
    from app.ui.aces_tab import AcesTab
    from app.ui.stats_tab import StatsTab
    from app.ui.dashboard_tab import DashboardTab
    from app.ui.settings_tab import SettingsTab
    from app.ui.achievements_tab import AchievementsTab
    from app.ui.notifications_tab import NotificationsTab
    from app.ui.tab_manager import TabManager

    from app.core.data_parser import IL2DataParser
    from app.core.data_processor import IL2DataProcessor
    from app.core.report_generator import IL2ReportGenerator
    from app.core.signals import signals
    from app.core.plugins import PluginLoader
    from app.core.notifications import notification_center
    try:
        from app.core.achievements import achievement_system
    except Exception:
        achievement_system = None
except Exception:
    # Fallback local opcional
    from base_tab import BaseTab
    from missions_tab import MissionsTab
    from squadron_tab import SquadronTab
    from aces_tab import AcesTab
    from stats_tab import StatsTab
    from dashboard_tab import DashboardTab
    from settings_tab import SettingsTab
    from achievements_tab import AchievementsTab
    from notifications_tab import NotificationsTab
    from tab_manager import TabManager

    from data_parser import IL2DataParser
    from data_processor import IL2DataProcessor
    from report_generator import IL2ReportGenerator
    from signals import signals
    from plugins import PluginLoader
    from notifications import notification_center
    try:
        from achievements import achievement_system
    except Exception:
        achievement_system = None


class DataSyncThread(QThread):
    """
    Worker thread for synchronously processing campaign data.

    This QThread runs the data processing in the background to prevent the UI
    from freezing. It emits signals to update the main window on progress,

    completion, or errors.

    Attributes:
        data_loaded (pyqtSignal): Emitted when data is successfully processed.
        error_occurred (pyqtSignal): Emitted when an error occurs during processing.
        progress (pyqtSignal): Emitted to update the progress bar.
        started_sync (pyqtSignal): Emitted when the thread starts processing.
    """
    data_loaded = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    progress = pyqtSignal(int)
    started_sync = pyqtSignal()

    def __init__(self, pwcgfc_path: str, campaign_name: str, parent=None):
        """
        Initialize the data synchronization thread.

        Args:
            pwcgfc_path (str): The file path to the PWCGFC directory.
            campaign_name (str): The name of the campaign to process.
            parent (QObject, optional): The parent object. Defaults to None.
        """
        super().__init__(parent)
        self.pwcgfc_path = pwcgfc_path
        self.campaign_name = campaign_name

    def run(self):
        """
        Execute the data processing task.

        Initializes the data processor, processes the campaign, and emits
        signals based on the outcome.
        """
        try:
            self.started_sync.emit()
            self.progress.emit(5)
            processor = IL2DataProcessor(self.pwcgfc_path)
            self.progress.emit(30)
            processed_data = processor.process_campaign(self.campaign_name)
            self.progress.emit(90)
            if not processed_data:
                self.error_occurred.emit("Não foi possível carregar os dados da campanha.")
                self.progress.emit(0)
                return
            self.data_loaded.emit(processed_data)
            self.progress.emit(100)
        except Exception as e:
            self.error_occurred.emit(f"Erro ao sincronizar dados: {e}")
            try:
                self.progress.emit(0)
            except Exception:
                pass


class IL2CampaignAnalyzer(QMainWindow):
    """
    The main window for the IL-2 Campaign Analyzer application.

    This class sets up the user interface, manages application state,
    and connects UI elements to the underlying data processing and
    reporting logic.
    """
    def __init__(self):
        """
        Initialize the main application window.
        """
        super().__init__()
        self.settings = QSettings("IL2CampaignAnalyzer", "Settings")
        self.pwcgfc_path: str = ""
        self.current_data: dict = {}
        self.selected_mission_index: int = -1
        self.report_generator = IL2ReportGenerator()
        self.sync_thread: DataSyncThread | None = None

        self.setup_ui()
        self._connect_signals()
        self.load_saved_settings()

    def setup_ui(self):
        """
        Initialize and arrange all UI widgets in the main window.
        """
        self.setWindowTitle("IL-2 Campaign Analyzer")
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.path_label = QLabel("Nenhum caminho selecionado")
        main_layout.addWidget(self.path_label)

        select_path_button = QPushButton("Selecionar Pasta PWCGFC")
        select_path_button.clicked.connect(self.select_pwcgfc_folder)
        main_layout.addWidget(select_path_button)

        campaign_layout = QHBoxLayout()
        campaign_layout.addWidget(QLabel("Campanha:"))
        self.campaign_combo = QComboBox()
        campaign_layout.addWidget(self.campaign_combo)
        main_layout.addLayout(campaign_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        self.tabs = QTabWidget()
        self.create_tabs()
        main_layout.addWidget(self.tabs)

        buttons_layout = QHBoxLayout()

        sync_button = QPushButton("Sincronizar Dados")
        sync_button.clicked.connect(self.sync_data)
        buttons_layout.addWidget(sync_button)

        self.diary_button = QPushButton("Gerar Diário de Bordo (.txt)")
        self.diary_button.clicked.connect(self.export_diary)
        self.diary_button.setEnabled(False)
        buttons_layout.addWidget(self.diary_button)

        self.export_pdf_button = QPushButton("Exportar Missão para PDF")
        self.export_pdf_button.clicked.connect(self.export_mission_pdf)
        self.export_pdf_button.setEnabled(False)
        buttons_layout.addWidget(self.export_pdf_button)

        main_layout.addLayout(buttons_layout)

        self.setStatusBar(QStatusBar())

    def create_tabs(self):
        """
        Create and register all the tabs for the main interface.
        """
        self.tab_manager = TabManager(self.tabs)

        self.tab_dashboard = self.tab_manager.register_tab("Dashboard", DashboardTab, parent=self)

        profile_tab = QWidget()
        profile_layout = QFormLayout(profile_tab)
        self.pilot_name_label = QLabel("N/A")
        self.squadron_name_label = QLabel("N/A")
        self.total_missions_label = QLabel("N/A")
        profile_layout.addRow("Nome:", self.pilot_name_label)
        profile_layout.addRow("Esquadrão:", self.squadron_name_label)
        profile_layout.addRow("Missões Voadas:", self.total_missions_label)
        self.tab_manager.register_tab("Perfil do Piloto", lambda: profile_tab)

        self.tab_squadron = self.tab_manager.register_tab("Esquadrão", SquadronTab, parent=self)
        self.tab_missions = self.tab_manager.register_tab("Missões", MissionsTab, parent=self)
        self.tab_aces = self.tab_manager.register_tab("Ases da Campanha", AcesTab, parent=self)
        self.tab_stats = self.tab_manager.register_tab("Estatísticas", StatsTab, parent=self)
        self.tab_achievements = self.tab_manager.register_tab("Conquistas", AchievementsTab, parent=self)
        self.tab_notifications = self.tab_manager.register_tab("Notificações", NotificationsTab, parent=self)
        self.tab_settings = self.tab_manager.register_tab("Configurações", SettingsTab, parent=self)

        self.plugin_loader = PluginLoader()
        try:
            self.plugin_loader.discover_plugins()
            self.plugin_loader.register_tabs(self.tab_manager)
        except Exception:
            pass

    def _connect_signals(self):
        """
        Connect global application signals to their corresponding slots.
        """
        signals.mission_selected.connect(self.on_mission_selected)
        signals.squadron_member_selected.connect(self.on_squadron_member_selected)
        signals.ace_selected.connect(self.on_ace_selected)
        signals.data_loaded.connect(self._on_global_data_loaded)

    def _on_global_data_loaded(self, data):
        """
        Slot to handle globally loaded data.

        Args:
            data (dict): The loaded campaign data.
        """
        if isinstance(data, dict):
            self.current_data = data
            self.update_ui_with_data()

    def load_campaigns(self):
        """
        Load the list of available campaigns from the PWCGFC directory.
        """
        if not self.pwcgfc_path:
            return
        parser = IL2DataParser(self.pwcgfc_path)
        campaigns = parser.get_campaigns()
        self.campaign_combo.clear()
        self.campaign_combo.addItems(campaigns)

    def sync_data(self):
        """
        Start the data synchronization process in a background thread.
        """
        current_campaign = self.campaign_combo.currentText()
        if not self.pwcgfc_path or not current_campaign:
            QMessageBox.warning(self, "Aviso", "Selecione a pasta e uma campanha primeiro!")
            return
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.sync_thread = DataSyncThread(self.pwcgfc_path, current_campaign)
        self.sync_thread.data_loaded.connect(self.on_data_loaded)
        self.sync_thread.error_occurred.connect(self.on_sync_error)
        self.sync_thread.progress.connect(self.progress_bar.setValue)
        self.sync_thread.started_sync.connect(lambda: self.progress_bar.setVisible(True))
        self.sync_thread.start()

    def on_data_loaded(self, data):
        """
        Slot to handle successfully loaded data from the sync thread.

        Args:
            data (dict): The processed campaign data.
        """
        if not isinstance(data, dict):
            QMessageBox.critical(self, "Erro", "Dados inválidos recebidos do processador.")
            self.progress_bar.setVisible(False)
            return
        self.current_data = data
        try:
            signals.data_loaded.emit(data)
        except Exception:
            pass
        self.update_ui_with_data()
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("Dados carregados com sucesso!", 5000)

    def on_sync_error(self, message):
        """
        Slot to handle errors reported by the sync thread.

        Args:
            message (str): The error message.
        """
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Erro de Sincronização", message)
        self.statusBar().showMessage("Falha ao carregar dados.", 5000)

    def update_ui_with_data(self):
        """
        Update all UI elements with the newly loaded campaign data.
        """
        self.export_pdf_button.setEnabled(False)
        self.diary_button.setEnabled(False)
        self.selected_mission_index = -1

        pilot_data = self.current_data.get("pilot", {})
        self.pilot_name_label.setText(pilot_data.get("name", "N/A"))
        self.squadron_name_label.setText(pilot_data.get("squadron", "N/A"))
        self.total_missions_label.setText(str(pilot_data.get("total_missions", "0")))

        for tab_name, (tab_widget, _) in self.tab_manager.tabs.items():
            try:
                if hasattr(tab_widget, "update_data"):
                    if tab_name == "Missões":
                        tab_widget.update_data(self.current_data.get("missions", []))
                    elif tab_name == "Ases da Campanha":
                        tab_widget.update_data(self.current_data.get("aces", []))
                    elif tab_name == "Esquadrão":
                        tab_widget.update_data(self.current_data.get("squadron_members", []))
                    elif tab_name == "Notificações":
                        tab_widget.update_data(self.current_data)
                    else:
                        tab_widget.update_data(self.current_data)
            except Exception as e:
                print(f"Erro ao atualizar a aba {tab_name}: {e}")
                self.statusBar().showMessage(
                    f"Erro ao atualizar {tab_name}. Veja o console para detalhes.", 5000
                )

        if self.current_data:
            self.diary_button.setEnabled(True)

        try:
            if achievement_system:
                achievement_system.check_achievements(self.current_data)
        except Exception:
            pass

        pilot_kills = int(pilot_data.get("kills", 0) or 0)
        if pilot_kills >= 10:
            notification_center.send(
                f"{pilot_data.get('name', 'Piloto')} atingiu {pilot_kills} vitórias!", "info"
            )

        total_losses = sum(int(m.get("losses", 0) or 0) for m in self.current_data.get("missions", []))
        if total_losses > 5:
            notification_center.send(
                f"Alerta: o esquadrão sofreu {total_losses} perdas!", "warning"
            )

    def on_mission_selected(self, mission_data):
        """
        Slot to handle the selection of a mission in the missions tab.

        Enables or disables the PDF export button based on the selection.

        Args:
            mission_data (dict): The data for the selected mission.
        """
        if mission_data:
            self.export_pdf_button.setEnabled(True)
            try:
                self.selected_mission_index = getattr(self.tab_missions, "selected_index", -1)
            except Exception:
                self.selected_mission_index = -1
        else:
            self.export_pdf_button.setEnabled(False)
            self.selected_mission_index = -1

    def on_squadron_member_selected(self, member_data):
        """
        Slot to handle the selection of a squadron member.

        Args:
            member_data (dict): The data for the selected member.
        """
        self.statusBar().showMessage(
            f"Selecionado: {member_data.get('name')} ({member_data.get('rank')})", 4000
        )

    def on_ace_selected(self, ace_data):
        """
        Slot to handle the selection of a campaign ace.

        Args:
            ace_data (dict): The data for the selected ace.
        """
        self.statusBar().showMessage(
            f"Ás selecionado: {ace_data.get('name')} ({ace_data.get('victories')} vitórias)", 4000
        )

    def export_diary(self):
        """
        Export the entire campaign diary to a text file.
        """
        if not self.current_data:
            QMessageBox.warning(self, "Aviso", "Sincronize os dados de uma campanha primeiro!")
            return
        diary_content = self.report_generator.generate_campaign_diary_txt(self.current_data)
        pilot_name = self.current_data.get("pilot", {}).get("name", "Piloto").replace(" ", "_")
        default_filename = f"Diario_de_Bordo_{pilot_name}.txt"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salvar Diário de Bordo", default_filename, "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(diary_content)
                QMessageBox.information(self, "Sucesso", f"Diário salvo em: {file_path}")
            except IOError as e:
                QMessageBox.critical(self, "Erro", f"Falha ao salvar diário: {e}")

    def export_mission_pdf(self):
        """
        Export the details of the selected mission to a PDF file.
        """
        if self.selected_mission_index == -1:
            QMessageBox.warning(self, "Aviso", "Selecione uma missão para exportar.")
            return
        try:
            mission_to_export = self.current_data["missions"][self.selected_mission_index]
        except Exception:
            QMessageBox.warning(self, "Aviso", "Índice de missão inválido.")
            return
        default_filename = f"Missao_{mission_to_export.get('date','').replace('/', '-')}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salvar Relatório da Missão", default_filename, "PDF (*.pdf)"
        )
        if file_path:
            success = self.report_generator.generate_mission_report_pdf(
                mission_data=mission_to_export,
                all_missions=self.current_data.get("missions", []),
                mission_index=self.selected_mission_index,
                output_path=file_path,
            )
            if success:
                QMessageBox.information(self, "Sucesso", f"Relatório salvo em: {file_path}")
            else:
                QMessageBox.critical(self, "Erro", "Não foi possível gerar o PDF da missão.")

    def select_pwcgfc_folder(self):
        """
        Open a dialog to select the PWCGFC folder and save the path.
        """
        folder_path = QFileDialog.getExistingDirectory(self, "Selecionar Pasta PWCGFC")
        if folder_path:
            self.pwcgfc_path = folder_path
            self.path_label.setText(f"Caminho: {folder_path}")
            self.settings.setValue("pwcgfc_path", self.pwcgfc_path)
            self.load_campaigns()

    def load_saved_settings(self):
        """
        Load the PWCGFC folder path from application settings.
        """
        saved_path = self.settings.value("pwcgfc_path", "")
        if saved_path and os.path.exists(saved_path):
            self.pwcgfc_path = saved_path
            self.path_label.setText(f"Caminho: {saved_path}")
            self.load_campaigns()

    def closeEvent(self, event):
        """
        Handle the window close event.

        Saves the current PWCGFC path to settings before closing.

        Args:
            event (QCloseEvent): The close event.
        """
        self.settings.setValue("pwcgfc_path", self.pwcgfc_path)
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("IL2 Campaign Analyzer")
    app.setOrganizationName("IL2CampaignAnalyzer")

    try:
        qss_path = Path(__file__).parent / "resources" / "style.qss"
        if qss_path.exists():
            with open(qss_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
    except Exception:
        pass

    try:
        notification_center.setup_tray(app)
    except Exception:
        pass

    lockfile_path = str(Path(tempfile.gettempdir()) / "il2_campaign_analyzer.lock")
    lock = QLockFile(lockfile_path)
    lock.setStaleLockTime(0)
    if not lock.tryLock(100):
        QMessageBox.warning(None, "Instância em execução", "Outra instância já está aberta.")
        sys.exit(0)

    window = IL2CampaignAnalyzer()
    window.show()
    exit_code = app.exec_()

    if lock.isLocked():
        lock.unlock()
    sys.exit(exit_code)
