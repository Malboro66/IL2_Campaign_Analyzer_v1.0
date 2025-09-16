# app/core/signals.py
from PyQt5.QtCore import QObject, pyqtSignal

class AppSignals(QObject):
    """
    EventBus central para toda a aplicação.
    Qualquer parte da UI pode emitir ou ouvir esses sinais.
    """
    mission_selected = pyqtSignal(dict)
    squadron_member_selected = pyqtSignal(dict)
    ace_selected = pyqtSignal(dict)
    data_loaded = pyqtSignal(dict)

# Instância global que será usada pela aplicação
signals = AppSignals()
