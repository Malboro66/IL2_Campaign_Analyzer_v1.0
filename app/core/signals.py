"""
Defines global signals for the application.

This module creates a single, globally accessible instance of AppSignals
to act as a central event bus. This allows different parts of the
application to communicate with each other without being directly coupled.
"""
from PyQt5.QtCore import QObject, pyqtSignal

class AppSignals(QObject):
    """
    A central event bus for the entire application.

    Any part of the UI can emit or connect to these signals to handle
    application-wide events.

    Signals:
        mission_selected (pyqtSignal): Emitted when a mission is selected.
                                       Carries a dictionary of mission data.
        squadron_member_selected (pyqtSignal): Emitted when a squadron member
                                               is selected. Carries a dict
                                               of member data.
        ace_selected (pyqtSignal): Emitted when a campaign ace is selected.
                                   Carries a dictionary of ace data.
        data_loaded (pyqtSignal): Emitted when the main campaign data has
                                  been successfully loaded and processed.
                                  Carries the complete data dictionary.
    """
    mission_selected = pyqtSignal(dict)
    squadron_member_selected = pyqtSignal(dict)
    ace_selected = pyqtSignal(dict)
    data_loaded = pyqtSignal(dict)

# Global instance to be used throughout the application
signals = AppSignals()
