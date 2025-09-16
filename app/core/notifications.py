# app/core/notifications.py
from PyQt5.QtWidgets import QMessageBox, QSystemTrayIcon, QStyle
from PyQt5.QtCore import QObject, pyqtSignal


class NotificationCenter(QObject):
    # Sinal global para notificação (texto + nível)
    notify = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tray = None

    def setup_tray(self, app):
        """Cria ícone na bandeja do sistema para notificações"""
        self.tray = QSystemTrayIcon(app.style().standardIcon(QStyle.SP_ComputerIcon))
        self.tray.setToolTip("IL-2 Campaign Analyzer")
        self.tray.show()

    def send(self, message, level="info"):
        """Dispara notificação"""
        self.notify.emit(message, level)
        if self.tray:
            icon = QSystemTrayIcon.Information
            if level == "warning":
                icon = QSystemTrayIcon.Warning
            elif level == "error":
                icon = QSystemTrayIcon.Critical
            self.tray.showMessage("IL-2 Campaign Analyzer", message, icon, 5000)


# Instância global
notification_center = NotificationCenter()
