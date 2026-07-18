"""
Lead Management widget — Darklightz Lead Generator v2.0

Redesigned as a two-level CRM view:

  Level 1 — Collections list
      Each search session is shown as a card:
        🔍 Keyword  in  City
        Date · Time · Status · Lead count
        [Open Collection] button

  Level 2 — Leads table for a selected collection
        Back button → returns to level 1
        All 15 columns, sortable, searchable, filterable
        Right-click for actions (status, notes, maps, WhatsApp, delete)
"""

from __future__ import annotations

import webbrowser
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMenu, QMessageBox,
    QDialog, QTextEdit, QDialogButtonBox,
    QLineEdit, QSizePolicy, QAbstractItemView,
    QScrollArea, QFrame, QStackedWidget,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QColor, QFont, QBrush

from database import operations as db
from frontend.styles import STATUS_COLOURS, LEAD_TYPE_COLOURS
from utilities.logger import logger


# ---------------------------------------------------------------------------
# Lead table column spec
# ---------------------------------------------------------------------------
COLUMNS: list[tuple[str, str, int]] = [
    ("Business Name",  "name",          200),
    ("Category",       "category",      130),
    ("Phone",          "phone",         130),
    ("Mobile",         "mobile",        130),
    ("WhatsApp",       "whatsapp",      210),
    ("Email",          "email",         190),
    ("Instagram",      "instagram",     190),
    ("Facebook",       "facebook",      190),
    ("Website",        "website",       190),
    ("Address",        "address",       230),
    ("Google Maps",    "maps_link",     210),
    ("Rating",         "rating",         60),
    ("Reviews",        "reviews",        70),
    ("Status",         "status",        110),
    ("Notes",          "notes",         200),
]

STATUS_OPTIONS = [
    "New", "Contacted", "Follow-up", "Interested", "Closed", "Not Interested"
]


# ---------------------------------------------------------------------------
# Notes editor dialog
# ---------------------------------------------------------------------------

class _NotesDialog(QDialog):
    def __init__(self, current_notes: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Notes")
        self.setMinimumSize(500, 280)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Notes:"))
        self._editor = QTextEdit()
        self._editor.setPlainText(current_notes)
        layout.addWidget(self._editor)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_notes(self) -> str:
        return self._editor.toPlainText().strip()


# ---------------------------------------------------------------------------
# Single collection card
# ---------------------------------------------------------------------------

class _CollectionCard(QFrame):
    def __init__(self, session: dict, on_open, parent=None):
        super().__init__(parent)
        self.setObjectName("StatCard")
        self._session = session

        row = QHBoxLayout(self)
        row.setContentsMargins(20, 14, 20, 14)
        row.setSpacing(20)

        # Left: icon + info
        info = QVBoxLayout()
        info.setSpacing(4)

        keyword  = session.get("keyword", "—")
        city     = session.get("city", "—")
        status   = session.get("status", "")
        count    = session.get("lead_count", 0)
        raw_date = session.get("created_at", "")

        # Parse and format date/time
        try:
            dt = datetime.strptime(raw_date[:19], "%Y-%m-%d %H:%M:%S")
            date_str = dt.strftime("%d %b %Y")
            time_str = dt.strftime("%I:%M %p")
        except Exception:
            date_str = raw_date[:10]
            time_str = ""

        title_lbl = QLabel(f"🔍  {keyword}   —   {city}")
        title_lbl.setStyleSheet(
            "color: #cdd6f4; font-size: 14px; font-weight: bold;"
        )

        status_colour = "#a6e3a1" if status == "complete" else "#fab387"
        status_icon   = "✅" if status == "complete" else "⏸"

        meta_lbl = QLabel(
            f"{date_str}  ·  {time_str}  ·  "
            f"<span style='color:{status_colour}'>{status_icon} {status.capitalize()}</span>  ·  "
            f"<b style='color:#cba6f7'>{count} lead{'s' if count != 1 else ''}</b>"
        )
        meta_lbl.setTextFormat(Qt.TextFormat.RichText)
        meta_lbl.setStyleSheet("color: #a6adc8; font-size: 12px;")

        info.addWidget(title_lbl)
        info.addWidget(meta_lbl)

        row.addLayout(info, 1)

        # Right: open button
        open_btn = QPushButton("Open Collection  →")
        open_btn.setFixedWidth(160)
        open_btn.clicked.connect(lambda: on_open(session))
        row.addWidget(open_btn)


# ---------------------------------------------------------------------------
# Collections list page (Level 1)
# ---------------------------------------------------------------------------

class _CollectionsPage(QWidget):
    def __init__(self, on_open_session, parent=None):
        super().__init__(parent)
        self._on_open = on_open_session
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(8)

        title = QLabel("Lead Collections")
        title.setObjectName("PageTitle")
        subtitle = QLabel(
            "Each search session is a Lead Collection. "
            "Click 'Open Collection' to view, manage, and export its leads."
        )
        subtitle.setObjectName("PageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Toolbar
        toolbar = QHBoxLayout()
        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet("color: #6c7086; font-size: 12px;")
        refresh_btn = QPushButton("↻ Refresh")
        refresh_btn.setObjectName("SecondaryButton")
        refresh_btn.setFixedWidth(90)
        refresh_btn.clicked.connect(self.refresh)
        toolbar.addWidget(self._count_lbl)
        toolbar.addStretch()
        toolbar.addWidget(refresh_btn)
        layout.addLayout(toolbar)

        # Scroll area for cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._content = QWidget()
        self._cards_layout = QVBoxLayout(self._content)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.setSpacing(10)
        self._cards_layout.addStretch()
        scroll.setWidget(self._content)
        layout.addWidget(scroll)

    def refresh(self) -> None:
        sessions = db.get_searches_with_counts()

        # Remove all existing cards (keep the stretch at the end)
        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not sessions:
            empty = QLabel(
                "No search sessions yet.\n\n"
                "Go to Lead Search and run your first search."
            )
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: #45475a; font-size: 14px; padding: 40px;")
            self._cards_layout.insertWidget(0, empty)
            self._count_lbl.setText("0 collections")
            return

        for session in sessions:
            card = _CollectionCard(session, self._on_open)
            self._cards_layout.insertWidget(
                self._cards_layout.count() - 1, card
            )

        total = len(sessions)
        self._count_lbl.setText(
            f"{total} collection{'s' if total != 1 else ''}"
        )


# ---------------------------------------------------------------------------
# Leads table page (Level 2)
# ---------------------------------------------------------------------------

class _LeadsTablePage(QWidget):
    def __init__(self, on_back, parent=None):
        super().__init__(parent)
        self._on_back = on_back
        self._session: dict = {}
        self._all_leads: list[dict] = []
        self._filtered_leads: list[dict] = []
        self._sort_col = 0
        self._sort_asc = True

        # Debounce search
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(self._apply_filters)

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(8)

        # Header row: back button + title
        header_row = QHBoxLayout()
        back_btn = QPushButton("← Back to Collections")
        back_btn.setObjectName("SecondaryButton")
        back_btn.setFixedWidth(200)
        back_btn.clicked.connect(self._on_back)
        header_row.addWidget(back_btn)
        header_row.addStretch()

        self._export_hint = QLabel("")
        self._export_hint.setStyleSheet("color: #6c7086; font-size: 11px;")
        header_row.addWidget(self._export_hint)
        layout.addLayout(header_row)

        self._title = QLabel("")
        self._title.setObjectName("PageTitle")
        self._subtitle = QLabel("")
        self._subtitle.setObjectName("PageSubtitle")
        self._subtitle.setWordWrap(True)
        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText(
            "Search name, phone, email, address …"
        )
        self._search_input.setClearButtonEnabled(True)
        self._search_input.textChanged.connect(self._search_timer.start)
        self._search_input.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet("color: #6c7086; font-size: 12px;")

        toolbar.addWidget(self._search_input)
        toolbar.addWidget(self._count_lbl)
        layout.addLayout(toolbar)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(len(COLUMNS))
        self._table.setHorizontalHeaderLabels([c[0] for c in COLUMNS])
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        self._table.doubleClicked.connect(self._on_double_click)
        self._table.setSortingEnabled(False)

        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        hh.setStretchLastSection(False)
        for i, (_, _, width) in enumerate(COLUMNS):
            self._table.setColumnWidth(i, width)
        hh.sectionClicked.connect(self._header_clicked)

        layout.addWidget(self._table)

    # ------------------------------------------------------------------

    def load_session(self, session: dict) -> None:
        self._session = session
        keyword  = session.get("keyword", "—")
        city     = session.get("city", "—")
        count    = session.get("lead_count", 0)
        raw_date = session.get("created_at", "")
        try:
            dt = datetime.strptime(raw_date[:19], "%Y-%m-%d %H:%M:%S")
            date_str = dt.strftime("%d %b %Y  %I:%M %p")
        except Exception:
            date_str = raw_date

        self._title.setText(f"🔍  {keyword}  —  {city}")
        self._subtitle.setText(
            f"Searched on {date_str}  ·  {count} lead{'s' if count != 1 else ''}"
        )
        self._export_hint.setText(
            "To export this collection, go to the Export page."
        )
        self._search_input.clear()
        self._all_leads = db.get_leads(search_id=session["id"])
        self._apply_filters()

    def _apply_filters(self) -> None:
        query    = self._search_input.text().strip().lower()
        filtered = self._all_leads

        if query:
            search_keys = (
                "name", "phone", "mobile", "email",
                "address", "category", "notes",
            )
            filtered = [
                l for l in filtered
                if any(query in str(l.get(k, "")).lower() for k in search_keys)
            ]

        col_key = COLUMNS[self._sort_col][1]
        filtered = sorted(
            filtered,
            key=lambda x: str(x.get(col_key, "") or "").lower(),
            reverse=not self._sort_asc,
        )
        self._filtered_leads = filtered
        self._populate_table(filtered)
        n = len(filtered)
        self._count_lbl.setText(f"{n:,} lead{'s' if n != 1 else ''}")

    def _populate_table(self, leads: list[dict]) -> None:
        self._table.setUpdatesEnabled(False)
        self._table.setRowCount(0)
        self._table.setRowCount(len(leads))

        for row_idx, lead in enumerate(leads):
            for col_idx, (_, key, _) in enumerate(COLUMNS):
                value = str(lead.get(key, "") or "")
                item  = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                if col_idx == 0:
                    item.setData(Qt.ItemDataRole.UserRole, lead.get("id"))

                if key == "status":
                    colour = STATUS_COLOURS.get(value, "#a6adc8")
                    item.setForeground(QBrush(QColor(colour)))
                    f = QFont(); f.setBold(True); item.setFont(f)

                self._table.setItem(row_idx, col_idx, item)

        self._table.setUpdatesEnabled(True)

    def _header_clicked(self, col: int) -> None:
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True
        self._apply_filters()
        hh = self._table.horizontalHeader()
        hh.setSortIndicator(
            col,
            Qt.SortOrder.AscendingOrder if self._sort_asc
            else Qt.SortOrder.DescendingOrder
        )
        hh.setSortIndicatorShown(True)

    def _get_lead_from_row(self, row: int) -> tuple[int | None, dict | None]:
        item = self._table.item(row, 0)
        if not item or row >= len(self._filtered_leads):
            return None, None
        return item.data(Qt.ItemDataRole.UserRole), self._filtered_leads[row]

    def _on_double_click(self, index) -> None:
        col_key = COLUMNS[index.column()][1]
        _, lead  = self._get_lead_from_row(index.row())
        if not lead:
            return
        if col_key == "notes":
            self._open_notes_editor(index.row())
        elif col_key in ("whatsapp", "maps_link", "instagram", "facebook", "website"):
            url = lead.get(col_key, "")
            if url and url.startswith("http"):
                webbrowser.open(url)

    def _show_context_menu(self, pos) -> None:
        row = self._table.rowAt(pos.y())
        if row < 0:
            return
        lead_id, lead = self._get_lead_from_row(row)
        if lead_id is None:
            return

        menu = QMenu(self)

        # Status submenu
        status_menu = menu.addMenu("🔖  Set Status")
        for s in STATUS_OPTIONS:
            act = QAction(s, self)
            act.triggered.connect(
                lambda checked, _s=s, _id=lead_id: self._set_status(_id, _s)
            )
            status_menu.addAction(act)

        menu.addSeparator()

        notes_act = QAction("✏  Edit Notes", self)
        notes_act.triggered.connect(lambda: self._open_notes_editor(row))
        menu.addAction(notes_act)

        menu.addSeparator()

        maps_link = lead.get("maps_link", "")
        if maps_link:
            act = QAction("🗺  Open in Google Maps", self)
            act.triggered.connect(lambda: webbrowser.open(maps_link))
            menu.addAction(act)

            act2 = QAction("📋  Copy Google Maps Link", self)
            act2.triggered.connect(lambda: self._copy(maps_link))
            menu.addAction(act2)

        wa = lead.get("whatsapp", "")
        if wa:
            act = QAction("💬  Open WhatsApp", self)
            act.triggered.connect(lambda: webbrowser.open(wa))
            menu.addAction(act)

        website = lead.get("website", "")
        if website:
            act = QAction("🌐  Open Website", self)
            act.triggered.connect(lambda: webbrowser.open(website))
            menu.addAction(act)

        menu.addSeparator()

        del_act = QAction("🗑  Delete Lead", self)
        del_act.triggered.connect(lambda: self._delete_lead(lead_id))
        menu.addAction(del_act)

        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _set_status(self, lead_id: int, status: str) -> None:
        db.update_lead_status(lead_id, status)
        # Update in-memory list too
        for lead in self._all_leads:
            if lead.get("id") == lead_id:
                lead["status"] = status
        self._apply_filters()

    def _open_notes_editor(self, row: int) -> None:
        lead_id, lead = self._get_lead_from_row(row)
        if lead_id is None:
            return
        dlg = _NotesDialog(lead.get("notes", ""), parent=self)
        if dlg.exec():
            new_notes = dlg.get_notes()
            db.update_lead_notes(lead_id, new_notes)
            for l in self._all_leads:
                if l.get("id") == lead_id:
                    l["notes"] = new_notes
            self._apply_filters()

    def _delete_lead(self, lead_id: int) -> None:
        reply = QMessageBox.question(
            self, "Delete Lead", "Permanently delete this lead?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_lead(lead_id)
            self._all_leads = [l for l in self._all_leads if l.get("id") != lead_id]
            self._apply_filters()

    @staticmethod
    def _copy(text: str) -> None:
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(text)


# ---------------------------------------------------------------------------
# Main widget (two-level stacked view)
# ---------------------------------------------------------------------------

class LeadsWidget(QWidget):
    """Collections list → leads table drill-down."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._stack = QStackedWidget()

        self._collections_page = _CollectionsPage(
            on_open_session=self._open_session
        )
        self._leads_page = _LeadsTablePage(
            on_back=self._go_back
        )

        self._stack.addWidget(self._collections_page)  # index 0
        self._stack.addWidget(self._leads_page)         # index 1

        layout.addWidget(self._stack)

    def _open_session(self, session: dict) -> None:
        self._leads_page.load_session(session)
        self._stack.setCurrentIndex(1)

    def _go_back(self) -> None:
        self._collections_page.refresh()
        self._stack.setCurrentIndex(0)

    def refresh(self) -> None:
        """Called by main_window when navigating to this tab."""
        self._collections_page.refresh()
        self._stack.setCurrentIndex(0)
