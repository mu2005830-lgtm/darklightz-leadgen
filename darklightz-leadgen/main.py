"""
Darklightz Studio — Lead Generation Suite v2.0
Entry point.

Run:
    python main.py

Or on Windows after building with build.bat:
    DarklightzLeadGenerator.exe
"""

import sys
import os

# ---------------------------------------------------------------------------
# Resolve the project root — works both as source and as a PyInstaller bundle
# ---------------------------------------------------------------------------
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)

# ---------------------------------------------------------------------------
# Logger — set up first so every subsequent step is captured
# ---------------------------------------------------------------------------
from utilities.logger import logger, log_path
logger.info("Application starting v2.0.0 — log: %s", log_path())

# ---------------------------------------------------------------------------
# Qt application object — created before any Qt widgets
# ---------------------------------------------------------------------------
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

app = QApplication(sys.argv)
app.setApplicationName("Darklightz Lead Generation Suite")
app.setApplicationDisplayName("Darklightz Studio — Lead Generation Suite")
app.setOrganizationName("Darklightz Studio")
app.setOrganizationDomain("darklightz.studio")
app.setApplicationVersion("2.0.0")

# HiDPI scaling (Windows 10/11 at 125 % / 150 % display scaling)
QApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)

# App icon
_icon_candidates = [
    os.path.join(BASE_DIR, "assets", "icon.ico"),
    os.path.join(BASE_DIR, "assets", "logo.png"),
]
for _icon_path in _icon_candidates:
    if os.path.exists(_icon_path):
        app.setWindowIcon(QIcon(_icon_path))
        logger.info("App icon loaded: %s", _icon_path)
        break

# ---------------------------------------------------------------------------
# Splash screen — shown immediately so the user sees something at once
# ---------------------------------------------------------------------------
from frontend.splash_screen import DarklightzSplash
from frontend.styles import DARK_THEME

app.setStyleSheet(DARK_THEME)

splash = DarklightzSplash()
splash.show()
app.processEvents()

# ---------------------------------------------------------------------------
# Database initialisation (while splash is visible)
# ---------------------------------------------------------------------------
from database.models import init_db
try:
    init_db()
    logger.info("Database initialised (v2.0 schema applied).")
except Exception as exc:
    logger.critical("Database init failed: %s", exc)

# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------
from frontend.main_window import MainWindow


def _excepthook(exc_type, exc_value, exc_tb):
    import traceback
    tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logger.critical("Unhandled exception:\n%s", tb_str)
    QMessageBox.critical(
        None,
        "Unexpected Error",
        f"An unexpected error occurred:\n\n{exc_value}\n\n"
        f"Details have been written to:\n{log_path()}",
    )


sys.excepthook = _excepthook


def main() -> int:
    window = MainWindow()
    splash.finish(window)
    window.show()
    logger.info("Main window shown.")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
