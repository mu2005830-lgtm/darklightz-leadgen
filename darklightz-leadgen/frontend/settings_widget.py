"""
Settings widget — Darklightz Lead Generator v2.0.

v2.0: Added update check toggle setting.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QCheckBox, QSpinBox,
    QComboBox, QFrame, QMessageBox,
)
from PyQt6.QtCore import Qt

from database import operations as db
from utilities.logger import logger


class SettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._load_settings()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("Settings")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Configure scraper behaviour and application preferences.")
        subtitle.setObjectName("PageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # ---- Scraper settings ----------------------------------------
        scraper_group = QGroupBox("Scraper")
        scraper_layout = QVBoxLayout(scraper_group)
        scraper_layout.setSpacing(12)

        # Headless
        headless_row = QHBoxLayout()
        headless_lbl = QLabel("Run browser in background (headless mode)")
        headless_lbl.setWordWrap(True)
        self._headless_cb = QCheckBox()
        self._headless_cb.setChecked(True)
        headless_row.addWidget(self._headless_cb)
        headless_row.addWidget(headless_lbl, 1)
        scraper_layout.addLayout(headless_row)

        # Scroll delay
        delay_row = QHBoxLayout()
        delay_lbl = QLabel("Scroll delay between results (ms):")
        delay_lbl.setFixedWidth(260)
        self._delay_spin = QSpinBox()
        self._delay_spin.setRange(500, 5000)
        self._delay_spin.setSingleStep(250)
        self._delay_spin.setValue(1500)
        self._delay_spin.setFixedWidth(100)
        delay_row.addWidget(delay_lbl)
        delay_row.addWidget(self._delay_spin)
        delay_row.addStretch()
        scraper_layout.addLayout(delay_row)

        # Default lead count
        count_row = QHBoxLayout()
        count_lbl = QLabel("Default number of leads to collect:")
        count_lbl.setFixedWidth(260)
        self._default_count = QSpinBox()
        self._default_count.setRange(1, 2000)
        self._default_count.setValue(50)
        self._default_count.setSingleStep(25)
        self._default_count.setFixedWidth(100)
        count_row.addWidget(count_lbl)
        count_row.addWidget(self._default_count)
        count_row.addStretch()
        scraper_layout.addLayout(count_row)

        layout.addWidget(scraper_group)

        # ---- Application settings ------------------------------------
        app_group = QGroupBox("Application")
        app_layout = QVBoxLayout(app_group)
        app_layout.setSpacing(12)

        # Auto-update check on startup
        update_row = QHBoxLayout()
        update_lbl = QLabel("Check for updates automatically on startup")
        update_lbl.setWordWrap(True)
        self._auto_update_cb = QCheckBox()
        self._auto_update_cb.setChecked(True)
        update_row.addWidget(self._auto_update_cb)
        update_row.addWidget(update_lbl, 1)
        app_layout.addLayout(update_row)

        layout.addWidget(app_group)

        # ---- Data management ------------------------------------------
        data_group = QGroupBox("Data Management")
        data_layout = QVBoxLayout(data_group)
        data_layout.setSpacing(10)

        delete_btn = QPushButton("🗑  Delete ALL Leads (cannot be undone)")
        delete_btn.setObjectName("DangerButton")
        delete_btn.clicked.connect(self._confirm_delete_all)
        data_layout.addWidget(delete_btn)

        layout.addWidget(data_group)

        # ---- Save button -------------------------------------------
        save_btn = QPushButton("Save Settings")
        save_btn.setFixedWidth(160)
        save_btn.clicked.connect(self._save_settings)
        layout.addWidget(save_btn)

        layout.addStretch()

    # ------------------------------------------------------------------
    def _load_settings(self) -> None:
        self._headless_cb.setChecked(
            db.get_setting("headless", "true") == "true"
        )
        self._delay_spin.setValue(
            int(db.get_setting("scroll_delay", "1500"))
        )
        self._default_count.setValue(
            int(db.get_setting("default_count", "50"))
        )
        self._auto_update_cb.setChecked(
            db.get_setting("auto_update_check", "true") == "true"
        )

    def _save_settings(self) -> None:
        db.set_setting("headless",           "true" if self._headless_cb.isChecked() else "false")
        db.set_setting("scroll_delay",       str(self._delay_spin.value()))
        db.set_setting("default_count",      str(self._default_count.value()))
        db.set_setting("auto_update_check",  "true" if self._auto_update_cb.isChecked() else "false")
        logger.info("Settings saved.")
        QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully.")

    def _confirm_delete_all(self) -> None:
        reply = QMessageBox.warning(
            self,
            "Delete All Leads",
            "This will permanently delete ALL leads from the database.\n"
            "This action cannot be undone.\n\nAre you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Yes:
            import sqlite3
            from database.models import get_connection
            conn = get_connection()
            with conn:
                conn.execute("DELETE FROM leads")
                conn.execute("DELETE FROM searches")
            conn.close()
            logger.info("All leads deleted by user.")
            QMessageBox.information(self, "Done", "All leads and searches have been deleted.")
