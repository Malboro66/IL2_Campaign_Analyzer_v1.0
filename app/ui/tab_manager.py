# app/ui/tab_manager.py
from PyQt5.QtWidgets import QTabWidget

class TabManager:
    def __init__(self, tab_widget: QTabWidget):
        self.tab_widget = tab_widget
        self.tabs = {}

    def register_tab(self, name: str, widget_class, *args, **kwargs):
        """
        Registra e adiciona uma aba ao QTabWidget.
        - name: título da aba
        - widget_class: classe QWidget que implementa a aba
        - args/kwargs: parâmetros passados para o construtor da aba
        """
        if name in self.tabs:
            raise ValueError(f"Aba '{name}' já registrada")

        widget = widget_class(*args, **kwargs)
        index = self.tab_widget.addTab(widget, name)
        self.tabs[name] = (widget, index)
        return widget

    def get_tab(self, name: str):
        """Retorna a instância do widget da aba pelo nome"""
        return self.tabs.get(name, (None, None))[0]

    def remove_tab(self, name: str):
        """Remove uma aba dinamicamente"""
        widget, index = self.tabs.pop(name, (None, None))
        if widget and index is not None:
            self.tab_widget.removeTab(index)
            widget.deleteLater()
