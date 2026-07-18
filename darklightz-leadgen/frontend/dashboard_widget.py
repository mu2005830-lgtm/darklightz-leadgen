"""
Dashboard widget — Darklightz Lead Generator v2.0.

v2.0: added follow-up, no_website, social_only stat cards.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QScrollArea, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from database.operations import get_dashboard_stats


# ---------------------------------------------------------------------------
# Stat card
# ---------------------------------------------------------------------------

class StatCard(QFrame):
    def __init__(self, label: str, value: str, accent_colour: str = "#cba6f7"):
        super().__init__()
        self.setObjectName("StatCard")
        self._accent = accent_colour

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(4)

        self._value_lbl = QLabel(value)
        self._value_lbl.setObjectName("StatValue")
        self._value_lbl.setStyleSheet(f"color: {accent_colour};")

        self._label_lbl = QLabel(label)
        self._label_lbl.setObjectName("StatLabel")

        layout.addWidget(self._value_lbl)
        layout.addWidget(self._label_lbl)

    def update_value(self, value: str) -> None:
        self._value_lbl.setText(value)


# ---------------------------------------------------------------------------
# Dashboard widget
# ---------------------------------------------------------------------------

class DashboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards: dict[str, StatCard] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(0)

        title = QLabel("Dashboard")
        title.setObjectName("PageTitle")
        subtitle = QLabel(
            "Real-time overview of your lead collection and search history."
        )
        subtitle.setObjectName("PageSubtitle")
        subtitle.setWordWrap(True)
        outer.addWidget(title)
        outer.addWidget(subtitle)
        outer.addSpacing(16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        vbox    = QVBoxLayout(content)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(16)
        scroll.setWidget(content)

        # ---- Section: Lead overview ---------------------------------
        font = QFont()
        font.setPointSize(13)
        font.setBold(True)

        overview_lbl = QLabel("Lead Overview")
        overview_lbl.setObjectName("PageTitle")
        overview_lbl.setFont(font)
        vbox.addWidget(overview_lbl)

        overview_metrics = [
            ("total_leads",    "Total Leads",       "#cba6f7"),
            ("total_searches", "Total Searches",     "#89b4fa"),
            ("no_website",     "No Website",         "#f38ba8"),
            ("social_only",    "Social Only",        "#fab387"),
        ]
        overview_grid = QGridLayout()
        overview_grid.setSpacing(12)
        for col, (key, label, colour) in enumerate(overview_metrics):
            card = StatCard(label, "0", colour)
            self._cards[key] = card
            overview_grid.addWidget(card, 0, col)
        vbox.addLayout(overview_grid)

        # ---- Section: Status breakdown ------------------------------
        status_lbl = QLabel("Status Breakdown")
        status_lbl.setObjectName("PageTitle")
        status_lbl.setFont(font)
        vbox.addWidget(status_lbl)

        status_metrics = [
            ("new_leads",  "New",         "#cba6f7"),
            ("contacted",  "Contacted",   "#89b4fa"),
            ("follow_up",  "Follow-up",   "#fab387"),
            ("interested", "Interested",  "#a6e3a1"),
            ("closed",     "Closed",      "#a6adc8"),
        ]
        status_grid = QGridLayout()
        status_grid.setSpacing(12)
        for col, (key, label, colour) in enumerate(status_metrics):
            card = StatCard(label, "0", colour)
            self._cards[key] = card
            status_grid.addWidget(card, 0, col)
        vbox.addLayout(status_grid)

        # ---- Section: Recent searches --------------------------------
        recent_label = QLabel("Recent Searches")
        recent_label.setObjectName("PageTitle")
        recent_label.setFont(font)
        vbox.addWidget(recent_label)

        self._recent_frame = QVBoxLayout()
        self._recent_frame.setSpacing(6)
        vbox.addLayout(self._recent_frame)
        vbox.addStretch()

        outer.addWidget(scroll)

    # ------------------------------------------------------------------
    def refresh(self) -> None:
        stats = get_dashboard_stats()

        for key, card in self._cards.items():
            card.update_value(str(stats.get(key, 0)))

        # Rebuild recent searches list
        while self._recent_frame.count():
            item = self._recent_frame.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for s in stats.get("recent_searches", []):
            row = QFrame()
            row.setObjectName("StatCard")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(12, 8, 12, 8)

            kw = QLabel(f"🔍  {s['keyword']}  in  {s['city']}")
            kw.setStyleSheet("color: #cdd6f4; font-weight: bold;")

            status_colour = "#a6e3a1" if s.get("status") == "complete" else "#fab387"
            status_lbl = QLabel(s.get("status", ""))
            status_lbl.setStyleSheet(f"color: {status_colour}; font-size: 11px;")

            ts = QLabel(s.get("created_at", ""))
            ts.setStyleSheet("color: #6c7086; font-size: 11px;")
            ts.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )

            row_layout.addWidget(kw)
            row_layout.addWidget(status_lbl)
            row_layout.addStretch()
            row_layout.addWidget(ts)
            self._recent_frame.addWidget(row)
