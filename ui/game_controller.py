"""
GameController to manage game state and coordinate between game logic and UI.
"""

from PyQt6.QtCore import QObject, pyqtSignal, QThread
from utils.game import Game
from utils.player import Player
import numpy as np
import torch
import multiprocessing as mp
from functools import partial
from copy import deepcopy
import time


class GameController(QObject):
    """Controller for managing game state and UI updates."""
    
    # Signals for UI updates
    game_state_changed = pyqtSignal(object, list)  # game, player_names
    turn_changed = pyqtSignal(int)  # current_player_id
    action_taken = pyqtSignal(int, int, int, list)  # player_id, action_region, soldiers, dice_result
    game_ended = pyqtSignal(list)  # final_scores
    winrate_updated = pyqtSignal(list, int)  # winrates, search_count
    winrate_calculating = pyqtSignal()  # Signal when starting winrate calculation
    dice_rolled = pyqtSignal(list)  # dice_result
    action_options_updated = pyqtSignal(list)  # options
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.game = None
        self.player_names = []
        self.which_ai = []
        self.current_player_id = 0
        self.is_running = False
        self.search_time = 2.0
        self.current_options = None  # Store current dice options
        self.current_dice_values = None  # Store actual dice values (0-5, representing 1-6)
        self.has_rerolled = False  # Track if reroll has been used this turn
        self.last_move_region = {}  # Track last moved region for each player {player_id: region_id}
        self.current_winrates = None  # Store current win rates for all players
        self.last_search_times = None  # Store last search times (for judge)
        self.last_ai_search_times = None  # Store last AI player search times (average per move)
        self._calculating_winrate = False  # Flag for winrate calculation
        self.node_winners = None  # Store winning player for each node
        
    def initialize_game(self, players, player_names, which_ai, dice_mode, search_time=8.0):
        """Initialize the game with players."""
        self.game = Game(players=players, dice=dice_mode)
        self.player_names = player_names
        self.which_ai = which_ai
        self.current_player_id = 0
        self.is_running = True
        self.search_time = search_time  # Set AI search time
        self.game.reset()
        self.game_state_changed.emit(self.game, self.player_names)
    
    def reset_game(self):
        """Reset the game to initial state."""
        if self.game:
            self.game.reset()
            self.current_player_id = 0
            # Update node winners after reset
            self.node_winners = self.game.get_node_winners()
            self.game_state_changed.emit(self.game, self.player_names)
    
    def get_current_player(self):
        """Get the current player."""
        if self.game:
            return self.current_player_id % self.game.player_num
        return 0
    
    def is_ai_player(self, player_id):
        """Check if a player is AI."""
        return player_id in self.which_ai
    
    @staticmethod
    def simulate(game, player_id, search_time, action):
        """Simulate game for search."""
        points = []
        cnt = 0
        t1 = time.time()
        n_players = game.player_num
        while True:
            game_sim = deepcopy(game)
            for i in range(n_players):
                game_sim.players[i].player_type = 'agent'
            
            if action != -1:
                game_sim.step(player_id, action)
            idx = (player_id + 1) % n_players
            
            while True:
                game_sim.step(idx)
                idx = (idx + 1) % n_players
                flag = game_sim.terminal()
                if flag:
                    break
            score = game_sim.get_current_score()
            points.append(score)
            cnt += 1
            t = time.time()
            if (t - t1) >= search_time:
                break
        return np.array(points), cnt
    
    def search(self, game, player_id, search_time):
        """Search for best action."""
        with mp.Pool(processes=5) as pool:
            func = partial(GameController.simulate, game, player_id, search_time)
            result = pool.map(func, range(33))
        
        sim_points, search_times = zip(*result)
        
        res = []
        for points in sim_points:
            rank = np.argsort(points, axis=1)[:, -1]
            res.append(np.where(rank == player_id)[0].shape[0] / rank.shape[0])
        
        search_times = np.array(search_times)
        res = np.array(res)
        
        return res, search_times
    
    def judge(self, game, player_id, search_time):
        """Judge current game state."""
        with mp.Pool(processes=5) as pool:
            func = partial(GameController.simulate, game, player_id, search_time)
            result = pool.map(func, [-1] * 5)
        
        sim_points, search_times = zip(*result)
        sim_points = np.concatenate(sim_points, axis=0)
        search_times = np.sum(search_times)
        
        ranking = np.argsort(sim_points, axis=1)[:, -1]
        winrate = []
        for i in range(game.player_num):
            winrate.append(np.where(ranking == i)[0].shape[0] / ranking.shape[0])
        
        return winrate, search_times
    
    def take_ai_action(self, player_id):
        """Take action for AI player."""
        if not self.game or player_id not in self.which_ai:
            return False
        
        if self.game.players[player_id].soldiers == 0:
            return False
        
        # Set all players to random except current
        for k in range(self.game.player_num):
            self.game.players[k].random = True
        self.game.players[player_id].random = False
        
        # Search for best action
        search_result, search_times = self.search(self.game, player_id, self.search_time)
        
        # Store average search time per move (for action log)
        self.last_ai_search_times = np.mean(search_times) if len(search_times) > 0 else 0
        
        # Take action
        p, success = self.game.step(
            player_id=player_id, 
            by_search=True, 
            search_result=search_result, 
            verbose=False
        )
        
        if success:
            # Store soldiers before action (already executed, so we need to estimate)
            # The action has been executed, so we can't get exact value
            # Use option[1] + 1 as estimate
            action_region = p[0] if p is not None and len(p) > 0 else -1
            soldiers_deployed = p[1] + 1 if p is not None and len(p) > 1 else 1
            self.last_move_region[player_id] = action_region  # Track moved region
            self.action_taken.emit(player_id, action_region, soldiers_deployed, [])
            
            # Calculate winrates with loading indicator
            self._calculating_winrate = True
            self.winrate_calculating.emit()
            winrate, search_times_judge = self.judge(self.game, player_id, self.search_time)
            self.current_winrates = winrate  # Store win rates
            self.last_search_times = int(search_times_judge)
            self._calculating_winrate = False
            self.winrate_updated.emit(winrate, int(search_times_judge))
            
            # Update node winners after move
            if self.game:
                self.node_winners = self.game.get_node_winners()
            
            self.game_state_changed.emit(self.game, self.player_names)
            
            # Advance to next player after action is complete
            self.current_player_id += 1
            return True
        return False
    
    def roll_dice_for_player(self, player_id):
        """Roll dice and return options for a player."""
        if not self.game:
            return None
        
        # Use game's roll_dice function
        options = self.game.roll_dice()
        
        # Get dice values from game (stored after roll_dice call)
        if self.game.last_dice_values:
            self.current_dice_values = [d + 1 for d in self.game.last_dice_values]  # Convert 0-5 to 1-6
        else:
            self.current_dice_values = None
        
        self.current_options = options  # Store for later use
        self.has_rerolled = False  # Reset reroll flag for new turn
        self.dice_rolled.emit(options.tolist())
        self.action_options_updated.emit(options.tolist())
        return options
    
    def reroll_dice_for_player(self, player_id):
        """Reroll dice for a manual player."""
        if not self.game or player_id in self.which_ai:
            return False
        
        if self.game.players[player_id].soldiers == 0:
            return False
        
        # Only allow reroll once per turn (always dice mode)
        if self.has_rerolled:
            return False
        
        # Use game's roll_dice function
        options = self.game.roll_dice()
        
        # Get dice values from game (stored after roll_dice call)
        if self.game.last_dice_values:
            self.current_dice_values = [d + 1 for d in self.game.last_dice_values]  # Convert 0-5 to 1-6
        else:
            self.current_dice_values = None
        
        self.current_options = options  # Store for later use
        self.has_rerolled = True  # Mark reroll as used
        self.dice_rolled.emit(options.tolist())
        self.action_options_updated.emit(options.tolist())
        return True
    
    def take_manual_action(self, player_id, action_index, reroll=False):
        """Take action for manual player."""
        if not self.game or player_id in self.which_ai:
            return False
        
        if self.game.players[player_id].soldiers == 0:
            return False
        
        # Get the stored options (should be set by roll_dice_for_player)
        if self.current_options is None:
            # Fallback: use game's roll_dice if not set
            options = self.game.roll_dice()
            self.current_options = options
            if self.game.last_dice_values:
                self.current_dice_values = [d + 1 for d in self.game.last_dice_values]
            else:
                self.current_dice_values = None
        else:
            options = self.current_options
        
        # Always dice mode: action_index is 0, 1, or 2
        if action_index < 0 or action_index >= 3:
            return False
        
        chosen_option = action_index
        option = options[chosen_option].copy()
        # option[0] is dice[0] + dice[1] (0-10), which represents region value - 2
        # Convert region value to region index using v2p (same as game.step does)
        option[0] = self.game.v2p[option[0]]
        
        # Store soldiers before action
        soldiers_before = self.game.players[player_id].soldiers
        
        # Execute the action
        soldiers_to_deploy = min(option[1] + 1, self.game.players[player_id].soldiers)
        self.game.cnt[option[0], player_id] += soldiers_to_deploy
        self.game.players[player_id].soldiers -= soldiers_to_deploy
        
        if self.game.players[player_id].soldiers == 0:
            self.game.power_level[player_id] = self.game.remain_player
            self.game.remain_player -= 1
        
        # Calculate soldiers deployed
        soldiers_deployed = int(soldiers_before - self.game.players[player_id].soldiers)
        
        # Track moved region
        self.last_move_region[player_id] = option[0]
        self.action_taken.emit(player_id, option[0], soldiers_deployed, options.tolist())
        self.current_options = None  # Clear after use
        self.current_dice_values = None  # Clear dice values
        self.has_rerolled = False  # Reset reroll flag for next turn
        
        # Calculate winrates after manual action with loading indicator
        self._calculating_winrate = True
        self.winrate_calculating.emit()
        winrate, search_times_judge = self.judge(self.game, player_id, self.search_time)
        self.current_winrates = winrate  # Store win rates
        self.last_search_times = int(search_times_judge)
        self._calculating_winrate = False
        self.winrate_updated.emit(winrate, int(search_times_judge))
        
        # Update node winners after move
        if self.game:
            self.node_winners = self.game.get_node_winners()
        
        self.game_state_changed.emit(self.game, self.player_names)
        
        # Advance to next player after action is complete
        self.current_player_id += 1
        return True
    
    def step_turn(self):
        """Advance to next turn."""
        if not self.game:
            return False
        
        # Check if game ended
        if self.game.terminal():
            final_pts = self.game.get_current_score(final=True)
            self.game_ended.emit(final_pts.tolist())
            self.is_running = False
            return False
        
        player_id = self.get_current_player()
        
        # Skip players with no soldiers
        while self.game.players[player_id].soldiers == 0:
            self.current_player_id += 1
            player_id = self.get_current_player()
            if self.game.terminal():
                final_pts = self.game.get_current_score(final=True)
                self.game_ended.emit(final_pts.tolist())
                self.is_running = False
                return False
        
        if player_id in self.which_ai:
            # AI player - emit turn changed, action will be taken in thread
            self.turn_changed.emit(player_id)
            return True
        else:
            # Manual player - wait for input
            self.turn_changed.emit(player_id)
            return True
    
    def get_game_state(self):
        """Get current game state."""
        return self.game
    
    def get_scores(self):
        """Get current scores."""
        if self.game:
            return self.game.get_current_score()
        return None

