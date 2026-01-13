import numpy as np


edges = [[0, 1], [0, 7], [0, 8],
         [1, 7], [1, 4], [2, 5],
         [2, 9], [2, 6], [2, 10],
         [3, 6], [4, 5], [4, 7],
         [4, 9], [5, 9], [6, 10], [9, 10]]

class Game:
    def __init__(self, players, dice=0):
        self.player_num = len(players)
        self.players = players
        self.dice = dice
        self.reset()

    def reset(self):
        self.values = np.arange(11) + 2
        np.random.shuffle(self.values)
        self.v2p = {}
        for i in range(11):
            self.v2p[self.values[i]-2] = i

        self.net = np.zeros((11, 11))
        for e in edges:
            self.net[e[0], e[1]] = 1
            self.net[e[1], e[0]] = 1

        value_net = np.zeros((11, 11))
        for i in range(11):
            for j in range(i+1, 11):
                if self.values[i] < self.values[j]:
                    value_net[i][j] = 1
                else:
                    value_net[j][i] = 1
        
        self.net = self.net * value_net

        self.cnt = np.zeros((11, self.player_num))
        self.pts = np.zeros(self.player_num)
        self.remain_player = self.player_num
        self.power_level = np.zeros(self.player_num)
        for i in range(self.player_num):
            self.players[i].reset()

    def step(self, player_id, force_move=-1, by_search=False, search_result=None, verbose=False):
        if self.players[player_id].soldiers == 0:
            return None, False

        options = self.roll_dice()
        if self.dice == 1 and verbose:
            self.print_options(options)
        chosen_option, reroll = self.players[player_id].action(options, self.cnt, self.v2p, self.net, self.values, by_search, search_result, verbose, self.dice, True)

        if reroll:
            options = self.roll_dice()
            if self.dice == 1 and verbose:
                self.print_options(options)
            chosen_option, reroll = self.players[player_id].action(options, self.cnt, self.v2p, self.net, self.values, by_search, search_result, verbose, self.dice, False)

        if self.dice == 1:
            option = options[chosen_option]
            option[0] = self.v2p[option[0]]
        else:
            option = [chosen_option // 3, chosen_option % 3]

        if force_move != -1:
            self.cnt[force_move // 3, player_id] += min(force_move % 3 + 1, self.players[player_id].soldiers)
            self.players[player_id].soldiers -= min(force_move % 3 + 1, self.players[player_id].soldiers)
        else:
            self.cnt[option[0], player_id] += min(option[1] + 1, self.players[player_id].soldiers)
            self.players[player_id].soldiers -= min(option[1] + 1, self.players[player_id].soldiers)

        if self.players[player_id].soldiers == 0:
            self.power_level[player_id] = self.remain_player
            self.remain_player -= 1
        
        return option, True

    def roll_dice(self):
        dice = [np.random.randint(6) for i in range(3)]
        res = np.array([[dice[0] + dice[1], dice[2] // 2],
                        [dice[0] + dice[2], dice[1] // 2],
                        [dice[2] + dice[1], dice[0] // 2]])
        return res

    def get_current_score(self, final=False):
        loc_order = np.argsort(self.values)
        self_cnt = self.cnt.copy() + 0.1 * self.power_level.reshape(1, -1)

        self.pts = np.zeros(self.player_num)
        for loc in loc_order:
            state = self_cnt[loc]
            sorted_indices = np.argsort(state)[::-1]
            
            if state[sorted_indices[0]] >= 1:
                if final:
                    print(f'player {sorted_indices[0]} win on loc {loc} with value {self.values[loc]}, loc {loc} : {state}')
                self.pts[sorted_indices[0]] += self.values[loc]
                for i in range(11):
                    if self.net[loc, i] == 1 and self_cnt[i, sorted_indices[0]] >= 1:
                        self_cnt[i, sorted_indices[0]] += 2

            if state[sorted_indices[1]] >= 1:
                self.pts[sorted_indices[1]] += np.floor(self.values[loc] / 2)
        
        return self.pts

    def terminal(self):
        if self.remain_player == 0:
            return True
        return False

    def get_graph(self):
        net = np.eye(11) + self.net
        return net

    def print_options(self, options):
        for i in range(3):
            print(f"choice {i}: {options[i, 1] + 1:.0f} men -> land {options[i, 0] + 2:.0f}")
        print()