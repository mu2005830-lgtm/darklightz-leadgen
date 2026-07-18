"""
Export widget — export leads to Excel, CSV, or PDF.
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
    """Export page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(0)

        title = QLabel("Export Leads")
        title.setObjectName("PageTitle")
        subtitle = QLabel(
            "Export your leads to Excel, CSV, or PDF. "
            "All currently stored leads are exported unless a status filter is applied."
        )
        subtitle.setObjectName("PageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(20)

        # ---- Filter options ------------------------------------------
        filter_group = QGroupBox("Export Filter")
        filter_layout = QHBoxLayout(filter_group)
        filter_layout.setSpacing(14)

        filter_layout.addWidget(QLabel("Status:"))
        self._status_filter = QComboBox()
        self._status_filter.addItems([
            "All", "New", "Contacted", "Follow-up",
            "Interested", "Closed", "Not Interested",
        ])
        self._status_filter.setFixedWidth(160)
        filter_layout.addWidget(self._status_filter)
        filter_layout.addStretch()

        layout.addWidget(filter_group)
        layout.addSpacing(16)

        # ---- Export buttons ------------------------------------------
        exports_group = QGroupBox("Export Format")
        exports_layout = QVBoxLayout(exports_group)
        exports_layout.setSpacing(12)

        def _export_card(icon: str, title_txt: str, desc: str, handler) -> QFrame:
            card = QFrame()
            card.setObjectName("StatCard")
            row = QHBoxLayout(card)
            row.setContentsMargins(16, 12, 16, 12)
            row.setSpacing(16)

            text_col = QVBoxLayout()
            title_lbl = QLabel(f"{icon}  {title_txt}")
            title_lbl.setStyleSheet("font-weight: bold; font-size: 14px; color: #cdd6f4;")
            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet("color: #a6adc8; font-size: 12px;")
            text_col.addWidget(title_lbl)
            text_col.addWidget(desc_lbl)

            btn = QPushButton(f"Export {title_txt}")
            btn.setObjectName("ExportButton")
            btn.setFixedWidth(160)
            btn.clicked.connect(handler)

            row.addLayout(text_col, 1)
            row.addWidget(btn)
            return card

        exports_layout.addWidget(_export_card(
            "📊", "Excel (.xlsx)",
            "Styled spreadsheet with all columns and alternating row colours.",
            self._export_excel,
        ))
        exports_layout.addWidget(_export_card(
            "📄", "CSV (.csv)",
            "Universal comma-separated format — opens in any spreadsheet app.",
            self._export_csv,
        ))
        exports_layout.addWidget(_export_card(
            "📑", "PDF (.pdf)",
            "Formatted printable report, landscape A4 with Darklightz branding.",
            self._export_pdf,
        ))

        layout.addWidget(exports_group)
        layout.addStretch()

        # Status label at the bottom
        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet("color: #a6e3a1; font-size: 12px;")
        layout.addWidget(self._status_lbl)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_leads(self) -> list[dict]:
        status = self._status_filter.currentText()
        return db.get_leads(status_filter=status)

    def _default_name(self, ext: str) -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"darklightz_leads_{ts}.{ext}"

    def _export_dir(self) -> str:
        saved = db.get_setting("export_dir")
        if saved and os.path.isdir(saved):
            return saved
        return str(Path.home() / "Downloads")

    # ------------------------------------------------------------------
    # Export handlers
    # ------------------------------------------------------------------

    def _export_excel(self) -> None:
        leads = self._get_leads()
        if not leads:
            QMessageBox.information(self, "No Leads", "No leads match the current filter.")
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
        leads = self._get_leads()
        if not leads:
            QMessageBox.information(self, "No Leads", "No leads match the current filter.")
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
        leads = self._get_leads()
        if not leads:
            QMessageBox.information(self, "No Leads", "No leads match the current filter.")
            return
        default = os.path.join(self._export_dir(), self._default_name("pdf"))
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF File", default, "PDF Files (*.pdf)"
        )
        if not path:
            return
        try:
            status = self._status_filter.currentText()
            report_title = f"Lead Report — {status}"
            out = pdf_exporter.export(leads, path, title=report_title)
            self._status_lbl.setText(f"✅  Saved {len(leads):,} leads → {out}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))
