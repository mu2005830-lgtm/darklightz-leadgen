"""
Search widget — the "Start Search" form that kicks off a scraping session.

v2.0
----
* Pulls default lead count and scroll_delay from settings.
* Progress log uses monospace QTextEdit styled as LogView.
* Fixed: self._max initialised in __init__ to prevent AttributeError on
  stale signals after a crash.
* Fixed: subtitle updated to reflect v2.0 filtering behaviour.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QSpinBox, QPushButton, QProgressBar,
    QTextEdit, QGroupBox, QCheckBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from backend.scraper import ScraperWorker
from database import operations as db
from utilities.logger import logger


class SearchWidget(QWidget):
    """Lead search form + real-time progress log."""

    # Emitted whenever a new lead has been inserted into the DB
    leads_updated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: ScraperWorker | None = None
        self._search_id: int | None = None
        self._max: int = 0
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(0)

        title = QLabel("Lead Search")
        title.setObjectName("PageTitle")
        subtitle = QLabel(
            "Enter your search criteria and click Start Search.  "
            "Only businesses without a dedicated real website are collected — "
            "businesses with Instagram, Facebook, or WhatsApp only are included as leads."
        )
        subtitle.setObjectName("PageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(12)

        # ---- Search form group ----------------------------------------
        form_group = QGroupBox("Search Parameters")
        form_layout = QVBoxLayout(form_group)
        form_layout.setSpacing(12)

        # Row 1: Keyword + City
        row1 = QHBoxLayout()
        row1.setSpacing(16)

        kw_col = QVBoxLayout()
        kw_lbl = QLabel("Business Keyword")
        kw_lbl.setObjectName("FormLabel")
        self._keyword_input = QLineEdit()
        self._keyword_input.setPlaceholderText("e.g. Restaurant, Salon, Gym …")
        kw_col.addWidget(kw_lbl)
        kw_col.addWidget(self._keyword_input)

        city_col = QVBoxLayout()
        city_lbl = QLabel("City / Location")
        city_lbl.setObjectName("FormLabel")
        self._city_input = QLineEdit()
        self._city_input.setPlaceholderText("e.g. Lahore, Karachi, Islamabad …")
        city_col.addWidget(city_lbl)
        city_col.addWidget(self._city_input)

        row1.addLayout(kw_col, 2)
        row1.addLayout(city_col, 2)
        form_layout.addLayout(row1)

        # Row 2: Count + Options
        row2 = QHBoxLayout()
        row2.setSpacing(16)

        count_col = QVBoxLayout()
        count_lbl = QLabel("Number of Leads")
        count_lbl.setObjectName("FormLabel")
        self._count_spin = QSpinBox()
        self._count_spin.setRange(1, 2000)
        default_count = int(db.get_setting("default_count", "50"))
        self._count_spin.setValue(default_count)
        self._count_spin.setSingleStep(10)
        count_col.addWidget(count_lbl)
        count_col.addWidget(self._count_spin)

        opts_col = QVBoxLayout()
        opts_lbl = QLabel("Options")
        opts_lbl.setObjectName("FormLabel")
        headless_default = db.get_setting("headless", "true") == "true"
        self._headless_cb = QCheckBox("Run browser in background (headless)")
        self._headless_cb.setChecked(headless_default)
        opts_col.addWidget(opts_lbl)
        opts_col.addWidget(self._headless_cb)

        row2.addLayout(count_col, 1)
        row2.addLayout(opts_col, 3)
        form_layout.addLayout(row2)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self._start_btn = QPushButton("▶  Start Search")
        self._start_btn.clicked.connect(self._start_search)

        self._stop_btn = QPushButton("⏹  Stop")
        self._stop_btn.setObjectName("StopButton")
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop_search)

        btn_row.addWidget(self._start_btn)
        btn_row.addWidget(self._stop_btn)
        btn_row.addStretch()
        form_layout.addLayout(btn_row)

        layout.addWidget(form_group)
        layout.addSpacing(12)

        # ---- Progress group ------------------------------------------
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setSpacing(8)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setFormat("")
        progress_layout.addWidget(self._progress_bar)

        self._status_lbl = QLabel("Ready")
        self._status_lbl.setStyleSheet("color: #a6adc8; font-size: 12px;")
        progress_layout.addWidget(self._status_lbl)

        self._log = QTextEdit()
        self._log.setObjectName("LogView")
        self._log.setReadOnly(True)
        self._log.setMinimumHeight(200)
        progress_layout.addWidget(self._log)

        layout.addWidget(progress_group)
        layout.addStretch()

    # ------------------------------------------------------------------
    # Search control
    # ------------------------------------------------------------------

    def _start_search(self) -> None:
        keyword = self._keyword_input.text().strip()
        city    = self._city_input.text().strip()
        max_l   = self._count_spin.value()

        if not keyword or not city:
            self._status_lbl.setText("⚠  Please enter both a keyword and a city.")
            return

        self._log.clear()
        self._status_lbl.setText("Starting …")
        self._progress_bar.setValue(0)
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._max = max_l

        search_id = db.create_search(keyword, city, max_l)
        self._search_id = search_id

        scroll_delay = int(db.get_setting("scroll_delay", "1500"))

        self._worker = ScraperWorker(
            keyword=keyword,
            city=city,
            max_leads=max_l,
            search_id=search_id,
            headless=self._headless_cb.isChecked(),
            scroll_delay=scroll_delay,
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.lead_found.connect(self._on_lead_found)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _stop_search(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._status_lbl.setText("Stopping …")
            self._stop_btn.setEnabled(False)

    # ------------------------------------------------------------------
    # Worker signals
    # ------------------------------------------------------------------

    def _on_progress(self, count: int, message: str) -> None:
        pct = int(count / max(self._max, 1) * 100)
        self._progress_bar.setValue(pct)
        self._status_lbl.setText(message)
        self._log.append(f"[{count}/{self._max}]  {message}")

    def _on_lead_found(self, lead: dict) -> None:
        lead_id = db.insert_lead(lead)
        if lead_id:
            self.leads_updated.emit()

    def _on_finished(self, total: int, stopped: bool) -> None:
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._progress_bar.setValue(100 if not stopped else self._progress_bar.value())

        if self._search_id is not None:
            status = "stopped" if stopped else "complete"
            db.update_search_status(self._search_id, status)

        msg = (
            f"Stopped early — {total} lead(s) collected."
            if stopped
            else f"Search complete — {total} lead(s) collected."
        )
        self._status_lbl.setText(msg)
        self._log.append(f"\n✔  {msg}")
        logger.info(msg)

    def _on_error(self, message: str) -> None:
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._status_lbl.setText(f"⚠  Error: {message}")
        self._log.append(f"\n✖  Error: {message}")

        if self._search_id is not None:
            db.update_search_status(self._search_id, "stopped")

        logger.error("Scraper error: %s", message)
