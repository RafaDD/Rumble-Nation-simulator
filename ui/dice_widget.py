"""
DiceWidget for visual dice representation and rolling animations.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from ui.styles import GROUP_BOX_STYLE
import random


class SingleDiceWidget(QWidget):
    """Widget for displaying a single die."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 1
        self.is_rolling = False
        self._rotation = 0  # Use private attribute to avoid recursion
        self.setMinimumSize(60, 60)
        self.setMaximumSize(60, 60)
    
    def set_value(self, value):
        """Set the dice value (1-6)."""
        self.value = max(1, min(6, int(value)))
        self.update()
    
    def set_rolling(self, rolling):
        """Set rolling animation state."""
        self.is_rolling = rolling
        if rolling:
            self.start_animation()
        self.update()
    
    def start_animation(self):
        """Start rolling animation."""
        self.animation = QPropertyAnimation(self, b"rotation")
        self.animation.setDuration(500)
        self.animation.setStartValue(0)
        self.animation.setEndValue(360)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.setLoopCount(-1)  # Infinite loop while rolling
        self.animation.start()
    
    def get_rotation(self):
        return self._rotation
    
    def set_rotation(self, value):
        self._rotation = value
        self.update()
    
    rotation = pyqtProperty(int, get_rotation, set_rotation)
    
    def paintEvent(self, event):
        """Paint the die."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw die background
        if self.is_rolling:
            # Random value while rolling
            display_value = random.randint(1, 6)
        else:
            display_value = self.value
        
        # Die background
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawRoundedRect(5, 5, 50, 50, 5, 5)
        
        # Draw dots
        dot_color = QColor(0, 0, 0)
        dot_size = 8
        
        if display_value == 1:
            self.draw_dot(painter, 30, 30, dot_size, dot_color)
        elif display_value == 2:
            self.draw_dot(painter, 20, 20, dot_size, dot_color)
            self.draw_dot(painter, 40, 40, dot_size, dot_color)
        elif display_value == 3:
            self.draw_dot(painter, 20, 20, dot_size, dot_color)
            self.draw_dot(painter, 30, 30, dot_size, dot_color)
            self.draw_dot(painter, 40, 40, dot_size, dot_color)
        elif display_value == 4:
            self.draw_dot(painter, 20, 20, dot_size, dot_color)
            self.draw_dot(painter, 40, 20, dot_size, dot_color)
            self.draw_dot(painter, 20, 40, dot_size, dot_color)
            self.draw_dot(painter, 40, 40, dot_size, dot_color)
        elif display_value == 5:
            self.draw_dot(painter, 20, 20, dot_size, dot_color)
            self.draw_dot(painter, 40, 20, dot_size, dot_color)
            self.draw_dot(painter, 30, 30, dot_size, dot_color)
            self.draw_dot(painter, 20, 40, dot_size, dot_color)
            self.draw_dot(painter, 40, 40, dot_size, dot_color)
        elif display_value == 6:
            self.draw_dot(painter, 20, 15, dot_size, dot_color)
            self.draw_dot(painter, 20, 30, dot_size, dot_color)
            self.draw_dot(painter, 20, 45, dot_size, dot_color)
            self.draw_dot(painter, 40, 15, dot_size, dot_color)
            self.draw_dot(painter, 40, 30, dot_size, dot_color)
            self.draw_dot(painter, 40, 45, dot_size, dot_color)
    
    def draw_dot(self, painter, x, y, size, color):
        """Draw a single dot on the die."""
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(x - size//2, y - size//2, size, size)


class DiceWidget(QWidget):
    """Widget for displaying three dice and action options."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dice_values = [1, 1, 1]
        self.options = None
        self.is_rolling = False
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI layout."""
        layout = QVBoxLayout()
        layout.setSpacing(3)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        title = QLabel("Dice")
        title_font = QFont("Arial", 12, QFont.Weight.Bold)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Dice container
        dice_layout = QHBoxLayout()
        dice_layout.setSpacing(15)
        
        self.dice1 = SingleDiceWidget()
        self.dice2 = SingleDiceWidget()
        self.dice3 = SingleDiceWidget()
        
        dice_layout.addWidget(self.dice1)
        dice_layout.addWidget(self.dice2)
        dice_layout.addWidget(self.dice3)
        dice_layout.addStretch()
        
        layout.addLayout(dice_layout)
        
        self.setLayout(layout)
        
        # Apply styling
        self.setStyleSheet(f"""
            {GROUP_BOX_STYLE}
        """)
    
    def roll_dice(self, values=None):
        """Roll the dice with animation."""
        if values is None:
            values = [random.randint(1, 6) for _ in range(3)]
        
        self.is_rolling = True
        self.dice1.set_rolling(True)
        self.dice2.set_rolling(True)
        self.dice3.set_rolling(True)
        
        # Stop rolling after animation
        QTimer.singleShot(500, lambda: self.finish_roll(values))
    
    def finish_roll(self, values):
        """Finish the dice roll animation."""
        self.dice_values = values
        self.is_rolling = False
        self.dice1.set_rolling(False)
        self.dice2.set_rolling(False)
        self.dice3.set_rolling(False)
        
        self.dice1.set_value(values[0])
        self.dice2.set_value(values[1])
        self.dice3.set_value(values[2])
    
    def set_options(self, options):
        """Set and display action options based on dice results."""
        self.options = options
        # Options text removed - will be shown on buttons in action panel
    
    def get_dice_values(self):
        """Get current dice values."""
        return self.dice_values.copy()

