"""
Catppuccin Mocha-inspired dark QSS stylesheet for Darklightz Lead Generator v2.0.

v2.0: Added DangerButton and ExportButton object names.
"""

DARK_THEME = """
/* =====================================================================
   Global
   ===================================================================== */

QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #181825;
}

/* =====================================================================
   Sidebar / Nav
   ===================================================================== */

#Sidebar {
    background-color: #181825;
    border-right: 1px solid #313244;
    min-width: 200px;
    max-width: 220px;
}

#NavButton {
    background-color: transparent;
    color: #a6adc8;
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    text-align: left;
    font-size: 13px;
    margin: 2px 8px;
}

#NavButton:hover {
    background-color: #313244;
    color: #cdd6f4;
}

#NavButton[active="true"] {
    background-color: #313244;
    color: #cba6f7;
    font-weight: bold;
    border-left: 3px solid #cba6f7;
}

#AppTitle {
    color: #cba6f7;
    font-size: 16px;
    font-weight: bold;
    padding: 16px 14px 8px 14px;
}

#AppSubtitle {
    color: #6c7086;
    font-size: 10px;
    padding: 0px 14px 12px 14px;
}

#SidebarDivider {
    background-color: #313244;
    max-height: 1px;
    min-height: 1px;
    margin: 4px 12px;
}

/* =====================================================================
   Stat Cards (Dashboard)
   ===================================================================== */

#StatCard {
    background-color: #313244;
    border-radius: 10px;
    padding: 16px;
    border: 1px solid #45475a;
}

#StatValue {
    color: #cba6f7;
    font-size: 28px;
    font-weight: bold;
}

#StatLabel {
    color: #a6adc8;
    font-size: 11px;
}

/* =====================================================================
   Page Headers
   ===================================================================== */

#PageTitle {
    font-size: 20px;
    font-weight: bold;
    color: #cdd6f4;
    padding-bottom: 4px;
}

#PageSubtitle {
    font-size: 12px;
    color: #6c7086;
    padding-bottom: 12px;
}

/* =====================================================================
   Buttons
   ===================================================================== */

QPushButton {
    background-color: #cba6f7;
    color: #1e1e2e;
    border: none;
    border-radius: 7px;
    padding: 8px 20px;
    font-size: 13px;
    font-weight: bold;
    min-height: 34px;
}

QPushButton:hover {
    background-color: #d4b5f8;
}

QPushButton:pressed {
    background-color: #b891f5;
}

QPushButton:disabled {
    background-color: #45475a;
    color: #6c7086;
}

QPushButton#SecondaryButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
}

QPushButton#SecondaryButton:hover {
    background-color: #45475a;
    color: #cdd6f4;
}

QPushButton#DangerButton {
    background-color: #f38ba8;
    color: #1e1e2e;
}

QPushButton#DangerButton:hover {
    background-color: #f5a3b8;
}

QPushButton#ExportButton {
    background-color: #89b4fa;
    color: #1e1e2e;
    padding: 6px 16px;
    font-size: 12px;
}

QPushButton#ExportButton:hover {
    background-color: #9fc0fb;
}

QPushButton#StopButton {
    background-color: #f38ba8;
    color: #1e1e2e;
}

QPushButton#StopButton:hover {
    background-color: #f5a3b8;
}

/* =====================================================================
   Form inputs
   ===================================================================== */

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: #cba6f7;
    selection-color: #1e1e2e;
    min-height: 32px;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #cba6f7;
}

QSpinBox {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 32px;
}

QSpinBox:focus {
    border: 1px solid #cba6f7;
}

QSpinBox::up-button, QSpinBox::down-button {
    background-color: #45475a;
    border: none;
    width: 18px;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #585b70;
}

/* =====================================================================
   ComboBox
   ===================================================================== */

QComboBox {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 12px;
    min-height: 32px;
}

QComboBox:focus {
    border: 1px solid #cba6f7;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    selection-background-color: #45475a;
}

/* =====================================================================
   CheckBox
   ===================================================================== */

QCheckBox {
    spacing: 8px;
    color: #cdd6f4;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #45475a;
    background-color: #313244;
}

QCheckBox::indicator:checked {
    background-color: #cba6f7;
    border-color: #cba6f7;
}

/* =====================================================================
   GroupBox
   ===================================================================== */

QGroupBox {
    border: 1px solid #313244;
    border-radius: 8px;
    margin-top: 14px;
    padding: 12px 16px;
    color: #a6adc8;
    font-size: 12px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #cba6f7;
    font-weight: bold;
}

/* =====================================================================
   Table
   ===================================================================== */

QTableWidget {
    background-color: #1e1e2e;
    alternate-background-color: #181825;
    gridline-color: #313244;
    border: 1px solid #313244;
    border-radius: 8px;
    selection-background-color: #45475a;
    selection-color: #cdd6f4;
    font-size: 12px;
}

QTableWidget::item {
    padding: 6px 8px;
    border: none;
}

QTableWidget::item:selected {
    background-color: #45475a;
    color: #cdd6f4;
}

QHeaderView::section {
    background-color: #181825;
    color: #a6adc8;
    padding: 8px 10px;
    border: none;
    border-right: 1px solid #313244;
    border-bottom: 1px solid #313244;
    font-weight: bold;
    font-size: 11px;
}

QHeaderView::section:hover {
    background-color: #313244;
    color: #cdd6f4;
    cursor: pointer;
}

QHeaderView::section:checked {
    background-color: #313244;
    color: #cba6f7;
}

/* =====================================================================
   Progress Bar
   ===================================================================== */

QProgressBar {
    background-color: #313244;
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
    color: #cdd6f4;
    font-size: 10px;
}

QProgressBar::chunk {
    background-color: #cba6f7;
    border-radius: 4px;
}

/* =====================================================================
   ScrollArea / ScrollBar
   ===================================================================== */

QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background-color: #1e1e2e;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #45475a;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #585b70;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background-color: #1e1e2e;
    height: 8px;
}

QScrollBar::handle:horizontal {
    background-color: #45475a;
    border-radius: 4px;
    min-width: 20px;
}

/* =====================================================================
   Status Bar
   ===================================================================== */

QStatusBar {
    background-color: #181825;
    color: #6c7086;
    font-size: 11px;
    border-top: 1px solid #313244;
}

/* =====================================================================
   Log / TextEdit (search progress)
   ===================================================================== */

QTextEdit#LogView {
    background-color: #11111b;
    color: #a6adc8;
    border: 1px solid #313244;
    border-radius: 6px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 11px;
    padding: 8px;
}

/* =====================================================================
   Dialog
   ===================================================================== */

QDialog {
    background-color: #1e1e2e;
}

QDialogButtonBox QPushButton {
    min-width: 80px;
}

/* =====================================================================
   Label helpers
   ===================================================================== */

#FormLabel {
    color: #a6adc8;
    font-size: 12px;
    font-weight: bold;
}

/* =====================================================================
   Context Menu
   ===================================================================== */

QMenu {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 8px;
    padding: 4px;
}

QMenu::item {
    padding: 7px 20px;
    border-radius: 5px;
    margin: 1px;
}

QMenu::item:selected {
    background-color: #45475a;
    color: #cdd6f4;
}

QMenu::separator {
    height: 1px;
    background-color: #45475a;
    margin: 4px 8px;
}
"""


STATUS_COLOURS = {
    "New":            "#cba6f7",   # purple
    "Contacted":      "#89b4fa",   # blue
    "Follow-up":      "#fab387",   # peach
    "Interested":     "#a6e3a1",   # green
    "Closed":         "#a6adc8",   # grey
    "Not Interested": "#f38ba8",   # red
}

LEAD_TYPE_COLOURS = {
    "No Website":          "#f38ba8",
    "No Online Presence":  "#fab387",
    "Facebook Only":       "#89b4fa",
    "Instagram Only":      "#f2cdcd",
    "WhatsApp Only":       "#a6e3a1",
    "Social Only":         "#f9e2af",
}
