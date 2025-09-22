# app/ui/profile_tab.py

from __future__ import annotations

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFormLayout, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt


class ProfileTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = {}
        self._setup_ui()

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)

        # Header (hero)
        self.header = QGroupBox("Perfil do Piloto")
        h = QHBoxLayout()
        self.lbl_avatar = QLabel("[Avatar]")
        self.lbl_avatar.setFixedSize(96, 96)
        self.lbl_avatar.setAlignment(Qt.AlignCenter)
        self.lbl_title = QLabel("Nome • Patente • Nação")
        self.btn_edit = QPushButton("Editar perfil")
        h.addWidget(self.lbl_avatar)
        h.addWidget(self.lbl_title, 1)
        h.addWidget(self.btn_edit)
        self.header.setLayout(h)
        self.layout.addWidget(self.header)

        # Bio
        self.bio = QGroupBox("Biografia")
        fbio = QFormLayout()
        self.bio_name = QLabel("-")
        self.bio_birth = QLabel("-")
        self.bio_place = QLabel("-")
        self.bio_summary = QLabel("-")
        fbio.addRow("Nome:", self.bio_name)
        fbio.addRow("Nascimento:", self.bio_birth)
        fbio.addRow("Local:", self.bio_place)
        fbio.addRow("Resumo:", self.bio_summary)
        self.bio.setLayout(fbio)
        self.layout.addWidget(self.bio)

        # Carreira
        self.career = QGroupBox("Carreira")
        fcar = QFormLayout()
        self.career_unit = QLabel("-")
        self.career_path = QListWidget()
        fcar.addRow("Esquadrão atual:", self.career_unit)
        fcar.addRow("Histórico de unidades:", self.career_path)
        self.career.setLayout(fcar)
        self.layout.addWidget(self.career)

        # Estatísticas
        self.stats = QGroupBox("Estatísticas")
        fstats = QFormLayout()
        self.stat_missions = QLabel("0")
        self.stat_hours = QLabel("0.0")
        self.stat_kills = QLabel("0")
        self.stat_awards = QLabel("0")
        fstats.addRow("Missões:", self.stat_missions)
        fstats.addRow("Horas de voo:", self.stat_hours)
        fstats.addRow("Vitórias:", self.stat_kills)
        fstats.addRow("Medalhas:", self.stat_awards)
        self.stats.setLayout(fstats)
        self.layout.addWidget(self.stats)

        # Favoritos
        self.favs = QGroupBox("Favoritos")
        ff = QFormLayout()
        self.fav_aircraft = QLabel("-")
        ff.addRow("Aeronaves:", self.fav_aircraft)
        self.favs.setLayout(ff)
        self.layout.addWidget(self.favs)

        self.layout.addStretch(1)

    def update_data(self, data: dict):
        """
        Espera chave 'pilotProfile' (ou 'pilot_profile') com estrutura:
        - core: name, rank, nation, squadronCurrent, avatarUrl
        - bio: birthDate, birthPlace, summary, favorites.aircraft[]
        - career: units[], stats{ missions, hours, victories, awards[] }
        """
        self.data = data or {}
        prof = (self.data.get("pilotProfile")
                or self.data.get("pilot_profile")
                or {})

        core = prof.get("core") or {}
        name = core.get("name", "-")
        rank = core.get("rank", "-")
        nation = core.get("nation", "-")
        self.lbl_title.setText(f"{name} • {rank} • {nation}")
        self.career_unit.setText(core.get("squadronCurrent", "-"))

        bio = prof.get("bio") or {}
        self.bio_name.setText(name or "-")
        self.bio_birth.setText(bio.get("birthDate") or "-")
        self.bio_place.setText(bio.get("birthPlace") or "-")
        self.bio_summary.setText(bio.get("summary") or "-")
        favs = ((bio.get("favorites") or {}).get("aircraft")) or []
        self.fav_aircraft.setText(", ".join(favs) if favs else "-")

        car = prof.get("career") or {}
        stats = car.get("stats") or {}
        self.stat_missions.setText(str(stats.get("missions", 0)))
        self.stat_hours.setText(str(stats.get("hours", 0.0)))
        self.stat_kills.setText(str(stats.get("victories", 0)))
        self.stat_awards.setText(str(len(stats.get("awards", []))))

        self.career_path.clear()
        for u in car.get("units", []):
            item = QListWidgetItem(f"{u.get('name','?')} ({u.get('from','?')} → {u.get('to','?') or 'presente'})")
            self.career_path.addItem(item)
