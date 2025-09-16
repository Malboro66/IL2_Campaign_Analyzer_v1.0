# app/ui/notifications_tab.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QLabel
from PyQt5.QtCore import Qt
from app.core.notifications import notification_center


class NotificationsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

        # Conecta sinal do centro de notificações
        notification_center.notify.connect(self._add_notification)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.list = QListWidget()
        layout.addWidget(QLabel("Histórico de Notificações"))
        layout.addWidget(self.list)

    def _add_notification(self, message, level):
        self.list.addItem(f"[{level.upper()}] {message}")
