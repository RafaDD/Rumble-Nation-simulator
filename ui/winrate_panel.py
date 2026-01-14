"""
WinRatePanel for displaying AI estimated win rates.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from ui.styles import FONT_SIZE_MEDIUM, FONT_SIZE_SMALL, PLAYER_COLORS, GROUP_BOX_STYLE


class WinRatePanel(QWidget):
    """Panel for displaying AI estimated win rates."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.winrates = None
        self.search_times = None
        self.calculating = False
        self.player_names = []
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI layout."""
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.group = QGroupBox("AI Win Rates")
        group_layout = QVBoxLayout()
        group_layout.setSpacing(5)
        group_layout.setContentsMargins(10, 10, 10, 10)
        
        self.winrate_labels = []
        self.status_label = QLabel("Waiting for calculation...")
        self.status_label.setFont(QFont("Arial", FONT_SIZE_SMALL))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        group_layout.addWidget(self.status_label)
        
        self.group.setLayout(group_layout)
        layout.addWidget(self.group)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Apply styling
        self.setStyleSheet(f"{GROUP_BOX_STYLE}")
    
    def update_winrates(self, winrates, search_times=None, calculating=False, player_names=None):
        """Update win rates display."""
        self.winrates = winrates
        self.search_times = search_times
        self.calculating = calculating
        if player_names is not None:
            self.player_names = player_names
        
        group_layout = self.group.layout()
        
        # Clear existing labels
        for label in self.winrate_labels:
            group_layout.removeWidget(label)
            label.deleteLater()
        self.winrate_labels.clear()
        
        if calculating:
            self.status_label.setText("Calculating Win Rates...")
            self.status_label.setVisible(True)
        elif winrates is not None and len(winrates) > 0:
            self.status_label.setVisible(False)
            
            # Create labels for each player
            for i, winrate_val in enumerate(winrates):
                player_name = self.player_names[i] if i < len(self.player_names) else f"P{i+1}"
                label = QLabel(f"{player_name}: {winrate_val*100:.2f}%")
                label.setFont(QFont("Arial", FONT_SIZE_SMALL))
                
                # Color code by player
                if i < len(PLAYER_COLORS):
                    color = PLAYER_COLORS[i + 1]
                    label.setStyleSheet(f"color: rgb({color[0]}, {color[1]}, {color[2]});")
                
                group_layout.addWidget(label)
                self.winrate_labels.append(label)
            
            # Add search times at bottom
            if search_times is not None and search_times > 0:
                search_label = QLabel(f"Searches: {int(search_times)}")
                search_label.setFont(QFont("Arial", FONT_SIZE_SMALL - 2))
                search_label.setStyleSheet("color: rgb(100, 100, 100);")
                group_layout.addWidget(search_label)
                self.winrate_labels.append(search_label)
        else:
            self.status_label.setText("No win rates available")
            self.status_label.setVisible(True)

