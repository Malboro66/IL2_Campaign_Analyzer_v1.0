"""
Provides a centralized system for handling application notifications.

This module includes a NotificationCenter class that can emit signals for
in-app notifications and also display system tray pop-up messages.
"""
from __future__ import annotations
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QSystemTrayIcon, QStyle, QApplication

class NotificationCenter(QObject):
    """
    Manages and dispatches notifications for the application.

    This class provides a single point for sending notifications, which can
    be displayed as system tray messages and/or handled by other parts of
    the application via a PyQt signal.

    Attributes:
        notify (pyqtSignal): A signal that emits a message (str) and a
                             level (str) when a notification is sent.
    """
    notify = pyqtSignal(str, str)
    def __init__(self, parent: QObject | None = None) -> None:
        """
        Initialize the NotificationCenter.

        Args:
            parent (QObject | None, optional): The parent object. Defaults to None.
        """
        super().__init__(parent)
        self.tray: QSystemTrayIcon | None = None
    def setup_tray(self, app: QApplication) -> None:
        """
        Set up the system tray icon for displaying notifications.

        Args:
            app (QApplication): The main application instance.
        """
        try:
            icon = app.style().standardIcon(QStyle.SP_ComputerIcon)
            self.tray = QSystemTrayIcon(icon)
            self.tray.setToolTip("IL-2 Campaign Analyzer")
            self.tray.show()
        except Exception:
            self.tray = None
    def send(self, message: str, level: str = "info") -> None:
        """
        Send a notification.

        Emits the 'notify' signal and, if the tray icon is available,
        displays a system tray message.

        Args:
            message (str): The notification message content.
            level (str, optional): The notification level ('info', 'warning',
                                   'error', 'critical'). Defaults to "info".
        """
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
