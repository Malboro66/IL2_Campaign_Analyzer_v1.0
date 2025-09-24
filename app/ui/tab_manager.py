"""
Provides a manager for handling tabs in a QTabWidget.
"""
from __future__ import annotations
from typing import Type
from PyQt5.QtWidgets import QTabWidget, QWidget

class TabManager:
    """
    A helper class to manage the creation, registration, and removal of tabs.
    """
    def __init__(self, tab_widget: QTabWidget) -> None:
        """
        Initialize the TabManager.

        Args:
            tab_widget (QTabWidget): The QTabWidget instance to manage.
        """
        self.tab_widget = tab_widget
        self.tabs: dict[str, tuple[QWidget, int]] = {}

    def register_tab(self, name: str, widget_class: Type[QWidget], *args, **kwargs) -> QWidget:
        """
        Create, register, and add a new tab to the tab widget.

        Args:
            name (str): The name of the tab to display.
            widget_class (Type[QWidget]): The class of the widget for the tab's content.
            *args: Positional arguments to pass to the widget's constructor.
            **kwargs: Keyword arguments to pass to the widget's constructor.

        Returns:
            QWidget: The newly created widget instance.

        Raises:
            ValueError: If a tab with the same name is already registered.
        """
        if name in self.tabs:
            raise ValueError(f"Aba '{name}' já registrada")
        widget = widget_class(*args, **kwargs)
        index = self.tab_widget.addTab(widget, name)
        self.tabs[name] = (widget, index)
        return widget

    def get_tab(self, name: str) -> QWidget | None:
        """
        Retrieve a registered tab widget by its name.

        Args:
            name (str): The name of the tab.

        Returns:
            QWidget | None: The widget instance, or None if not found.
        """
        return self.tabs.get(name, (None, None))[0]

    def remove_tab(self, name: str) -> None:
        """
        Remove a tab from the tab widget and unregister it.

        Args:
            name (str): The name of the tab to remove.
        """
        widget, index = self.tabs.pop(name, (None, None))
        if widget is not None and index is not None:
            self.tab_widget.removeTab(index)
            widget.deleteLater()
