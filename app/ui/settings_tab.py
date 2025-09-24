"""
Defines the UI tab for application settings.
"""
from __future__ import annotations
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton, QFileDialog, QFormLayout
from PyQt5.QtCore import QSettings

class SettingsTab(QWidget):
    """
    A widget for configuring application-wide settings.

    This tab allows the user to change settings like the UI theme and
    default export options. Settings are persisted using QSettings.
    """
    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the SettingsTab.

        Args:
            parent (QWidget | None, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.settings = QSettings("IL2CampaignAnalyzer", "Settings")
        self._setup_ui()
        self.load_settings()

    def _setup_ui(self) -> None:
        """
        Set up the user interface for the tab.
        """
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.cmb_theme = QComboBox()
        self.cmb_theme.addItems(["Claro", "Escuro"])
        form.addRow(QLabel("Tema da interface:"), self.cmb_theme)
        self.cmb_export_format = QComboBox()
        self.cmb_export_format.addItems(["TXT", "PDF", "CSV"])
        form.addRow(QLabel("Formato padrão de exportação:"), self.cmb_export_format)
        self.btn_export_folder = QPushButton("Selecionar pasta…")
        self.lbl_export_folder = QLabel("Nenhuma pasta definida")
        self.btn_export_folder.clicked.connect(self.select_export_folder)
        form.addRow(QLabel("Pasta padrão de exportação:"), self.btn_export_folder)
        form.addRow(QLabel("Atual:"), self.lbl_export_folder)
        layout.addLayout(form)
        self.btn_save = QPushButton("Salvar Configurações")
        self.btn_save.clicked.connect(self.save_settings)
        layout.addWidget(self.btn_save)

    def load_settings(self) -> None:
        """
        Load the settings from QSettings and update the UI controls.
        """
        theme = self.settings.value("theme", "Claro")
        export_format = self.settings.value("export_format", "TXT")
        export_folder = self.settings.value("export_folder", "")
        it = self.cmb_theme.findText(theme)
        if it >= 0: self.cmb_theme.setCurrentIndex(it)
        ie = self.cmb_export_format.findText(export_format)
        if ie >= 0: self.cmb_export_format.setCurrentIndex(ie)
        if export_folder: self.lbl_export_folder.setText(export_folder)

    def save_settings(self) -> None:
        """
        Save the current values from the UI controls to QSettings.
        """
        self.settings.setValue("theme", self.cmb_theme.currentText())
        self.settings.setValue("export_format", self.cmb_export_format.currentText())
        self.settings.setValue("export_folder", self.lbl_export_folder.text())

    def select_export_folder(self) -> None:
        """
        Open a dialog to select the default folder for exports.
        """
        folder = QFileDialog.getExistingDirectory(self, "Selecionar pasta de exportação")
        if folder: self.lbl_export_folder.setText(folder)
