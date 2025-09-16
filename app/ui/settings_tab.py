# app/ui/settings_tab.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton, QFileDialog, QFormLayout
)
from PyQt5.QtCore import QSettings


class SettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings('IL2CampaignAnalyzer', 'Settings')
        self._setup_ui()
        self.load_settings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # Tema
        self.cmb_theme = QComboBox()
        self.cmb_theme.addItems(["Claro", "Escuro"])
        form.addRow(QLabel("Tema da interface:"), self.cmb_theme)

        # Formato exportação
        self.cmb_export_format = QComboBox()
        self.cmb_export_format.addItems(["TXT", "PDF", "CSV"])
        form.addRow(QLabel("Formato padrão de exportação:"), self.cmb_export_format)

        # Pasta exportação
        self.btn_export_folder = QPushButton("Selecionar pasta…")
        self.lbl_export_folder = QLabel("Nenhuma pasta definida")
        self.btn_export_folder.clicked.connect(self.select_export_folder)
        form.addRow(QLabel("Pasta padrão de exportação:"), self.btn_export_folder)
        form.addRow(QLabel("Atual:"), self.lbl_export_folder)

        layout.addLayout(form)

        # Botão salvar
        self.btn_save = QPushButton("Salvar Configurações")
        self.btn_save.clicked.connect(self.save_settings)
        layout.addWidget(self.btn_save)

    def load_settings(self):
        theme = self.settings.value("theme", "Claro")
        export_format = self.settings.value("export_format", "TXT")
        export_folder = self.settings.value("export_folder", "")

        idx_theme = self.cmb_theme.findText(theme)
        if idx_theme >= 0:
            self.cmb_theme.setCurrentIndex(idx_theme)

        idx_format = self.cmb_export_format.findText(export_format)
        if idx_format >= 0:
            self.cmb_export_format.setCurrentIndex(idx_format)

        if export_folder:
            self.lbl_export_folder.setText(export_folder)

    def save_settings(self):
        self.settings.setValue("theme", self.cmb_theme.currentText())
        self.settings.setValue("export_format", self.cmb_export_format.currentText())
        self.settings.setValue("export_folder", self.lbl_export_folder.text())

    def select_export_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Selecionar pasta de exportação")
        if folder:
            self.lbl_export_folder.setText(folder)
