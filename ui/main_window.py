"""
MainWindow for the game UI application.
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QMenuBar, QStatusBar, QMessageBox, QApplication)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QFont
from ui.map_widget import MapWidget
from ui.player_panel import PlayerPanel
from ui.dice_widget import DiceWidget
from ui.action_panel import ActionPanel
from ui.game_controller import GameController
from ui.setup_dialog import SetupDialog
from utils.player import Player
import torch
import multiprocessing as mp


class GameThread(QThread):
    """Thread for running AI game steps."""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, controller, player_id):
        super().__init__()
        self.controller = controller
        self.player_id = player_id
    
    def run(self):
        """Run the AI action."""
        try:
            self.controller.take_ai_action(self.player_id)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.controller = GameController()
        self.game_thread = None
        self.setup_ui()
        self.connect_signals()
        
        # Show setup dialog on startup
        self.show_setup_dialog()
    
    def setup_ui(self):
        """Set up the UI."""
        self.setWindowTitle("天下鸣动 - Game Simulator")
        self.setMinimumSize(1200, 800)
        
        # Apply global styling
        from ui.styles import BACKGROUND_COLOR, GROUP_BOX_STYLE, BUTTON_STYLE, BUTTON_SECONDARY_STYLE
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {BACKGROUND_COLOR};
            }}
            {GROUP_BOX_STYLE}
            {BUTTON_STYLE}
        """)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Left side: Map
        self.map_widget = MapWidget()
        self.map_widget.set_region_click_callback(self.on_region_clicked)
        main_layout.addWidget(self.map_widget, 2)
        
        # Right side: Control panels (two columns)
        right_container = QWidget()
        right_main_layout = QHBoxLayout()
        right_main_layout.setSpacing(10)
        right_main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Left column: Winrate panel (above) and Player panel (below)
        left_column = QWidget()
        left_column_layout = QVBoxLayout()
        left_column_layout.setSpacing(5)
        left_column_layout.setContentsMargins(0, 0, 0, 0)
        
        from ui.winrate_panel import WinRatePanel
        self.winrate_panel = WinRatePanel()
        left_column_layout.addWidget(self.winrate_panel)
        
        self.player_panel = PlayerPanel()
        left_column_layout.addWidget(self.player_panel, 1)
        
        left_column.setLayout(left_column_layout)
        right_main_layout.addWidget(left_column, 1)
        
        # Right column: Dice, Actions, Log (tight layout)
        right_column = QWidget()
        right_column_layout = QVBoxLayout()
        right_column_layout.setSpacing(3)
        right_column_layout.setContentsMargins(0, 0, 0, 0)
        
        # Dice widget
        self.dice_widget = DiceWidget()
        right_column_layout.addWidget(self.dice_widget)
        
        # Action panel
        self.action_panel = ActionPanel()
        self.action_panel.set_action_callback(self.on_action_selected)
        self.action_panel.set_reroll_callback(self.on_reroll_requested)
        right_column_layout.addWidget(self.action_panel)
        
        right_column.setLayout(right_column_layout)
        right_main_layout.addWidget(right_column, 1)
        
        right_container.setLayout(right_main_layout)
        right_container.setMaximumWidth(500)
        main_layout.addWidget(right_container, 1)
        
        central_widget.setLayout(main_layout)
        
        # Menu bar
        self.create_menu_bar()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        
        # Game menu
        game_menu = menubar.addMenu("Game")
        
        new_game_action = QAction("New Game", self)
        new_game_action.setShortcut("Ctrl+N")
        new_game_action.triggered.connect(self.show_setup_dialog)
        game_menu.addAction(new_game_action)
        
        reset_action = QAction("Reset Game", self)
        reset_action.setShortcut("Ctrl+R")
        reset_action.triggered.connect(self.reset_game)
        game_menu.addAction(reset_action)
        
        game_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        game_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def connect_signals(self):
        """Connect controller signals to UI updates."""
        self.controller.game_state_changed.connect(self.on_game_state_changed)
        self.controller.turn_changed.connect(self.on_turn_changed)
        self.controller.action_taken.connect(self.on_action_taken)
        self.controller.game_ended.connect(self.on_game_ended)
        self.controller.winrate_updated.connect(self.on_winrate_updated)
        self.controller.dice_rolled.connect(self.on_dice_rolled)
        self.controller.action_options_updated.connect(self.on_action_options_updated)
    
    def show_setup_dialog(self):
        """Show the setup dialog and initialize game."""
        dialog = SetupDialog(self)
        if dialog.exec():
            config = dialog.get_config()
            self.initialize_game(config)
    
    def initialize_game(self, config):
        """Initialize the game with configuration."""
        try:
            # Load model
            model_name = f'./model_offline/{config["stage"]}-{config["n_players"]}/{config["model_config"]["model_dir"]}/best_model.pth'
            
            # Create players
            players = []
            for i in range(config["n_players"]):
                if i in config["which_ai"]:
                    player_type = 'agent'
                else:
                    player_type = 'manual'
                
                player = Player(
                    player_type=player_type,
                    player_num=config["n_players"],
                    model_config=config["model_config"],
                    player_id=i
                )
                
                player.model.load_state_dict(torch.load(model_name))
                player.epsilon = 0.0
                player.random = False
                player.model.eval()
                
                players.append(player)
            
            # Initialize controller
            self.controller.initialize_game(
                players=players,
                player_names=config["player_names"],
                which_ai=config["which_ai"],
                dice_mode=config["dice_mode"],
                search_time=config.get("search_time", 8.0)
            )
            
            # Update UI
            self.player_panel.set_players(config["player_names"], config["which_ai"])
            if hasattr(self, 'winrate_panel'):
                self.winrate_panel.update_winrates(None, None, False, config["player_names"])
            # Clear action log when starting new game
            self.action_panel.clear_log()
            self.update_all_displays()
            
            # Start first turn
            self.controller.step_turn()
            
            self.status_bar.showMessage("Game started")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to initialize game: {str(e)}")
    
    def reset_game(self):
        """Reset the current game."""
        if self.controller.game:
            self.controller.reset_game()
            self.update_all_displays()
            self.controller.step_turn()
            self.status_bar.showMessage("Game reset")
    
    def update_all_displays(self):
        """Update all UI displays."""
        game = self.controller.get_game_state()
        if game:
            # Update scores before displaying
            game.pts = game.get_current_score()
            
            # Update map
            self.map_widget.update_game_state(
                game, 
                self.controller.player_names,
                self.controller.highlight_region if hasattr(self.controller, 'highlight_region') else None,
                self.controller.highlight_player if hasattr(self.controller, 'highlight_player') else None,
                self.controller.last_move_region if hasattr(self.controller, 'last_move_region') else {},
                self.controller.current_winrates if hasattr(self.controller, 'current_winrates') else None,
                getattr(self.controller, 'last_search_times', None),
                getattr(self.controller, '_calculating_winrate', False),
                getattr(self.controller, 'node_winners', None)
            )
            
            # Update player panel
            self.player_panel.update_all_players(game)
    
    def on_game_state_changed(self, game, player_names):
        """Handle game state change."""
        self.update_all_displays()
    
    def on_turn_changed(self, player_id):
        """Handle turn change."""
        if not self.controller.game:
            return
        
        player_name = self.controller.player_names[player_id] if player_id < len(self.controller.player_names) else f"Player {player_id+1}"
        is_ai = self.controller.is_ai_player(player_id)
        
        # Update action panel
        self.action_panel.set_current_player(player_id, is_ai, player_name)
        
        # Update player panel
        self.player_panel.set_active_player(player_id)
        
        # Update status bar
        self.status_bar.showMessage(f"{player_name}'s turn")
        
        # If manual player, roll dice and show options
        if not is_ai and self.controller.game.players[player_id].soldiers > 0:
            options = self.controller.roll_dice_for_player(player_id)
            if options is not None:
                self.action_panel.set_options(options.tolist(), True)  # Always dice mode
        
        # If AI player, start AI action in thread
        if is_ai:
            self.start_ai_action(player_id)
    
    def start_ai_action(self, player_id):
        """Start AI action in separate thread."""
        if self.game_thread and self.game_thread.isRunning():
            return
        
        self.game_thread = GameThread(self.controller, player_id)
        self.game_thread.finished.connect(lambda: self.on_ai_action_finished(player_id))
        self.game_thread.error.connect(self.on_ai_error)
        self.game_thread.start()
    
    def on_ai_action_finished(self, player_id):
        """Handle AI action completion."""
        # Advance to next turn (current_player_id was already advanced in take_ai_action)
        QApplication.processEvents()  # Process any pending events
        self.controller.step_turn()
    
    def on_ai_error(self, error_msg):
        """Handle AI action error."""
        QMessageBox.warning(self, "AI Error", f"Error during AI action: {error_msg}")
    
    def on_action_taken(self, player_id, action_region, soldiers, dice_result):
        """Handle action taken."""
        # Log the action
        player_name = self.controller.player_names[player_id] if player_id < len(self.controller.player_names) else f"Player {player_id+1}"
        is_ai = self.controller.is_ai_player(player_id)
        
        # Get region value for display
        if self.controller.game and action_region >= 0 and action_region < len(self.controller.game.values):
            region_value = int(self.controller.game.values[action_region])
            log_text = f"{player_name} sent {int(soldiers)} soldiers to Region {region_value}"
            if is_ai:
                # Add AI search times (average per move)
                ai_search_times = getattr(self.controller, 'last_ai_search_times', None)
                if ai_search_times is not None and ai_search_times > 0:
                    log_text += f" (AI, {int(ai_search_times)} searches)"
                else:
                    log_text += " (AI)"
            self.action_panel.log_action(log_text, player_id)
    
    def on_game_ended(self, final_scores):
        """Handle game end."""
        msg = "Game Over!\n\nFinal Scores:\n"
        for i, score in enumerate(final_scores):
            name = self.controller.player_names[i] if i < len(self.controller.player_names) else f"Player {i+1}"
            msg += f"{name}: {int(score)}\n"
        
        QMessageBox.information(self, "Game Over", msg)
        self.status_bar.showMessage("Game ended")
    
    def on_winrate_calculating(self):
        """Handle winrate calculation start."""
        # Update winrate panel to show calculating
        self.winrate_panel.update_winrates(
            None, 
            None, 
            calculating=True,
            player_names=self.controller.player_names
        )
        # Update map to show calculating indicator
        self.update_all_displays()
    
    def on_winrate_updated(self, winrates, search_count):
        """Handle winrate update."""
        # Update winrate panel
        self.winrate_panel.update_winrates(
            winrates,
            search_count,
            calculating=False,
            player_names=self.controller.player_names
        )
        
        # Update all players with winrates (without winrate in player panel)
        if self.controller.game:
            for i in range(self.controller.game.player_num):
                winrate = winrates[i] if i < len(winrates) else None
                self.player_panel.update_player(
                    i,
                    self.controller.game.players[i].soldiers,
                    self.controller.game.pts[i],
                    winrate,
                    self.controller.game.power_level[i] if hasattr(self.controller.game, 'power_level') else None
                )
        
        # Update AI status for current player
        current_player = self.controller.get_current_player()
        if current_player < len(winrates):
            self.action_panel.update_ai_status(winrates, search_count)
        
        # Update map with win rates and search times
        self.update_all_displays()
    
    def on_dice_rolled(self, dice_result):
        """Handle dice roll."""
        # Use the actual dice values stored in controller
        if self.controller.current_dice_values:
            self.dice_widget.roll_dice(self.controller.current_dice_values)
        else:
            # Fallback: extract from options (approximate)
            import random
            values = [random.randint(1, 6) for _ in range(3)]
            self.dice_widget.roll_dice(values)
    
    def on_action_options_updated(self, options):
        """Handle action options update."""
        self.action_panel.set_options(options, self.controller.game.dice == 1)
        self.dice_widget.set_options(options)
    
    def on_action_selected(self, action_index):
        """Handle manual action selection."""
        current_player = self.controller.get_current_player()
        if not self.controller.is_ai_player(current_player):
            # Take manual action (dice already rolled in on_turn_changed)
            success = self.controller.take_manual_action(current_player, action_index, False)
            if success:
                # Advance to next turn (current_player_id was already advanced in take_manual_action)
                QApplication.processEvents()
                self.controller.step_turn()
    
    def on_reroll_requested(self):
        """Handle reroll request."""
        current_player = self.controller.get_current_player()
        if not self.controller.is_ai_player(current_player):
            # Trigger reroll
            success = self.controller.reroll_dice_for_player(current_player)
            if success:
                # Update UI with new options (dice animation handled by dice_rolled signal)
                if self.controller.current_options is not None:
                    options = self.controller.current_options.tolist()
                    self.action_panel.set_options(options, self.controller.game.dice == 1)
                    # Note: dice_rolled signal is emitted by reroll_dice_for_player,
                    # which triggers on_dice_rolled() to animate with correct values
            else:
                # Reroll failed (already used or not allowed)
                from PyQt6.QtWidgets import QMessageBox
                if self.controller.has_rerolled:
                    QMessageBox.information(self, "Reroll", "You can only reroll once per turn.")
                else:
                    QMessageBox.information(self, "Reroll", "Reroll is not available.")
    
    def on_region_clicked(self, region_id):
        """Handle region click."""
        # This could be used for manual region selection in non-dice mode
        pass
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About",
            "天下鸣动 Game Simulator\n\n"
            "A PyQt6-based desktop application for playing and simulating the 天下鸣动 game."
        )
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.game_thread and self.game_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Game Running",
                "A game is currently running. Are you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        
        event.accept()

