"""
MapWidget for displaying the game map with custom graph visualization.
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPoint, QRect
from PyQt6.QtGui import QPainter, QFont, QColor, QPen, QBrush
import numpy as np
from ui.styles import PLAYER_COLORS, REGION_POSITIONS, FONT_SIZE_MEDIUM, FONT_SIZE_SMALL
import math

# Graph edges from game.py
EDGES = [[0, 1], [0, 7], [0, 8],
         [1, 7], [1, 4], [2, 5],
         [2, 9], [2, 6], [2, 10],
         [3, 6], [4, 5], [4, 7],
         [4, 9], [5, 9], [6, 10], [9, 10]]


class MapWidget(QWidget):
    """Widget for displaying the game map with custom graph visualization."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.game_state = None
        self.player_names = []
        self.highlight_region = None
        self.highlight_player = None
        self.selected_region = None
        self.region_click_callback = None
        self.last_move_regions = {}  # Track last moved regions per player {player_id: region_id}
        self.node_winners = None  # Store winning player for each node
        
        # Set minimum size
        self.setMinimumSize(800, 700)
        self.setStyleSheet("background-color: #f0f0f0;")
        
    def update_game_state(self, game, player_names, highlight_region=None, highlight_player=None, last_move_regions=None, winrates=None, search_times=None, calculating_winrate=False, node_winners=None):
        """Update the displayed game state."""
        self.game_state = game
        self.player_names = player_names
        self.highlight_region = highlight_region
        self.highlight_player = highlight_player
        if last_move_regions is not None:
            self.last_move_regions = last_move_regions
        if node_winners is not None:
            self.node_winners = node_winners
        # winrates, search_times, calculating_winrate are now handled by WinRatePanel, not displayed here
        self.update()
    
    def set_region_click_callback(self, callback):
        """Set callback for region clicks."""
        self.region_click_callback = callback
    
    def mousePressEvent(self, event):
        """Handle mouse clicks on regions."""
        if event.button() == Qt.MouseButton.LeftButton and self.region_click_callback:
            # Check if click is near any region
            click_pos = event.position().toPoint()
            for i, pos in enumerate(REGION_POSITIONS):
                # Check if click is within node area
                node_rect = self.get_node_rect(i)
                if node_rect.contains(click_pos):
                    self.region_click_callback(i)
                    break
    
    def get_node_rect(self, idx):
        """Get the rectangle for a node."""
        pos = REGION_POSITIONS[idx]
        node_width = 80
        node_height = 60 + self.game_state.player_num * 18 if self.game_state else 60
        return QRect(pos[0] - node_width // 2, pos[1] - node_height // 2, node_width, node_height)
    
    def get_edge_path(self, start_idx, end_idx):
        """Calculate edge path that avoids crossing nodes."""
        start_pos = REGION_POSITIONS[start_idx]
        end_pos = REGION_POSITIONS[end_idx]
        
        # Calculate direction vector
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist == 0:
            return [start_pos, end_pos]
        
        # Normalize
        dx /= dist
        dy /= dist
        
        # Offset from node centers to avoid crossing
        offset = 45
        
        # Start and end points on node boundaries
        start_point = QPoint(
            int(start_pos[0] + dx * offset),
            int(start_pos[1] + dy * offset)
        )
        end_point = QPoint(
            int(end_pos[0] - dx * offset),
            int(end_pos[1] - dy * offset)
        )
        
        return [start_point, end_point]
    
    def paintEvent(self, event):
        """Paint the custom graph map."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor(245, 245, 245))
        
        if self.game_state is None:
            # Draw placeholder
            painter.setPen(QColor(100, 100, 100))
            painter.setFont(QFont("Arial", 16))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Waiting for game to start...")
            return
        
        # Get game state data
        values = self.game_state.values
        cnt = self.game_state.cnt
        player_num = self.game_state.player_num
        
        # Draw edges first (so nodes appear on top)
        edge_pen = QPen(QColor(180, 180, 180), 1.5)
        painter.setPen(edge_pen)
        
        for edge in EDGES:
            if len(edge) == 2:
                start_idx, end_idx = edge[0], edge[1]
                if start_idx < len(REGION_POSITIONS) and end_idx < len(REGION_POSITIONS):
                    path = self.get_edge_path(start_idx, end_idx)
                    if len(path) == 2:
                        painter.drawLine(path[0], path[1])
        
        # Draw nodes (regions) as tables
        font_header = QFont("Arial", FONT_SIZE_MEDIUM, QFont.Weight.Bold)
        font_small = QFont("Arial", FONT_SIZE_SMALL - 2)
        
        for idx, pos in enumerate(REGION_POSITIONS):
            value = int(values[idx])
            
            # Determine node color based on winning player (from check result)
            winning_player = None
            if self.node_winners is not None and idx < len(self.node_winners):
                if self.node_winners[idx] >= 0:
                    winning_player = int(self.node_winners[idx])
            
            # Fallback to controlling player if no winner determined yet
            if winning_player is None:
                max_soldiers = 0
                for p_idx in range(player_num):
                    if cnt[idx, p_idx] > max_soldiers:
                        max_soldiers = cnt[idx, p_idx]
                        winning_player = p_idx
            
            # Node dimensions
            node_width = 80
            node_height = 40 + player_num * 18
            node_rect = QRect(pos[0] - node_width // 2, pos[1] - node_height // 2, 
                            node_width, node_height)
            
            # Draw node background - more transparent based on winning player
            if winning_player is not None and winning_player < len(PLAYER_COLORS):
                color = PLAYER_COLORS[winning_player + 1]
                node_color = QColor(color[0], color[1], color[2], 120)  # More transparent (was 200)
            else:
                node_color = QColor(240, 240, 240, 180)  # More transparent (was 240)
            
            # Highlight if selected
            if self.highlight_region == idx:
                border_pen = QPen(QColor(255, 255, 0), 3)  # Yellow highlight
            else:
                border_pen = QPen(QColor(100, 100, 100), 2)
            
            # Draw node background
            painter.setBrush(QBrush(node_color))
            painter.setPen(border_pen)
            painter.drawRoundedRect(node_rect, 5, 5)
            
            # Draw header with value
            header_rect = QRect(node_rect.x(), node_rect.y(), node_rect.width(), 25)
            painter.fillRect(header_rect, QColor(255, 255, 255, 0))
            painter.setPen(QColor(0, 0, 0))
            painter.setFont(font_header)
            value_text = f"Value: {value}"
            text_rect = painter.fontMetrics().boundingRect(value_text)
            painter.drawText(header_rect.x() + (header_rect.width() - text_rect.width()) // 2,
                           header_rect.y() + text_rect.height() + 2, value_text)
            
            # Draw table rows for each player
            row_height = 18
            y_offset = header_rect.bottom() + 2
            
            for player_idx in range(player_num):
                soldier_count = int(cnt[idx, player_idx])
                
                # Row background (alternating for readability)
                row_rect = QRect(node_rect.x() + 2, y_offset, node_rect.width() - 4, row_height)
                if player_idx % 2 == 0:
                    painter.fillRect(row_rect, QColor(255, 255, 255, 150))
                else:
                    painter.fillRect(row_rect, QColor(240, 240, 240, 150))
                
                # Get player color
                if player_idx < len(PLAYER_COLORS):
                    color = PLAYER_COLORS[player_idx + 1]
                    text_color = QColor(color[0], color[1], color[2])
                else:
                    text_color = QColor(128, 128, 128)
                
                # Highlight if this is the highlighted region/player
                if self.highlight_region == idx and self.highlight_player == player_idx:
                    painter.setPen(QPen(QColor(255, 255, 0), 2))
                    painter.drawRect(row_rect)
                else:
                    painter.setPen(Qt.PenStyle.NoPen)
                
                # Draw player name and count
                if player_idx < len(self.player_names):
                    name = self.player_names[player_idx]  # Shorten name
                else:
                    name = f"P{player_idx+1}"
                
                painter.setPen(text_color)
                painter.setFont(font_small)
                text = f"{name}: {soldier_count}"
                painter.drawText(row_rect.x() + 3, row_rect.y() + row_rect.height() - 3, text)
                
                y_offset += row_height
        
        # Draw scores at top-left (larger, more prominent)
        # Always calculate current scores
        if hasattr(self.game_state, 'get_current_score'):
            current_scores = self.game_state.get_current_score()
        elif hasattr(self.game_state, 'pts'):
            current_scores = self.game_state.pts
        else:
            current_scores = np.zeros(player_num)
        
        # Score panel background - always white, never changes
        # Reset brush to white to ensure background doesn't change
        score_bg = QColor(255, 255, 255, 255)  # Fully opaque white
        painter.setBrush(QBrush(score_bg))  # Explicitly set brush to white
        score_width = 220
        score_height = player_num * 30 + 30
        score_rect = QRect(10, 10, score_width, score_height)
        # Fill with white background
        painter.fillRect(score_rect, score_bg)
        # Draw border
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.drawRect(score_rect)
        
        # Title
        painter.setPen(QColor(0, 0, 0))
        painter.setFont(QFont("Arial", FONT_SIZE_MEDIUM, QFont.Weight.Bold))
        painter.drawText(score_rect.x() + 10, score_rect.y() + 20, "Current Scores")
        
        # Scores
        font_score = QFont("Arial", FONT_SIZE_SMALL, QFont.Weight.Bold)
        painter.setFont(font_score)
        y_pos = score_rect.y() + 40
        
        for i in range(player_num):
            score_val = int(current_scores[i]) if i < len(current_scores) else 0
            if i < len(self.player_names):
                text = f"{self.player_names[i]}: {score_val}"
            else:
                text = f"P{i+1}: {score_val}"
            
            if i < len(PLAYER_COLORS):
                color = PLAYER_COLORS[i + 1]
                painter.setPen(QColor(color[0], color[1], color[2]))
            else:
                painter.setPen(QColor(128, 128, 128))
            
            painter.drawText(score_rect.x() + 15, y_pos, text)
            y_pos += 28
