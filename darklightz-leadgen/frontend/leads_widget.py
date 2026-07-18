"""
Lead Table widget — Darklightz Lead Generator v2.0.

v2.0 redesign
-------------
* All new fields shown: category, mobile, email, maps_link, latitude,
  longitude, opening_hours.
* Sortable columns (click header).
* Live search bar filters across name, phone, email, address, category.
* Status filter dropdown.
* Inline Notes editing (double-click Notes cell).
* Inline Status editing (right-click → Set Status).
* "Open in Google Maps" action button from right-click menu.
* "Copy Google Maps Link" action button from right-click menu.
* "Add to Collection" action for Lead Collections.
"""

from __future__ import annotations

import webbrowser
from typing import Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMenu, QMessageBox,
    QDialog, QTextEdit, QDialogButtonBox, QComboBox,
    QLineEdit, QSizePolicy, QAbstractItemView,
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont, QBrush

from database import operations as db
from frontend.styles import STATUS_COLOURS, LEAD_TYPE_COLOURS
from utilities.logger import logger


# ---------------------------------------------------------------------------
# Column spec: (header label, dict key, width, editable)
# ---------------------------------------------------------------------------
COLUMNS: list[tuple[str, str, int, bool]] = [
    ("Business Name",  "name",          200, False),
    ("Category",       "category",      130, False),
    ("Phone",          "phone",         130, False),
    ("Mobile",         "mobile",        130, False),
    ("WhatsApp",       "whatsapp",      210, False),
    ("Email",          "email",         190, False),
    ("Instagram",      "instagram",     190, False),
    ("Facebook",       "facebook",      190, False),
    ("Website",        "website",       190, False),
    ("Address",        "address",       230, False),
    ("Google Maps",    "maps_link",     210, False),
    ("Latitude",       "latitude",       90, False),
    ("Longitude",      "longitude",      90, False),
    ("Rating",         "rating",         60, False),
    ("Reviews",        "reviews",        70, False),
    ("Opening Hours",  "opening_hours", 210, False),
    ("Lead Type",      "lead_type",     130, False),
    ("Status",         "status",        110, False),
    ("City",           "city",          100, False),
    ("Notes",          "notes",         200, True),
    ("Date Added",     "created_at",    140, False),
]

STATUS_OPTIONS = [
    "New", "Contacted", "Follow-up", "Interested", "Closed", "Not Interested"
]


# ---------------------------------------------------------------------------
# Notes editor dialog
# ---------------------------------------------------------------------------

class NotesDialog(QDialog):
    def __init__(self, lead_id: int, current_notes: str, parent=None):
        super().__init__(parent)
        self.lead_id = lead_id
        self.setWindowTitle("Edit Notes")
        self.setMinimumSize(500, 300)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Notes:"))

        self._editor = QTextEdit()
        self._editor.setPlainText(current_notes)
        layout.addWidget(self._editor)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_notes(self) -> str:
        return self._editor.toPlainText().strip()


# ---------------------------------------------------------------------------
# Main widget
# ---------------------------------------------------------------------------

class LeadsWidget(QWidget):
    """Redesigned lead table with all v2.0 fields."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_leads: list[dict] = []
        self._filtered_leads: list[dict] = []
        self._sort_col: int = 20   # default sort: Date Added
        self._sort_asc: bool = False

        # Must be created BEFORE _build_ui() because _build_ui connects to it
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(self._apply_filters)

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(8)

        # Page header
        title = QLabel("Lead Table")
        title.setObjectName("PageTitle")
        subtitle = QLabel(
            "All collected leads. Click a column header to sort. "
            "Right-click a row for actions. Double-click Notes to edit."
        )
        subtitle.setObjectName("PageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # ---- Toolbar -----------------------------------------------------
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText(
            "Search name, phone, email, address, category …"
        )
        self._search_input.setClearButtonEnabled(True)
        self._search_input.textChanged.connect(self._search_timer.start)
        self._search_input.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        self._status_filter = QComboBox()
        self._status_filter.addItems(
            ["All Statuses", "New", "Contacted", "Follow-up",
             "Interested", "Closed", "Not Interested"]
        )
        self._status_filter.setFixedWidth(160)
        self._status_filter.currentTextChanged.connect(self._apply_filters)

        self._type_filter = QComboBox()
        self._type_filter.addItems(
            ["All Types", "No Website", "Social Only", "No Online Presence",
             "Facebook Only", "Instagram Only", "WhatsApp Only"]
        )
        self._type_filter.setFixedWidth(160)
        self._type_filter.currentTextChanged.connect(self._apply_filters)

        self._count_label = QLabel("0 leads")
        self._count_label.setStyleSheet("color: #6c7086; font-size: 12px;")

        refresh_btn = QPushButton("↻ Refresh")
        refresh_btn.setObjectName("SecondaryButton")
        refresh_btn.setFixedWidth(90)
        refresh_btn.clicked.connect(self.refresh)

        toolbar.addWidget(self._search_input)
        toolbar.addWidget(self._status_filter)
        toolbar.addWidget(self._type_filter)
        toolbar.addWidget(self._count_label)
        toolbar.addWidget(refresh_btn)

        layout.addLayout(toolbar)

        # ---- Table -------------------------------------------------------
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
        self._table.setSortingEnabled(False)  # we sort manually

        # Column widths
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        hh.setStretchLastSection(False)
        for i, (_, _, width, _) in enumerate(COLUMNS):
            self._table.setColumnWidth(i, width)
        hh.sectionClicked.connect(self._header_clicked)

        layout.addWidget(self._table)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Reload all leads from the database and re-apply filters."""
        self._all_leads = db.get_leads()
        self._apply_filters()

    def _apply_filters(self) -> None:
        query   = self._search_input.text().strip().lower()
        status  = self._status_filter.currentText()
        ltype   = self._type_filter.currentText()

        filtered = self._all_leads

        if status != "All Statuses":
            filtered = [l for l in filtered if l.get("status") == status]

        if ltype != "All Types":
            filtered = [l for l in filtered if l.get("lead_type") == ltype]

        if query:
            search_keys = ("name", "phone", "mobile", "email",
                           "address", "category", "facebook",
                           "instagram", "notes", "city")
            filtered = [
                l for l in filtered
                if any(query in str(l.get(k, "")).lower() for k in search_keys)
            ]

        # Sort
        col_key = COLUMNS[self._sort_col][1]
        filtered = sorted(
            filtered,
            key=lambda x: str(x.get(col_key, "") or "").lower(),
            reverse=not self._sort_asc,
        )

        self._filtered_leads = filtered
        self._populate_table(filtered)
        self._count_label.setText(f"{len(filtered):,} lead{'s' if len(filtered) != 1 else ''}")

    def _populate_table(self, leads: list[dict]) -> None:
        self._table.setUpdatesEnabled(False)
        self._table.setRowCount(0)
        self._table.setRowCount(len(leads))

        for row_idx, lead in enumerate(leads):
            lead_id = lead.get("id")

            for col_idx, (_, key, _, _) in enumerate(COLUMNS):
                value = str(lead.get(key, "") or "")
                item  = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                # Store lead id on first column
                if col_idx == 0:
                    item.setData(Qt.ItemDataRole.UserRole, lead_id)

                # Colour-code status column
                if key == "status":
                    colour = STATUS_COLOURS.get(value, "#a6adc8")
                    item.setForeground(QBrush(QColor(colour)))
                    font = QFont()
                    font.setBold(True)
                    item.setFont(font)

                # Colour-code lead_type column
                if key == "lead_type":
                    colour = LEAD_TYPE_COLOURS.get(value, "#a6adc8")
                    item.setForeground(QBrush(QColor(colour)))

                self._table.setItem(row_idx, col_idx, item)

        self._table.setUpdatesEnabled(True)

    # ------------------------------------------------------------------
    # Sorting
    # ------------------------------------------------------------------

    def _header_clicked(self, col: int) -> None:
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True
        self._apply_filters()

        # Visual indicator on header
        hh = self._table.horizontalHeader()
        hh.setSortIndicator(col, Qt.SortOrder.AscendingOrder if self._sort_asc else Qt.SortOrder.DescendingOrder)
        hh.setSortIndicatorShown(True)

    # ------------------------------------------------------------------
    # Interactions
    # ------------------------------------------------------------------

    def _get_lead_from_row(self, row: int) -> tuple[int, dict] | tuple[None, None]:
        item = self._table.item(row, 0)
        if not item:
            return None, None
        lead_id = item.data(Qt.ItemDataRole.UserRole)
        if lead_id is None or row >= len(self._filtered_leads):
            return None, None
        return lead_id, self._filtered_leads[row]

    def _on_double_click(self, index) -> None:
        col_key = COLUMNS[index.column()][1]
        if col_key == "notes":
            self._open_notes_editor(index.row())
        elif col_key == "maps_link":
            _, lead = self._get_lead_from_row(index.row())
            if lead and lead.get("maps_link"):
                webbrowser.open(lead["maps_link"])
        elif col_key in ("whatsapp", "instagram", "facebook", "website"):
            _, lead = self._get_lead_from_row(index.row())
            if lead:
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

        # Notes
        notes_act = QAction("✏  Edit Notes", self)
        notes_act.triggered.connect(lambda: self._open_notes_editor(row))
        menu.addAction(notes_act)

        menu.addSeparator()

        # Google Maps
        maps_link = lead.get("maps_link", "")
        if maps_link:
            open_maps_act = QAction("🗺  Open in Google Maps", self)
            open_maps_act.triggered.connect(lambda: webbrowser.open(maps_link))
            menu.addAction(open_maps_act)

            copy_maps_act = QAction("📋  Copy Google Maps Link", self)
            copy_maps_act.triggered.connect(lambda: self._copy_to_clipboard(maps_link))
            menu.addAction(copy_maps_act)

        # WhatsApp
        wa = lead.get("whatsapp", "")
        if wa:
            wa_act = QAction("💬  Open WhatsApp", self)
            wa_act.triggered.connect(lambda: webbrowser.open(wa))
            menu.addAction(wa_act)

        # Website
        website = lead.get("website", "")
        if website:
            web_act = QAction("🌐  Open Website", self)
            web_act.triggered.connect(lambda: webbrowser.open(website))
            menu.addAction(web_act)

        # Collections
        menu.addSeparator()
        coll_menu = menu.addMenu("📁  Add to Collection")
        collections = db.get_collections()
        if collections:
            for coll in collections:
                act = QAction(coll["name"], self)
                coll_id = coll["id"]
                act.triggered.connect(
                    lambda checked, _cid=coll_id, _lid=lead_id:
                    self._add_to_collection(_cid, _lid)
                )
                coll_menu.addAction(act)
        else:
            coll_menu.addAction(QAction("(No collections yet)", self))

        menu.addSeparator()

        # Delete
        del_act = QAction("🗑  Delete Lead", self)
        del_act.triggered.connect(lambda: self._delete_lead(lead_id))
        menu.addAction(del_act)

        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _set_status(self, lead_id: int, status: str) -> None:
        db.update_lead_status(lead_id, status)
        self.refresh()

    def _open_notes_editor(self, row: int) -> None:
        lead_id, lead = self._get_lead_from_row(row)
        if lead_id is None:
            return
        dlg = NotesDialog(lead_id, lead.get("notes", ""), parent=self)
        if dlg.exec():
            db.update_lead_notes(lead_id, dlg.get_notes())
            self.refresh()

    def _delete_lead(self, lead_id: int) -> None:
        reply = QMessageBox.question(
            self,
            "Delete Lead",
            "Permanently delete this lead?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_lead(lead_id)
            self.refresh()

    def _add_to_collection(self, collection_id: int, lead_id: int) -> None:
        db.add_leads_to_collection(collection_id, [lead_id])

    @staticmethod
    def _copy_to_clipboard(text: str) -> None:
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(text)
