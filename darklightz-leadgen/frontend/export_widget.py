"""
Export widget — Darklightz Lead Generator v2.0 (redesigned).

Redesign: instead of exporting the entire database, the user first selects
a Lead Collection (search session), then exports only that collection.

Supported formats: Excel (.xlsx), CSV (.csv), PDF (.pdf).
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QGroupBox,
    QComboBox, QMessageBox, QFrame,
)
from PyQt6.QtCore import Qt

from database import operations as db
from exports import excel_exporter, csv_exporter, pdf_exporter


class ExportWidget(QWidget):
    """Export a selected Lead Collection to Excel, CSV, or PDF."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sessions: list[dict] = []
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(0)

        title = QLabel("Export Leads")
        title.setObjectName("PageTitle")
        subtitle = QLabel(
            "Select a Lead Collection, then choose your export format. "
            "Only the selected collection's leads are exported."
        )
        subtitle.setObjectName("PageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(20)

        # ---- Collection selector -------------------------------------
        select_group = QGroupBox("Select Lead Collection")
        select_layout = QHBoxLayout(select_group)
        select_layout.setSpacing(12)

        self._collection_combo = QComboBox()
        self._collection_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )
        self._collection_combo.setMinimumWidth(420)
        self._collection_combo.currentIndexChanged.connect(
            self._on_collection_changed
        )

        refresh_btn = QPushButton("↻")
        refresh_btn.setObjectName("SecondaryButton")
        refresh_btn.setFixedWidth(40)
        refresh_btn.setToolTip("Refresh collection list")
        refresh_btn.clicked.connect(self.refresh)

        self._meta_lbl = QLabel("")
        self._meta_lbl.setStyleSheet("color: #a6adc8; font-size: 12px;")

        select_layout.addWidget(self._collection_combo)
        select_layout.addWidget(refresh_btn)
        select_layout.addWidget(self._meta_lbl)
        select_layout.addStretch()

        layout.addWidget(select_group)
        layout.addSpacing(16)

        # ---- Export buttons ------------------------------------------
        exports_group = QGroupBox("Export Format")
        exports_layout = QVBoxLayout(exports_group)
        exports_layout.setSpacing(12)

        exports_layout.addWidget(self._export_card(
            "📊", "Excel (.xlsx)",
            "Styled spreadsheet with all columns and clickable hyperlinks.",
            self._export_excel,
        ))
        exports_layout.addWidget(self._export_card(
            "📄", "CSV (.csv)",
            "Universal comma-separated format — opens in any spreadsheet app.",
            self._export_csv,
        ))
        exports_layout.addWidget(self._export_card(
            "📑", "PDF (.pdf)",
            "Formatted printable report, landscape A4 with Darklightz branding.",
            self._export_pdf,
        ))

        layout.addWidget(exports_group)
        layout.addStretch()

        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet("color: #a6e3a1; font-size: 12px;")
        layout.addWidget(self._status_lbl)

        self.refresh()

    @staticmethod
    def _export_card(icon: str, title_txt: str, desc: str, handler) -> QFrame:
        card = QFrame()
        card.setObjectName("StatCard")
        row = QHBoxLayout(card)
        row.setContentsMargins(16, 12, 16, 12)
        row.setSpacing(16)

        text_col = QVBoxLayout()
        title_lbl = QLabel(f"{icon}  {title_txt}")
        title_lbl.setStyleSheet(
            "font-weight: bold; font-size: 14px; color: #cdd6f4;"
        )
        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet("color: #a6adc8; font-size: 12px;")
        text_col.addWidget(title_lbl)
        text_col.addWidget(desc_lbl)

        btn = QPushButton(f"Export {title_txt}")
        btn.setObjectName("ExportButton")
        btn.setFixedWidth(170)
        btn.clicked.connect(handler)

        row.addLayout(text_col, 1)
        row.addWidget(btn)
        return card

    # ------------------------------------------------------------------
    # Data helpers
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Reload the list of search sessions into the combo box."""
        self._sessions = db.get_searches_with_counts()
        self._collection_combo.blockSignals(True)
        self._collection_combo.clear()

        if not self._sessions:
            self._collection_combo.addItem("(No collections yet — run a search first)")
        else:
            for s in self._sessions:
                keyword  = s.get("keyword", "?")
                city     = s.get("city", "?")
                count    = s.get("lead_count", 0)
                raw_date = s.get("created_at", "")
                try:
                    dt = datetime.strptime(raw_date[:19], "%Y-%m-%d %H:%M:%S")
                    date_str = dt.strftime("%d %b %Y  %I:%M %p")
                except Exception:
                    date_str = raw_date[:10]
                label = f"{keyword}  —  {city}  ·  {date_str}  ·  {count} leads"
                self._collection_combo.addItem(label)

        self._collection_combo.blockSignals(False)
        self._on_collection_changed(0)

    def _on_collection_changed(self, index: int) -> None:
        if not self._sessions or index < 0 or index >= len(self._sessions):
            self._meta_lbl.setText("")
            return
        s = self._sessions[index]
        count = s.get("lead_count", 0)
        status = s.get("status", "")
        status_icon = "✅" if status == "complete" else "⏸"
        self._meta_lbl.setText(
            f"{status_icon}  {count} lead{'s' if count != 1 else ''} ready to export"
        )

    def _get_selected_session(self) -> dict | None:
        idx = self._collection_combo.currentIndex()
        if not self._sessions or idx < 0 or idx >= len(self._sessions):
            return None
        return self._sessions[idx]

    def _get_leads(self) -> list[dict]:
        session = self._get_selected_session()
        if not session:
            return []
        return db.get_leads(search_id=session["id"])

    def _collection_label(self) -> str:
        session = self._get_selected_session()
        if not session:
            return "leads"
        keyword = session.get("keyword", "")
        city    = session.get("city", "")
        return f"{keyword}_{city}".replace(" ", "_").lower()

    def _default_name(self, ext: str) -> str:
        ts    = datetime.now().strftime("%Y%m%d_%H%M%S")
        label = self._collection_label()
        return f"darklightz_{label}_{ts}.{ext}"

    def _export_dir(self) -> str:
        saved = db.get_setting("export_dir")
        if saved and os.path.isdir(saved):
            return saved
        return str(Path.home() / "Downloads")

    # ------------------------------------------------------------------
    # Export handlers
    # ------------------------------------------------------------------

    def _no_session_warning(self) -> bool:
        """Show warning and return True if no valid session is selected."""
        if not self._get_selected_session():
            QMessageBox.warning(
                self, "No Collection Selected",
                "Please select a Lead Collection to export."
            )
            return True
        return False

    def _export_excel(self) -> None:
        if self._no_session_warning():
            return
        leads = self._get_leads()
        if not leads:
            QMessageBox.information(
                self, "No Leads", "This collection has no leads yet."
            )
            return
        default = os.path.join(self._export_dir(), self._default_name("xlsx"))
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Excel File", default, "Excel Files (*.xlsx)"
        )
        if not path:
            return
        try:
            out = excel_exporter.export(leads, path)
            self._status_lbl.setText(f"✅  Saved {len(leads):,} leads → {out}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))

    def _export_csv(self) -> None:
        if self._no_session_warning():
            return
        leads = self._get_leads()
        if not leads:
            QMessageBox.information(
                self, "No Leads", "This collection has no leads yet."
            )
            return
        default = os.path.join(self._export_dir(), self._default_name("csv"))
        path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV File", default, "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            out = csv_exporter.export(leads, path)
            self._status_lbl.setText(f"✅  Saved {len(leads):,} leads → {out}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))

    def _export_pdf(self) -> None:
        if self._no_session_warning():
            return
        leads = self._get_leads()
        if not leads:
            QMessageBox.information(
                self, "No Leads", "This collection has no leads yet."
            )
            return
        default = os.path.join(self._export_dir(), self._default_name("pdf"))
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF File", default, "PDF Files (*.pdf)"
        )
        if not path:
            return
        try:
            out = pdf_exporter.export(leads, path)
            self._status_lbl.setText(f"✅  Saved {len(leads):,} leads → {out}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))
