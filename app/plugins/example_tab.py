"""
An example plugin for the IL-2 Campaign Analyzer.

This module serves as a template for creating new plugins. A valid plugin
is a Python file in the `app/plugins` directory that contains a
`register_plugin` function.
"""
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout

class ExampleTab(QWidget):
    """
    A simple example of a custom tab widget provided by a plugin.
    """
    def __init__(self, parent=None):
        """
        Initialize the example tab.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Olá! Eu sou um plugin externo 🚀"))

def register_plugin(tab_manager):
    """
    Registers the plugin with the main application.

    This function is mandatory for any plugin. It is called by the
    PluginLoader during application startup.

    Args:
        tab_manager: The application's TabManager instance, which can be
                     used to register new tabs.
    """
    tab_manager.register_tab("Exemplo Plugin", ExampleTab)
