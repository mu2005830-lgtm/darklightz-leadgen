"""
About widget — Darklightz Lead Generator v2.0.

v2.0: "Check for Updates" button with live GitHub release check.
"""

from __future__ import annotations

import webbrowser
from datetime import date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QMessageBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from utilities.updater import check_for_updates, UpdateInfo
from utilities.logger import logger

APP_VERSION = "2.0.1"


# ---------------------------------------------------------------------------
# Background updater thread
# ---------------------------------------------------------------------------

class _UpdateWorker(QThread):
    done = pyqtSignal(object)   # UpdateInfo

    def run(self) -> None:
        info = check_for_updates(APP_VERSION)
        self.done.emit(info)


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------

class AboutWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: _UpdateWorker | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(0)

        title    = QLabel("About")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Application information, legal notices, and updates.")
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

        # ---- App info card ------------------------------------------
        app_card = _card()
        cl = app_card.layout()

        cl.addWidget(_heading("Darklightz Studio — Lead Generation Suite"))

        for label, value in [
            ("Version",    f"v{APP_VERSION}"),
            ("Build date", "2025"),
            ("Developer",  "Darklightz Studio"),
            ("License",    "Proprietary — All rights reserved"),
        ]:
            _row(cl, label, value)

        # Update buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self._update_btn = QPushButton("🔄  Check for Updates")
        self._update_btn.setObjectName("SecondaryButton")
        self._update_btn.setFixedHeight(36)
        self._update_btn.clicked.connect(self._check_updates)

        self._update_status = QLabel("")
        self._update_status.setStyleSheet("color: #a6adc8; font-size: 12px;")

        btn_row.addWidget(self._update_btn)
        btn_row.addWidget(self._update_status)
        btn_row.addStretch()
        cl.addLayout(btn_row)

        vbox.addWidget(app_card)

        # ---- Technology stack card ----------------------------------
        tech_card = _card()
        tcl = tech_card.layout()
        tcl.addWidget(_heading("Technology Stack"))
        for tech, desc in [
            ("Python 3.11+",            "Core runtime"),
            ("PyQt6",                   "Desktop UI framework"),
            ("Playwright / Chromium",   "Browser automation for scraping"),
            ("SQLite",                  "Local database — no server required"),
            ("openpyxl",               "Excel export"),
            ("ReportLab",               "PDF export"),
            ("Requests",                "Update checking (GitHub API)"),
        ]:
            _row(tcl, tech, desc)
        vbox.addWidget(tech_card)

        # ---- Legal card --------------------------------------------
        legal_card = _card()
        lcl = legal_card.layout()
        lcl.addWidget(_heading("Legal & Disclaimer"))
        warning = QLabel(
            "This application collects publicly available information from Google Maps "
            "for legitimate business prospecting purposes.\n\n"
            "Google's Terms of Service prohibit automated data collection. "
            "Use this tool responsibly and in compliance with applicable laws "
            "in your jurisdiction. The developer assumes no liability for misuse.\n\n"
            "Never use fabricated or purchased data. Only contact businesses "
            "through legitimate channels."
        )
        warning.setWordWrap(True)
        warning.setStyleSheet(
            "color: #f9e2af; font-size: 11px; "
            "background: #2a2516; padding: 12px; border-radius: 6px;"
        )
        lcl.addWidget(warning)
        vbox.addWidget(legal_card)

        # ---- Copyright ----------------------------------------------
        copy_lbl = QLabel(
            f"© {date.today().year} Darklightz Studio. All rights reserved.\n"
            "Developed by Darklightz Studio."
        )
        copy_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        copy_lbl.setStyleSheet("color: #45475a; font-size: 10px;")
        vbox.addWidget(copy_lbl)
        vbox.addStretch()

        outer.addWidget(scroll)

    # ------------------------------------------------------------------
    # Update check
    # ------------------------------------------------------------------

    def _check_updates(self) -> None:
        self._update_btn.setEnabled(False)
        self._update_btn.setText("Checking …")
        self._update_status.setText("")

        self._worker = _UpdateWorker()
        self._worker.done.connect(self._on_update_result)
        self._worker.start()

    def _on_update_result(self, info: UpdateInfo) -> None:
        self._update_btn.setEnabled(True)
        self._update_btn.setText("🔄  Check for Updates")

        if info.error:
            self._update_status.setStyleSheet("color: #f38ba8; font-size: 12px;")
            self._update_status.setText(f"⚠  {info.error}")
            logger.warning("Update check error: %s", info.error)
            return

        if info.update_available:
            self._update_status.setStyleSheet("color: #a6e3a1; font-size: 12px;")
            self._update_status.setText(
                f"✔  v{info.latest_version} available!"
            )
            reply = QMessageBox.question(
                self,
                "Update Available",
                f"Version {info.latest_version} is available.\n\n"
                f"Release: {info.release_name}\n\n"
                f"Would you like to open the download page?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                webbrowser.open(info.download_url or info.release_url)
        else:
            self._update_status.setStyleSheet("color: #a6adc8; font-size: 12px;")
            self._update_status.setText(
                f"✔  You are up to date (v{APP_VERSION})."
            )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _card() -> QFrame:
    card   = QFrame()
    card.setObjectName("StatCard")
    card.setMaximumWidth(700)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(24, 20, 24, 20)
    layout.setSpacing(6)
    return card


def _heading(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        "color: #cba6f7; font-size: 14px; font-weight: bold; margin-bottom: 8px;"
    )
    return lbl


def _row(layout, label: str, value: str) -> None:
    row = QWidget()
    rl  = QHBoxLayout(row)
    rl.setContentsMargins(0, 2, 0, 2)

    lbl = QLabel(label)
    lbl.setStyleSheet("color: #6c7086; font-size: 11px;")
    lbl.setFixedWidth(140)

    val = QLabel(value)
    val.setStyleSheet("color: #cdd6f4; font-size: 12px; font-weight: bold;")

    rl.addWidget(lbl)
    rl.addWidget(val, 1)
    layout.addWidget(row)
