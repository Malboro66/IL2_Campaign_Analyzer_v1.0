from __future__ import annotations
from PyQt5.QtWidgets import QWidget

class BaseTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
    def update_data(self, data: dict) -> None:
        raise NotImplementedError("Subclasses devem implementar o método update_data")
