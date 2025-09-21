from __future__ import annotations
from PyQt5.QtWidgets import QTabWidget

class TabManager:
    def __init__(self, tab_widget: QTabWidget) -> None:
        self.tab_widget = tab_widget
        self.tabs: dict[str, tuple[object, int]] = {}

    def register_tab(self, name: str, widget_class, *args, **kwargs):
        if name in self.tabs:
            raise ValueError(f"Aba '{name}' já registrada")
        widget = widget_class(*args, **kwargs)
        index = self.tab_widget.addTab(widget, name)
        self.tabs[name] = (widget, index)
        return widget

    def get_tab(self, name: str):
        return self.tabs.get(name, (None, None))[0]

    def remove_tab(self, name: str) -> None:
        widget, index = self.tabs.pop(name, (None, None))
        if widget is not None and index is not None:
            self.tab_widget.removeTab(index)
            widget.deleteLater()
