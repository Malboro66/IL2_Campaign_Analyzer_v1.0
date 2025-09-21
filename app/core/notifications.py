from __future__ import annotations
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QSystemTrayIcon, QStyle, QApplication

class NotificationCenter(QObject):
    notify = pyqtSignal(str, str)
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.tray: QSystemTrayIcon | None = None
    def setup_tray(self, app: QApplication) -> None:
        try:
            icon = app.style().standardIcon(QStyle.SP_ComputerIcon)
            self.tray = QSystemTrayIcon(icon)
            self.tray.setToolTip("IL-2 Campaign Analyzer")
            self.tray.show()
        except Exception:
            self.tray = None
    def send(self, message: str, level: str = "info") -> None:
        self.notify.emit(message, level)
        if not self.tray: return
        icon = QSystemTrayIcon.Information
        if level == "warning": icon = QSystemTrayIcon.Warning
        elif level in ("error", "critical"): icon = QSystemTrayIcon.Critical
        try:
            self.tray.showMessage("IL-2 Campaign Analyzer", message, icon, 5000)
        except Exception:
            pass

notification_center = NotificationCenter()
