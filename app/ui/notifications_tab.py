"""
Defines the UI tab for viewing and filtering campaign notifications.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QDateEdit, QPushButton, QCheckBox, QLineEdit, QComboBox, QGroupBox, QGridLayout
)
from PyQt5.QtCore import QDate


class NotificationsTab(QWidget):
    """
    A widget for viewing and filtering campaign log notifications.

    This tab provides a comprehensive set of controls to filter notifications
    by date, source, category, and keywords, displaying the results in a
    text area.
    """
    def __init__(self, parent=None):
        """
        Initialize the NotificationsTab.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self._idx = {}           # Full notifications_index
        self._by_date = {}       # Dict "DD/MM/YYYY" -> {"squadron":[...], "other":[...]}
        self._side = "ENTENTE"   # Current campaign side (from processor)
        self._setup_ui()

    def _setup_ui(self):
        """
        Set up the user interface for the tab.
        """
        layout = QVBoxLayout(self)

        # Top row: date period and shortcuts
        period_row = QHBoxLayout()
        period_row.addWidget(QLabel("De:"))

        self.date_from = QDateEdit(calendarPopup=True)
        self.date_from.setDisplayFormat("dd/MM/yyyy")
        period_row.addWidget(self.date_from)

        period_row.addWidget(QLabel("Até:"))
        self.date_to = QDateEdit(calendarPopup=True)
        self.date_to.setDisplayFormat("dd/MM/yyyy")
        period_row.addWidget(self.date_to)

        self.quick_range = QComboBox()
        self.quick_range.addItems([
            "Tudo", "Últimos 7 dias", "Últimos 30 dias", "Este mês", "Este ano"
        ])
        self.quick_range.currentIndexChanged.connect(self._apply_quick_range)
        period_row.addWidget(self.quick_range)

        layout.addLayout(period_row)

        # Origin filter row (squadron vs. other)
        origin_row = QHBoxLayout()
        origin_row.addWidget(QLabel("Origem:"))
        self.chk_squad = QCheckBox("Esquadrão")
        self.chk_squad.setChecked(True)
        origin_row.addWidget(self.chk_squad)
        self.chk_other_origin = QCheckBox("Outras (origem)")
        self.chk_other_origin.setChecked(True)
        origin_row.addWidget(self.chk_other_origin)
        origin_row.addStretch(1)
        layout.addLayout(origin_row)

        # Category filter group
        cat_group = QGroupBox("Categorias")
        gl = QGridLayout()
        self.chk_cat_promotions   = QCheckBox("Promoções")
        self.chk_cat_awards       = QCheckBox("Condecorações")
        self.chk_cat_casualties   = QCheckBox("Baixas")
        self.chk_cat_kills        = QCheckBox("Vitórias")
        self.chk_cat_others       = QCheckBox("Outras (sem categoria)")

        for i, w in enumerate([
            self.chk_cat_promotions, self.chk_cat_awards, self.chk_cat_casualties,
            self.chk_cat_kills, self.chk_cat_others
        ]):
            w.setChecked(True)
            gl.addWidget(w, i // 3, i % 3)

        cat_group.setLayout(gl)
        layout.addWidget(cat_group)

        # Keyword filter row
        text_row = QHBoxLayout()
        text_row.addWidget(QLabel("Incluir palavras:"))
        self.txt_include = QLineEdit()
        self.txt_include.setPlaceholderText("separe por vírgulas (ex.: promotion, award)")
        text_row.addWidget(self.txt_include)

        text_row.addWidget(QLabel("Excluir palavras:"))
        self.txt_exclude = QLineEdit()
        self.txt_exclude.setPlaceholderText("separe por vírgulas (ex.: transfer)")
        text_row.addWidget(self.txt_exclude)

        layout.addLayout(text_row)

        ppl_row = QHBoxLayout()
        ppl_row.addWidget(QLabel("Filtrar por piloto/unidade:"))
        self.txt_actor = QLineEdit()
        self.txt_actor.setPlaceholderText("nome do piloto/unidade citado")
        ppl_row.addWidget(self.txt_actor)
        ppl_row.addStretch(1)
        layout.addLayout(ppl_row)

        # Action buttons
        buttons = QHBoxLayout()
        self.apply_btn = QPushButton("Aplicar filtro")
        self.apply_btn.clicked.connect(self._render)
        buttons.addWidget(self.apply_btn)

        self.clear_btn = QPushButton("Limpar")
        self.clear_btn.clicked.connect(self._clear_filter)
        buttons.addWidget(self.clear_btn)

        buttons.addStretch(1)
        layout.addLayout(buttons)

        # Results text area
        self.title_label = QLabel("Notificações")
        self.title_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.title_label)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(self.text)

    # ---------- Datas ----------
    @staticmethod
    def _qdate_from_ddmmyyyy(s: str) -> QDate:
        """Convert a DD/MM/YYYY string to a QDate object."""
        try:
            d = datetime.strptime(s, "%d/%m/%Y")
            return QDate(d.year, d.month, d.day)
        except Exception:
            return QDate()

    def _compute_min_max_dates(self) -> tuple[QDate, QDate]:
        """
        Compute the minimum and maximum dates from the available notifications.
        """
        if not self._by_date:
            return QDate(), QDate()
        dates = [self._qdate_from_ddmmyyyy(k) for k in self._by_date.keys()]
        dates = [d for d in dates if d.isValid()]
        if not dates:
            return QDate(), QDate()
        return min(dates), max(dates)

    def _apply_quick_range(self):
        """
        Set the date range filters based on a predefined selection (e.g., "Last 7 days").
        """
        if not self._by_date:
            return
        min_d, max_d = self._compute_min_max_dates()
        if not (min_d.isValid() and max_d.isValid()):
            return

        label = self.quick_range.currentText()
        if label == "Tudo":
            self.date_from.setDate(min_d)
            self.date_to.setDate(max_d)
        else:
            dt_min = datetime(min_d.year(), min_d.month(), min_d.day())
            dt_max = datetime(max_d.year(), max_d.month(), max_d.day())
            ref = dt_max
            if label == "Últimos 7 dias":
                start = ref - timedelta(days=6)
            elif label == "Últimos 30 dias":
                start = ref - timedelta(days=29)
            elif label == "Este mês":
                start = ref.replace(day=1)
            elif label == "Este ano":
                start = ref.replace(month=1, day=1)
            else:
                start = dt_min

            start_q = QDate(start.year, start.month, start.day)
            ref_q = QDate(ref.year, ref.month, ref.day)
            if start_q < min_d:
                start_q = min_d
            if ref_q > max_d:
                ref_q = max_d
            self.date_from.setDate(start_q)
            self.date_to.setDate(ref_q)

    def _clear_filter(self):
        """
        Reset all filter controls to their default state and re-render.
        """
        min_d, max_d = self._compute_min_max_dates()
        if min_d.isValid():
            self.date_from.setDate(min_d)
        if max_d.isValid():
            self.date_to.setDate(max_d)
        # Reset controls
        self.chk_squad.setChecked(True)
        self.chk_other_origin.setChecked(True)
        for w in [
            self.chk_cat_promotions, self.chk_cat_awards, self.chk_cat_casualties,
            self.chk_cat_kills, self.chk_cat_others
        ]:
            w.setChecked(True)
        self.txt_include.clear()
        self.txt_exclude.clear()
        self.txt_actor.clear()
        self.quick_range.setCurrentIndex(0)
        self._render()

    # ---------- Categorias ----------
    def _categorize(self, text: str) -> set[str]:
        """
        Assign a set of heuristic categories to a notification based on its text.

        Args:
            text (str): The notification text.

        Returns:
            set[str]: A set of category names (e.g., {'promotions', 'awards'}).
                      Returns {'others'} if no specific category is matched.
        """
        t = text.lower()

        cats = set()
        # promotions
        if re.search(r"\b(promoted|promotion|promo(ç|c)[aã]o|promovido)\b", t):
            cats.add("promotions")
        # awards
        if re.search(r"\b(award(ed)?|awarded|medal|decorat|condecor|croix|pour le merite|blue max)\b", t):
            cats.add("awards")
        # casualties
        if re.search(r"\b(kia|mia|wounded|killed|ferid|morto|desaparecido|pow|prisoner|capturad|taken prisoner)\b", t):
            cats.add("casualties")
        # victories
        if any([
            re.search(r"\b(victor(y|ies)|kill(s)?|abate(u|u)?|vit[oó]ri[ao]s?\b)", t),
            re.search(r"\b(shot down|downed|brought down)\b", t),
            re.search(r"\b(confirmed (victor(y|ies)|kill)|victor(y|ies) confirmed)\b", t),
            re.search(r"\b(claim(ed)?|credited with)\b.*\b(victor(y|ies)|kill|aircraft|balloon)\b", t),
            re.search(r"\b(destroy(ed)?|destroy(s)?)\b.*\b(aircraft|plane|a/c|balloon)\b", t),
        ]):
            cats.add("kills")

        if not cats:
            cats.add("others")

        return cats

    def _selected_categories(self) -> set[str]:
        """
        Get the set of categories currently selected by the user.
        """
        selected = set()
        if self.chk_cat_promotions.isChecked(): selected.add("promotions")
        if self.chk_cat_awards.isChecked():     selected.add("awards")
        if self.chk_cat_casualties.isChecked(): selected.add("casualties")
        if self.chk_cat_kills.isChecked():      selected.add("kills")
        if self.chk_cat_others.isChecked():     selected.add("others")
        return selected

    # ---------- Filtro principal ----------
    def _passes_filters(self, date_str: str, text: str, is_squadron: bool) -> bool:
        """
        Check if a single notification passes all currently active filters.

        Args:
            date_str (str): The date of the notification ('DD/MM/YYYY').
            text (str): The notification text.
            is_squadron (bool): True if the notification is from the player's squadron.

        Returns:
            bool: True if the notification should be displayed, False otherwise.
        """
        # Date
        qd = QDate.fromString(date_str, "dd/MM/yyyy")
        if qd.isValid():
            if qd < self.date_from.date() or qd > self.date_to.date():
                return False

        # Origin
        if is_squadron and not self.chk_squad.isChecked():
            return False
        if (not is_squadron) and not self.chk_other_origin.isChecked():
            return False

        # Categories
        cats = self._categorize(text)
        selected = self._selected_categories()
        if selected and cats.isdisjoint(selected):
            return False

        # Keywords
        inc = [w.strip().lower() for w in self.txt_include.text().split(",") if w.strip()]
        exc = [w.strip().lower() for w in self.txt_exclude.text().split(",") if w.strip()]
        low = text.lower()

        if inc and not any(w in low for w in inc):
            return False
        if exc and any(w in low for w in exc):
            return False

        # Actor (pilot/unit)
        actor = self.txt_actor.text().strip().lower()
        if actor and actor not in low:
            return False

        return True

    # ---------- API ----------
    def update_data(self, data: dict):
        """
        Update the tab with new notification data from the main data structure.

        Args:
            data (dict): The complete processed campaign data dictionary.
        """
        self._idx = (data or {}).get("notifications_index") or {}
        self._side = self._idx.get("side") or "ENTENTE"
        self._by_date = self._idx.get("by_date") or {}

        # Set date range controls
        min_d, max_d = self._compute_min_max_dates()
        if min_d.isValid() and max_d.isValid():
            self.date_from.setMinimumDate(min_d)
            self.date_from.setMaximumDate(max_d)
            self.date_to.setMinimumDate(min_d)
            self.date_to.setMaximumDate(max_d)
            self.date_from.setDate(min_d)
            self.date_to.setDate(max_d)
            self.quick_range.setCurrentIndex(0)

        self._render()

    def _render(self):
        """
        Render the filtered notifications into the main text area.
        """
        self.text.clear()

        lines = ["Notificações"]

        if not self._by_date:
            lines.append("\nSem notificações disponíveis.")
            self.text.setText("\n".join(lines))
            return

        any_output = False
        for date_str in sorted(self._by_date.keys(), key=lambda s: datetime.strptime(s, "%d/%m/%Y")):
            groups = self._by_date.get(date_str) or {}
            squad = groups.get("squadron") or []
            other = groups.get("other") or []

            squad_f = [t for t in squad if self._passes_filters(date_str, t, True)]
            other_f = [t for t in other if self._passes_filters(date_str, t, False)]

            if not squad_f and not other_f:
                continue

            any_output = True
            lines.append(f"\n{date_str}")
            if squad_f and self.chk_squad.isChecked():
                lines.append("  Notificações do Esquadrão:")
                for t in squad_f:
                    lines.append(f"    - {t}")
            if other_f and self.chk_other_origin.isChecked():
                lines.append("  Outras Notificações:")
                for t in other_f:
                    lines.append(f"    - {t}")

        if not any_output:
            lines.append("\nSem notificações no período/critério selecionado.")

        self.text.setText("\n".join(lines))
