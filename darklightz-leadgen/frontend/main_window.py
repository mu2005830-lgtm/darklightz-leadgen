"""
Main application window — Darklightz Studio Lead Generation Suite v2.0.

v2.0: Auto-update check on startup (respects settings toggle).

Layout
------
    ┌──────────┬──────────────────────────────────────┐
    │ Sidebar  │  Content area (stacked pages)         │
    │          │                                       │
    │          ├──────────────────────────────────────┤
    │          │  footer: "Developed by Darklightz…"  │
    └──────────┴──────────────────────────────────────┘
"""

from __future__ import annotations

import os
import sys
import webbrowser

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStackedWidget, QSizePolicy,
    QStatusBar, QFrame, QMessageBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QCloseEvent, QPixmap

from frontend.dashboard_widget import DashboardWidget
from frontend.search_widget    import SearchWidget
from frontend.leads_widget     import LeadsWidget
from frontend.export_widget    import ExportWidget
from frontend.settings_widget  import SettingsWidget
from frontend.about_widget     import AboutWidget
from utilities.logger import logger

APP_VERSION = "2.0.0"

# ---------------------------------------------------------------------------
# Asset resolution
# ---------------------------------------------------------------------------
if getattr(sys, "frozen", False):
    _BASE = sys._MEIPASS
else:
    _BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_LOGO_PATH = os.path.join(_BASE, "assets", "logo.png")
_ICON_PATH = os.path.join(_BASE, "assets", "icon.ico")

# ---------------------------------------------------------------------------
# Nav item spec: (label, icon, page index)
# ---------------------------------------------------------------------------
NAV_ITEMS = [
    ("Dashboard",   "⬛", 0),
    ("Lead Search", "🔍", 1),
    ("Lead Table",  "📋", 2),
    ("Export",      "📤", 3),
    ("Settings",    "⚙",  4),
    ("About",       "ℹ",  5),
]


# ---------------------------------------------------------------------------
# Background startup update check
# ---------------------------------------------------------------------------

class _StartupUpdateWorker(QThread):
    update_available = pyqtSignal(str, str)   # (latest_version, download_url)

    def run(self) -> None:
        try:
            from utilities.updater import check_for_updates
            info = check_for_updates(APP_VERSION)
            if info.update_available and not info.error:
                self.update_available.emit(
                    info.latest_version,
                    info.download_url or info.release_url,
                )
        except Exception as exc:
            logger.debug("Startup update check failed: %s", exc)


# ---------------------------------------------------------------------------
# Nav button
# ---------------------------------------------------------------------------

class NavButton(QPushButton):
    def __init__(self, label: str, icon_char: str):
        super().__init__(f"  {icon_char}   {label}")
        self.setObjectName("NavButton")
        self.setCheckable(False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setProperty("active", False)
        self.setMinimumHeight(40)
        font = QFont()
        font.setPointSize(11)
        self.setFont(font)

    def set_active(self, active: bool) -> None:
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            f"Darklightz Studio — Lead Generation Suite  v{APP_VERSION}"
        )
        self.setMinimumSize(1100, 680)
        self.resize(1300, 800)

        for path in (_ICON_PATH, _LOGO_PATH):
            if os.path.exists(path):
                self.setWindowIcon(QIcon(path))
                break

        self._nav_buttons: list[NavButton] = []
        self._startup_worker: _StartupUpdateWorker | None = None
        self._build_ui()
        self._navigate(0)
        self._maybe_check_updates_on_startup()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────────────────
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Logo / title
        logo_widget = QWidget()
        logo_layout = QVBoxLayout(logo_widget)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(0)

        if os.path.exists(_LOGO_PATH):
            logo_pix = QPixmap(_LOGO_PATH).scaledToWidth(
                140, Qt.TransformationMode.SmoothTransformation
            )
            logo_lbl = QLabel()
            logo_lbl.setPixmap(logo_pix)
            logo_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            logo_lbl.setContentsMargins(0, 16, 0, 4)
            logo_layout.addWidget(logo_lbl)

        title_lbl = QLabel("DARKLIGHTZ")
        title_lbl.setObjectName("AppTitle")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        sub_lbl = QLabel("Lead Generation Suite")
        sub_lbl.setObjectName("AppSubtitle")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        ver_lbl = QLabel(f"v{APP_VERSION}")
        ver_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        ver_lbl.setStyleSheet("color: #45475a; font-size: 9px; padding-bottom: 8px;")

        logo_layout.addWidget(title_lbl)
        logo_layout.addWidget(sub_lbl)
        logo_layout.addWidget(ver_lbl)
        sidebar_layout.addWidget(logo_widget)

        # Divider
        div = QFrame()
        div.setObjectName("SidebarDivider")
        sidebar_layout.addWidget(div)
        sidebar_layout.addSpacing(8)

        # Nav buttons
        for label, icon_char, page_idx in NAV_ITEMS:
            btn = NavButton(label, icon_char)
            btn.clicked.connect(
                lambda checked, idx=page_idx: self._navigate(idx)
            )
            sidebar_layout.addWidget(btn)
            self._nav_buttons.append(btn)

        sidebar_layout.addStretch()

        # Footer
        footer_lbl = QLabel("Developed by\nDarklightz Studio")
        footer_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        footer_lbl.setStyleSheet(
            "color: #45475a; font-size: 9px; padding: 8px 14px 12px 14px;"
        )
        sidebar_layout.addWidget(footer_lbl)

        root.addWidget(sidebar)

        # ── Right pane: content + footer ─────────────────────────────
        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)

        # Pages
        self._stack = QStackedWidget()
        self._dashboard  = DashboardWidget()
        self._search     = SearchWidget()
        self._leads      = LeadsWidget()
        self._export     = ExportWidget()
        self._settings   = SettingsWidget()
        self._about      = AboutWidget()

        for widget in (
            self._dashboard, self._search, self._leads,
            self._export, self._settings, self._about,
        ):
            self._stack.addWidget(widget)

        # Forward search → leads signal
        self._search.leads_updated.connect(self._leads.refresh)
        self._search.leads_updated.connect(self._dashboard.refresh)

        right.addWidget(self._stack, 1)

        # Footer bar
        footer_bar = QFrame()
        footer_bar.setObjectName("StatCard")
        footer_bar.setMaximumHeight(28)
        footer_bar.setStyleSheet(
            "border-radius: 0; border-top: 1px solid #313244; "
            "background-color: #181825;"
        )
        fb_layout = QHBoxLayout(footer_bar)
        fb_layout.setContentsMargins(16, 0, 16, 0)
        fb_layout.setSpacing(0)

        footer_text = QLabel(
            f"Darklightz Studio — Lead Generation Suite  v{APP_VERSION}  "
            "·  Developed by Darklightz Studio"
        )
        footer_text.setStyleSheet("color: #45475a; font-size: 10px;")
        fb_layout.addWidget(footer_text)
        fb_layout.addStretch()

        right.addWidget(footer_bar)

        right_widget = QWidget()
        right_widget.setLayout(right)
        root.addWidget(right_widget, 1)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _navigate(self, page_idx: int) -> None:
        self._stack.setCurrentIndex(page_idx)
        for i, btn in enumerate(self._nav_buttons):
            btn.set_active(i == page_idx)

        # Refresh data-bearing pages on navigation
        if page_idx == 0:
            self._dashboard.refresh()
        elif page_idx == 2:
            self._leads.refresh()

    # ------------------------------------------------------------------
    # Auto-update check on startup
    # ------------------------------------------------------------------

    def _maybe_check_updates_on_startup(self) -> None:
        from database import operations as db
        auto = db.get_setting("auto_update_check", "true")
        if auto != "true":
            return

        self._startup_worker = _StartupUpdateWorker()
        self._startup_worker.update_available.connect(self._on_startup_update)
        self._startup_worker.start()

    def _on_startup_update(self, version: str, url: str) -> None:
        reply = QMessageBox.information(
            self,
            "Update Available",
            f"Darklightz Lead Generator v{version} is available.\n\n"
            "Would you like to open the download page?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            webbrowser.open(url)

    # ------------------------------------------------------------------
    # Close event
    # ------------------------------------------------------------------

    def closeEvent(self, event: QCloseEvent) -> None:
        logger.info("Application closing.")
        event.accept()
