# squadron_tab.py

from __future__ import annotations

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import pyqtSignal


class SquadronTab(QWidget):
    """
    Aba de Esquadrão.
    Aceita:
      - lista de membros: [{name, rank, victories, missions_flown, status}, ...]
      - OU dicionário-resumo: {"name","aircraft","total_missions","total_kills"}
      - OU None/[] (vazio)
    """
    member_selected = pyqtSignal(dict)  # emite quando um membro é selecionado

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.squadron_data = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Nome", "Patente", "Abates", "Missões Voadas", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

        layout.addWidget(self.table)

    def update_data(self, squadron) -> None:
        """
        Atualiza a tabela com a estrutura recebida.
        """
        # Se vier um dicionário-resumo, transforme em uma linha "resumo"
        if isinstance(squadron, dict):
            summary = squadron
            squadron = [{
                "name": summary.get("name", "Esquadrão"),
                "rank": "-",  # não disponível no resumo
                "victories": summary.get("total_kills", 0),
                "missions_flown": summary.get("total_missions", 0),
                "status": summary.get("aircraft", "N/A"),
            }]
        elif not isinstance(squadron, list):
            squadron = []

        # Mantenha apenas itens dicionário
        self.squadron_data = [m for m in (squadron or []) if isinstance(m, dict)]
        self.table.setRowCount(len(self.squadron_data))

        for row, member in enumerate(self.squadron_data):
            self.table.setItem(row, 0, QTableWidgetItem(str(member.get("name", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(str(member.get("rank", ""))))
            self.table.setItem(row, 2, QTableWidgetItem(str(member.get("victories", 0))))
            self.table.setItem(row, 3, QTableWidgetItem(str(member.get("missions_flown", 0))))
            self.table.setItem(row, 4, QTableWidgetItem(str(member.get("status", ""))))

    def _on_selection_changed(self) -> None:
        items = self.table.selectedItems()
        if not items:
            return
        row = items[0].row()
        if 0 <= row < len(self.squadron_data):
            member_data = self.squadron_data[row]
            self.member_selected.emit(member_data)
