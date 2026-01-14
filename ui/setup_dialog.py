"""
SetupDialog for game configuration.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton, 
                             QGroupBox, QMessageBox, QComboBox, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from utils.check_models import find_best
from ui.styles import (BUTTON_STYLE, BUTTON_SECONDARY_STYLE, GROUP_BOX_STYLE, 
                      LINE_EDIT_STYLE, SPIN_BOX_STYLE, CHECK_BOX_STYLE,
                      BACKGROUND_COLOR)
import os


class SetupDialog(QDialog):
    """Dialog for configuring game settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Game Setup")
        self.setMinimumWidth(400)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {BACKGROUND_COLOR};
            }}
            {GROUP_BOX_STYLE}
            {BUTTON_STYLE}
            {BUTTON_SECONDARY_STYLE}
            {LINE_EDIT_STYLE}
            {SPIN_BOX_STYLE}
            {CHECK_BOX_STYLE}
        """)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI layout."""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Model stage
        stage_layout = QHBoxLayout()
        stage_label = QLabel("Model Stage:")
        stage_label.setMinimumWidth(120)
        self.stage_spinbox = QSpinBox()
        self.stage_spinbox.setMinimum(0)
        self.stage_spinbox.setMaximum(10)
        self.stage_spinbox.setValue(0)
        stage_layout.addWidget(stage_label)
        stage_layout.addWidget(self.stage_spinbox)
        layout.addLayout(stage_layout)
        
        # Number of players
        players_layout = QHBoxLayout()
        players_label = QLabel("Number of Players:")
        players_label.setMinimumWidth(120)
        self.players_spinbox = QSpinBox()
        self.players_spinbox.setMinimum(2)
        self.players_spinbox.setMaximum(10)
        self.players_spinbox.setValue(3)
        self.players_spinbox.valueChanged.connect(self.on_player_count_changed)
        players_layout.addWidget(players_label)
        players_layout.addWidget(self.players_spinbox)
        layout.addLayout(players_layout)
        
        # Dice mode - always enabled (fixed to dice mode)
        # Removed checkbox, game is always in dice mode
        
        # AI search time
        search_time_layout = QHBoxLayout()
        search_time_label = QLabel("AI Search Time (s):")
        search_time_label.setMinimumWidth(120)
        self.search_time_spinbox = QDoubleSpinBox()
        self.search_time_spinbox.setMinimum(0.1)
        self.search_time_spinbox.setMaximum(60.0)
        self.search_time_spinbox.setSingleStep(0.5)
        self.search_time_spinbox.setValue(8.0)
        self.search_time_spinbox.setDecimals(1)
        search_time_layout.addWidget(search_time_label)
        search_time_layout.addWidget(self.search_time_spinbox)
        layout.addLayout(search_time_layout)
        
        # Player names and AI selection
        self.player_group = QGroupBox("Players")
        self.player_layout = QVBoxLayout()
        self.player_widgets = []
        self.setup_player_widgets(3)
        self.player_group.setLayout(self.player_layout)
        layout.addWidget(self.player_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet(BUTTON_SECONDARY_STYLE)
        self.cancel_button.clicked.connect(self.reject)
        self.start_button = QPushButton("Start Game")
        self.start_button.clicked.connect(self.validate_and_accept)
        self.start_button.setDefault(True)
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(self.start_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def setup_player_widgets(self, count):
        """Set up player name and AI selection widgets."""
        # Clear existing widgets
        for widget_data in self.player_widgets:
            widget = widget_data['widget']
            self.player_layout.removeWidget(widget)
            widget.deleteLater()
        self.player_widgets.clear()
        
        # Create new widgets
        for i in range(count):
            player_layout = QHBoxLayout()
            
            name_label = QLabel(f"Player {i+1}:")
            name_label.setMinimumWidth(80)
            name_edit = QLineEdit()
            name_edit.setPlaceholderText(f"Player {i+1}")
            name_edit.setText(f"Player {i+1}")
            
            ai_checkbox = QCheckBox("AI")
            ai_checkbox.setChecked(i == 0)  # First player is AI by default
            
            player_layout.addWidget(name_label)
            player_layout.addWidget(name_edit)
            player_layout.addWidget(ai_checkbox)
            
            widget = QWidget()
            widget.setLayout(player_layout)
            self.player_widgets.append({
                'widget': widget,
                'name_edit': name_edit,
                'ai_checkbox': ai_checkbox
            })
            self.player_layout.addWidget(widget)
    
    def on_player_count_changed(self, value):
        """Handle player count change."""
        self.setup_player_widgets(value)
    
    def validate_and_accept(self):
        """Validate inputs and accept the dialog."""
        # Get values
        stage = self.stage_spinbox.value()
        n_players = self.players_spinbox.value()
        
        # Get player names
        player_names = []
        which_ai = []
        
        for i, widget_data in enumerate(self.player_widgets):
            name = widget_data['name_edit'].text().strip()
            if not name:
                name = f"Player {i+1}"
            player_names.append(name)
            
            if widget_data['ai_checkbox'].isChecked():
                which_ai.append(i)
        
        # Validate model exists
        try:
            best_model_config = find_best(stage, n_players)
            if best_model_config.empty:
                QMessageBox.warning(
                    self, 
                    "Model Not Found", 
                    f"No model found for stage {stage} with {n_players} players."
                )
                return
            
            model_dir = best_model_config.loc[0]["model_dir"]
            model_path = f'./model_offline/{stage}-{n_players}/{model_dir}/best_model.pth'
            
            if not os.path.exists(model_path):
                QMessageBox.warning(
                    self,
                    "Model File Not Found",
                    f"Model file not found at: {model_path}"
                )
                return
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error loading model: {str(e)}"
            )
            return
        
        # Store results
        self.stage = stage
        self.n_players = n_players
        self.dice_mode = 1  # Always dice mode (fixed)
        self.player_names = player_names
        self.which_ai = which_ai
        self.model_config = best_model_config.loc[0]
        self.search_time = self.search_time_spinbox.value()
        
        self.accept()
    
    def get_config(self):
        """Get the configuration."""
        return {
            'stage': self.stage,
            'n_players': self.n_players,
            'dice_mode': self.dice_mode,
            'player_names': self.player_names,
            'which_ai': self.which_ai,
            'model_config': self.model_config,
            'search_time': self.search_time
        }

