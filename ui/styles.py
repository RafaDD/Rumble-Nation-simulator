"""
Styling constants and utilities for the UI.
"""

# Player colors matching play.py (BGR to RGB conversion)
PLAYER_COLORS = [
    (220, 40, 40),      # Rich Red
    (90, 60, 230),      # Electric Blue
    (230, 50, 90),      # Vivid Rose
    (255, 110, 0),      # Bold Orange
    (40, 160, 240),     # Strong Sky Blue
    (160, 60, 10),      # Strong Brown
    (90, 200, 10),      # Sharp Olive
    (40, 220, 120),     # Fresh Green
    (0, 200, 200),      # Deep Teal
    (20, 200, 20),      # Vivid Green
]

# Map region positions (x, y) for displaying region values
# Adjusted positions: moved top-right nodes (2, 3, 6) lower to avoid edge crossings
REGION_POSITIONS = [
    (110, 216),   # 0
    (216, 222),   # 1
    (580, 320),   # 2 - moved down from 181
    (720, 140),   # 3 - moved down from 105
    (339, 308),   # 4
    (458, 306),   # 5 - middle right
    (690, 260),   # 6 - moved down from 228
    (148, 409),   # 7
    (60, 570),    # 8
    (367, 474),   # 9
    (559, 522),   # 10
]

# UI styling constants
FONT_FAMILY = "Arial"
FONT_SIZE_LARGE = 14
FONT_SIZE_MEDIUM = 12
FONT_SIZE_SMALL = 10

# Window dimensions
MAP_WIDTH = 800
MAP_HEIGHT = 700
PANEL_WIDTH = 300

# Modern color scheme
BACKGROUND_COLOR = "#f5f5f5"
PANEL_BACKGROUND = "#ffffff"
BORDER_COLOR = "#d0d0d0"
ACCENT_COLOR = "#4a90e2"
TEXT_COLOR = "#333333"
TEXT_COLOR_LIGHT = "#666666"

# Button styles
BUTTON_STYLE = """
    QPushButton {
        background-color: #4a90e2;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: bold;
        min-height: 24px;
    }
    QPushButton:hover {
        background-color: #357abd;
    }
    QPushButton:pressed {
        background-color: #2a5f8f;
    }
    QPushButton:disabled {
        background-color: #cccccc;
        color: #888888;
    }
"""

BUTTON_SECONDARY_STYLE = """
    QPushButton {
        background-color: #6c757d;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: bold;
        min-height: 24px;
    }
    QPushButton:hover {
        background-color: #5a6268;
    }
    QPushButton:pressed {
        background-color: #484f54;
    }
"""

# Group box style
GROUP_BOX_STYLE = """
    QGroupBox {
        font-weight: bold;
        border: 2px solid #d0d0d0;
        border-radius: 5px;
        margin-top: 10px;
        padding-top: 10px;
        background-color: #ffffff;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
    }
"""

# Line edit style
LINE_EDIT_STYLE = """
    QLineEdit {
        border: 1px solid #d0d0d0;
        border-radius: 3px;
        padding: 5px;
        background-color: white;
    }
    QLineEdit:focus {
        border: 2px solid #4a90e2;
    }
"""

# Spin box style
SPIN_BOX_STYLE = """
    QSpinBox {
        border: 1px solid #d0d0d0;
        border-radius: 3px;
        padding: 5px;
        background-color: white;
    }
    QSpinBox:focus {
        border: 2px solid #4a90e2;
    }
"""

# Check box style
CHECK_BOX_STYLE = """
    QCheckBox {
        spacing: 5px;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border: 2px solid #d0d0d0;
        border-radius: 3px;
        background-color: white;
    }
    QCheckBox::indicator:checked {
        background-color: #4a90e2;
        border-color: #4a90e2;
    }
    QCheckBox::indicator:hover {
        border-color: #4a90e2;
    }
"""

