"""
PlayerPanel widget for displaying player information.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette, QFont
from ui.styles import PLAYER_COLORS, FONT_SIZE_MEDIUM, FONT_SIZE_SMALL, GROUP_BOX_STYLE


class PlayerInfoWidget(QFrame):
    """Widget for displaying a single player's information."""
    
    def __init__(self, player_id, player_name, is_ai, parent=None):
        super().__init__(parent)
        self.player_id = player_id
        self.player_name = player_name
        self.is_ai = is_ai
        
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(2)
        
        # Get player color
        if player_id < len(PLAYER_COLORS):
            color = PLAYER_COLORS[player_id + 1]
            self.player_color = QColor(color[0], color[1], color[2])
        else:
            self.player_color = QColor(128, 128, 128)
        
        # Set background color (light version)
        palette = self.palette()
        bg_color = QColor(
            min(255, self.player_color.red() + 200),
            min(255, self.player_color.green() + 200),
            min(255, self.player_color.blue() + 200)
        )
        palette.setColor(QPalette.ColorRole.Window, bg_color)
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI layout."""
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Player name and color indicator
        name_label = QLabel(self.player_name)
        name_font = QFont("Arial", FONT_SIZE_MEDIUM, QFont.Weight.Bold)
        name_label.setFont(name_font)
        name_label.setStyleSheet(f"color: rgb({self.player_color.red()}, {self.player_color.green()}, {self.player_color.blue()})")
        layout.addWidget(name_label)
        
        # AI indicator
        if self.is_ai:
            ai_label = QLabel("🤖 AI Player")
            ai_label.setFont(QFont("Arial", FONT_SIZE_SMALL))
            ai_label.setStyleSheet("color: rgb(100, 100, 200)")
            layout.addWidget(ai_label)
        else:
            manual_label = QLabel("👤 Manual Player")
            manual_label.setFont(QFont("Arial", FONT_SIZE_SMALL))
            manual_label.setStyleSheet("color: rgb(100, 200, 100)")
            layout.addWidget(manual_label)
        
        # Information labels
        self.soldiers_label = QLabel("Soldiers: 18")
        self.soldiers_label.setFont(QFont("Arial", FONT_SIZE_SMALL))
        layout.addWidget(self.soldiers_label)
        
        self.score_label = QLabel("Score: 0")
        self.score_label.setFont(QFont("Arial", FONT_SIZE_SMALL))
        layout.addWidget(self.score_label)
        
        # Win rate removed from player panel (now shown in map widget)
        
        self.priority_label = QLabel("Priority: --")
        self.priority_label.setFont(QFont("Arial", FONT_SIZE_SMALL))
        layout.addWidget(self.priority_label)
        
        self.setLayout(layout)
    
    def update_info(self, soldiers, score, winrate=None, priority=None):
        """Update player information."""
        self.soldiers_label.setText(f"Soldiers: {int(soldiers)}")
        self.score_label.setText(f"Score: {int(score)}")
        
        # Win rate removed - now shown in map widget
        
        if priority is not None:
            self.priority_label.setText(f"Priority: {int(priority)}")
    
    def set_active(self, active):
        """Highlight if this is the active player."""
        if active:
            self.setStyleSheet(f"""
                border: 3px solid rgb({self.player_color.red()}, {self.player_color.green()}, {self.player_color.blue()});
                border-radius: 5px;
            """)
        else:
            self.setStyleSheet("""
                border: 2px solid #d0d0d0;
                border-radius: 5px;
            """)


class PlayerPanel(QWidget):
    """Panel for displaying all players' information."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.player_widgets = {}
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI layout."""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        title = QLabel("Players")
        title_font = QFont("Arial", FONT_SIZE_MEDIUM, QFont.Weight.Bold)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Scroll area for players
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.players_container = QWidget()
        self.players_layout = QVBoxLayout()
        self.players_layout.setSpacing(10)
        self.players_layout.setContentsMargins(5, 5, 5, 5)
        self.players_container.setLayout(self.players_layout)
        
        scroll.setWidget(self.players_container)
        layout.addWidget(scroll)
        
        self.setLayout(layout)
    
    def set_players(self, player_names, which_ai):
        """Set the players to display."""
        # Clear existing widgets
        for widget in self.player_widgets.values():
            self.players_layout.removeWidget(widget)
            widget.deleteLater()
        self.player_widgets.clear()
        
        # Create new player widgets
        for i, name in enumerate(player_names):
            is_ai = i in which_ai
            widget = PlayerInfoWidget(i, name, is_ai)
            self.player_widgets[i] = widget
            self.players_layout.addWidget(widget)
        
        # Add stretch at the end
        self.players_layout.addStretch()
    
    def update_player(self, player_id, soldiers, score, winrate=None, priority=None):
        """Update a player's information."""
        if player_id in self.player_widgets:
            self.player_widgets[player_id].update_info(soldiers, score, winrate, priority)
    
    def set_active_player(self, player_id):
        """Set the active player."""
        for pid, widget in self.player_widgets.items():
            widget.set_active(pid == player_id)
    
    def update_all_players(self, game, winrates=None):
        """Update all players' information from game state."""
        if game is None:
            return
        
        for i in range(game.player_num):
            soldiers = game.players[i].soldiers
            score = game.pts[i] if hasattr(game, 'pts') else 0
            winrate = winrates[i] if winrates and i < len(winrates) else None
            priority = game.power_level[i] if hasattr(game, 'power_level') else None
            self.update_player(i, soldiers, score, winrate, priority)

