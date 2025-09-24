"""
Defines the base class for all tabs in the application.
"""
from __future__ import annotations
from PyQt5.QtWidgets import QWidget

class BaseTab(QWidget):
    """
    An abstract base class for all tabs in the main application window.

    This class provides a common interface for all tabs, ensuring they
    have an `update_data` method that can be called when new campaign
    data is loaded.
    """
    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the base tab.

        Args:
            parent (QWidget | None, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
    def update_data(self, data: dict) -> None:
        """
        Update the tab's display with new data.

        This method must be implemented by all subclasses.

        Args:
            data (dict): The new data to display.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError("Subclasses devem implementar o método update_data")
