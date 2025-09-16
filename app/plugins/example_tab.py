# app/plugins/example_tab.py
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout

class ExampleTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Olá! Eu sou um plugin externo 🚀"))

def register_plugin(tab_manager):
    """Função obrigatória para registro do plugin"""
    tab_manager.register_tab("Exemplo Plugin", ExampleTab)
