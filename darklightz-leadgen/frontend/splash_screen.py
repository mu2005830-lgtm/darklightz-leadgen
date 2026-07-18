"""
Splash screen — shown for 2–3 seconds on startup.

v2.0: Version number updated to 2.0.0.
"""

from __future__ import annotations

import os
import sys

from PyQt6.QtWidgets import QSplashScreen, QApplication
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QLinearGradient, QPen
from PyQt6.QtCore import Qt, QRect, QTimer

if getattr(sys, "frozen", False):
    _BASE = sys._MEIPASS
else:
    _BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_LOGO_PATH = os.path.join(_BASE, "assets", "logo.png")

APP_VERSION = "2.0.0"
BUILD_DATE  = "2025"


def _load_logo(target_width: int = 180) -> QPixmap | None:
    if not os.path.exists(_LOGO_PATH):
        return None
    pix = QPixmap(_LOGO_PATH)
    if pix.isNull():
        return None
    return pix.scaledToWidth(target_width, Qt.TransformationMode.SmoothTransformation)


def _render_splash(width: int = 560, height: int = 340) -> QPixmap:
    canvas = QPixmap(width, height)
    canvas.fill(Qt.GlobalColor.transparent)

    p = QPainter(canvas)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

    # Background gradient
    grad = QLinearGradient(0, 0, 0, height)
    grad.setColorAt(0.0, QColor("#1e1e2e"))
    grad.setColorAt(1.0, QColor("#11111b"))
    p.fillRect(0, 0, width, height, grad)

    # Border
    pen = QPen(QColor("#313244"), 1)
    p.setPen(pen)
    p.drawRect(0, 0, width - 1, height - 1)

    # Accent line
    accent = QLinearGradient(0, 0, width, 0)
    accent.setColorAt(0.0, QColor("#1e1e2e"))
    accent.setColorAt(0.4, QColor("#cba6f7"))
    accent.setColorAt(0.6, QColor("#89b4fa"))
    accent.setColorAt(1.0, QColor("#1e1e2e"))
    p.fillRect(0, 0, width, 3, accent)

    cy = 36

    # Logo
    logo = _load_logo(target_width=130)
    if logo:
        lx = (width - logo.width()) // 2
        p.drawPixmap(lx, cy, logo)
        cy += logo.height() + 20
    else:
        p.setPen(QColor("#cba6f7"))
        f = QFont("Arial", 52, QFont.Weight.Bold)
        p.setFont(f)
        p.drawText(QRect(0, cy, width, 70), Qt.AlignmentFlag.AlignHCenter, "DL")
        cy += 80

    # Studio name
    p.setPen(QColor("#cdd6f4"))
    f = QFont("Segoe UI", 20, QFont.Weight.Bold)
    f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 3)
    p.setFont(f)
    p.drawText(QRect(0, cy, width, 32), Qt.AlignmentFlag.AlignHCenter, "DARKLIGHTZ STUDIO")
    cy += 34

    # Tagline
    p.setPen(QColor("#a6adc8"))
    f2 = QFont("Segoe UI", 11)
    p.setFont(f2)
    p.drawText(
        QRect(0, cy, width, 24),
        Qt.AlignmentFlag.AlignHCenter,
        "Professional Lead Generation Suite",
    )
    cy += 32

    # Divider
    p.setPen(QPen(QColor("#313244"), 1))
    margin = 60
    p.drawLine(margin, cy, width - margin, cy)
    cy += 16

    # Developer
    p.setPen(QColor("#6c7086"))
    f3 = QFont("Segoe UI", 9)
    p.setFont(f3)
    p.drawText(
        QRect(0, cy, width, 20),
        Qt.AlignmentFlag.AlignHCenter,
        "Developed by Darklightz Studio",
    )
    cy += 20

    # Version
    p.setPen(QColor("#45475a"))
    f4 = QFont("Segoe UI", 8)
    p.setFont(f4)
    p.drawText(
        QRect(0, cy, width, 20),
        Qt.AlignmentFlag.AlignHCenter,
        f"Version {APP_VERSION}  ·  {BUILD_DATE}",
    )

    p.end()
    return canvas


class DarklightzSplash(QSplashScreen):
    def __init__(self):
        pixmap = _render_splash()
        super().__init__(pixmap, Qt.WindowType.WindowStaysOnTopHint)
        self.setMask(pixmap.mask())

    def mousePressEvent(self, event) -> None:
        pass  # Prevent clicking away the splash
