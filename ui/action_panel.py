"""
ActionPanel for manual player interactions and AI action display.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QGroupBox, QProgressBar, QTextEdit)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from ui.styles import (FONT_SIZE_MEDIUM, FONT_SIZE_SMALL, BUTTON_STYLE, 
                      BUTTON_SECONDARY_STYLE, GROUP_BOX_STYLE, PLAYER_COLORS)


class ActionPanel(QWidget):
    """Panel for displaying actions and player interactions."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_player_id = None
        self.is_ai_player = False
        self.action_callback = None
        self.reroll_callback = None
        self.options = None
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI layout."""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        self.title_label = QLabel("Actions")
        title_font = QFont("Arial", FONT_SIZE_MEDIUM, QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        layout.addWidget(self.title_label)
        
        # Status label
        self.status_label = QLabel("Waiting for game to start...")
        self.status_label.setWordWrap(True)
        self.status_label.setFont(QFont("Arial", FONT_SIZE_SMALL))
        layout.addWidget(self.status_label)
        
        # Manual player controls
        self.manual_group = QGroupBox("Your Turn")
        manual_layout = QVBoxLayout()
        
        # Action buttons (text will be on buttons)
        self.action_buttons_layout = QVBoxLayout()
        self.action_buttons = []
        manual_layout.addLayout(self.action_buttons_layout)
        
        # Reroll button
        self.reroll_button = QPushButton("Reroll Dice")
        self.reroll_button.setStyleSheet(BUTTON_SECONDARY_STYLE)
        self.reroll_button.clicked.connect(self.on_reroll)
        manual_layout.addWidget(self.reroll_button)
        
        self.manual_group.setLayout(manual_layout)
        self.manual_group.setVisible(False)
        layout.addWidget(self.manual_group)
        
        # AI player display
        self.ai_group = QGroupBox("AI Thinking")
        ai_layout = QVBoxLayout()
        
        self.ai_status_label = QLabel("AI is thinking...")
        self.ai_status_label.setWordWrap(True)
        ai_layout.addWidget(self.ai_status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        ai_layout.addWidget(self.progress_bar)
        
        # Win Rate and Searches removed - now shown in WinRatePanel
        
        self.ai_group.setLayout(ai_layout)
        self.ai_group.setVisible(False)
        layout.addWidget(self.ai_group)
        
        # Action log
        self.log_group = QGroupBox("Action Log")
        log_layout = QVBoxLayout()
        log_layout.setSpacing(2)
        log_layout.setContentsMargins(5, 5, 5, 5)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        # self.log_text.setMinimumHeight(150)
        self.log_text.setMaximumHeight(400)
        log_layout.addWidget(self.log_text)
        self.log_group.setLayout(log_layout)
        layout.addWidget(self.log_group)
        
        self.setLayout(layout)
        
        # Apply styling
        self.setStyleSheet(f"""
            {GROUP_BOX_STYLE}
            QProgressBar {{
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: #4a90e2;
                border-radius: 2px;
            }}
            QTextEdit {{
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                background-color: white;
                font-family: 'Courier New', monospace;
                font-size: 9pt;
                font-weight: bold;
                padding: 5px;
            }}
        """)
    
    def set_action_callback(self, callback):
        """Set callback for action selection."""
        self.action_callback = callback
    
    def set_reroll_callback(self, callback):
        """Set callback for reroll."""
        self.reroll_callback = callback
    
    def set_current_player(self, player_id, is_ai, player_name):
        """Set the current active player."""
        self.current_player_id = player_id
        self.is_ai_player = is_ai
        
        if is_ai:
            self.manual_group.setVisible(False)
            self.ai_group.setVisible(True)
            self.status_label.setText(f"{player_name} (AI) is thinking...")
            self.ai_status_label.setText(f"{player_name} is analyzing the game state...")
        else:
            self.manual_group.setVisible(True)
            self.ai_group.setVisible(False)
            self.status_label.setText(f"{player_name}'s turn")
            self.clear_action_buttons()
    
    def set_options(self, options, dice_mode=True):
        """Set available action options."""
        self.options = options
        self.clear_action_buttons()
        
        if not self.is_ai_player and options:
            # Always dice mode - show 3 options
            if len(options) >= 3:
                # Dice mode: 3 options - text on buttons
                # options[i][0] is dice[0] + dice[1] (0-10), represents region value - 2
                # options[i][1] is dice[2] // 2 (0-2), represents soldiers - 1
                for i in range(3):
                    opt = options[i]
                    # Display: region value = option[0] + 2, soldiers = option[1] + 1
                    men = int(opt[1]) + 1  # 1-3 soldiers
                    land_value = int(opt[0]) + 2  # Region value 2-12
                    button = QPushButton(f"Choice {i}: {men} soldiers → Region {land_value}")
                    button.setStyleSheet(BUTTON_STYLE)
                    button.clicked.connect(lambda checked, idx=i: self.on_action_selected(idx))
                    self.action_buttons.append(button)
                    self.action_buttons_layout.addWidget(button)
    
    def clear_action_buttons(self):
        """Clear action buttons."""
        for button in self.action_buttons:
            self.action_buttons_layout.removeWidget(button)
            button.deleteLater()
        self.action_buttons.clear()
    
    def on_action_selected(self, action_index):
        """Handle action selection."""
        if self.action_callback:
            self.action_callback(action_index)
    
    def on_reroll(self):
        """Handle reroll request."""
        if self.reroll_callback:
            self.reroll_callback()
    
    def update_ai_status(self, winrates=None, search_count=None, action=None):
        """Update AI player status."""
        # Win Rate and Searches removed - now shown in WinRatePanel
        pass
    
    def log_action(self, message, player_id=None):
        """Add message to action log with player color."""
        if player_id is not None and (player_id + 1) < len(PLAYER_COLORS):
            color = PLAYER_COLORS[player_id + 1]  # Colors are indexed starting at 1
            # Format message with HTML color and bold, with spacing
            colored_message = f'<span style="color: rgb({color[0]}, {color[1]}, {color[2]}); font-weight: bold;">{message}</span><br>'
            self.log_text.append(colored_message)
        else:
            # Add bold and spacing for non-colored messages
            bold_message = f'<span style="font-weight: bold;">{message}</span><br>'
            self.log_text.append(bold_message)
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_log(self):
        """Clear the action log."""
        self.log_text.clear()
    

