from __future__ import annotations
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QLabel
from PyQt5.QtCore import Qt
try:
    from app.core.notifications import notification_center
except Exception:
    from notifications import notification_center

class NotificationsTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui(); notification_center.notify.connect(self._add_notification)
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self); layout.addWidget(QLabel("Histórico de Notificações"))
        self.list = QListWidget(); layout.addWidget(self.list)
    def _add_notification(self, message: str, level: str) -> None:
        self.list.addItem(f"[{level.upper()}] {message}")
    def update_data(self, data: dict) -> None:
        if not data: return
        for entry in data.get("logs", []) or []:
            self.list.addItem(f"[LOG {entry.get('date','')}] {entry.get('text','')}")
