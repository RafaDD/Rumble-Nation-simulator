import numpy as np
import torch
from utils.model import Transformer_model

class Player:
    def __init__(self, player_type, model_config=None, player_num=3, player_id=0, log_file=None):
        self.soldiers = 18
        self.id = player_id
        self.player_type = player_type
        self.log_file = log_file
        self.player_num = player_num
        if self.player_type == 'agent' or self.player_type == 'manual':
            self.epsilon = 0.2
            self.random = False
            self.model = Transformer_model(player_num=player_num,
                                           embed_dim=model_config["embed_dim"],
                                           nlayers=model_config["nlayer"],
                                           gcn=model_config["gcn"]).cuda()
            self.buffer_s = []
            self.threshold = 0.8
            self.all_prob = []
            for i in range(6):
                for j in range(6):
                    for k in range(6):
                        tmp = []
                        tmp.append((i + j) * 3 + k // 2)
                        tmp.append((i + k) * 3 + j // 2)
                        tmp.append((j + k) * 3 + i // 2)
                        self.all_prob.append(tmp)

    def action(self, options, state, v2p, net, values, by_serach=False, search_result=None, verbose=False, dice=0, can_reroll=True):

        if self.player_type == 'random':
            action_space = 33 if dice == 0 else 3
            return np.random.randint(action_space), False

        elif self.player_type == 'agent':
            s = torch.from_numpy(state).cuda().float().reshape(-1, 11)
            indices = [self.id] + [i for i in range(self.player_num) if i != self.id]
            s = s[indices].reshape(-1)

            v = torch.from_numpy(values).cuda().float()
            network = torch.from_numpy(net + np.eye(11)).cuda().float()
            self.buffer_s.append(torch.cat([s.cpu(), v.cpu()]).numpy())

            if dice == 1:
                ops = [int(v2p[options[i, 0]] * 3 + min(options[i, 1], self.soldiers - 1)) for i in range(3)]

                if self.random and np.random.rand() < self.epsilon:
                    action = np.random.randint(3)

                if by_serach:
                    action = np.argmax(search_result[ops])
                    reroll, thresh = self.check_reroll(search_result, ops)
                    
                    if verbose:
                        print(f"Player {self.id + 1} : Max win rate : {np.max(search_result):.3f}, Chosen win rate : {np.max(search_result[ops]):.3f}, Reroll threshold : {thresh:.3f}, Reroll : {reroll}")

                    return action, reroll

                out = self.model(torch.cat([s, v], dim=-1), network).detach().cpu().numpy()
                reroll, thresh = self.check_reroll(out, ops)
                action = np.argmax(out[ops])

                return action, reroll
            
            else:
                if self.random and np.random.rand() < self.epsilon:
                    action = np.random.randint(33)
                    if by_serach and verbose:
                        print(f"Player {self.id + 1} : Use random, Max win rate : {np.max(search_result):.3f}, Chosen win rate : {search_result[action]:.3f}")
                    return action, False

                if by_serach:
                    action = np.argmax(search_result)
                    if verbose:
                        print(f"Player {self.id + 1} : Chosen win rate : {search_result[action]:.3f}")

                    return action, False

                out = self.model(torch.cat([s, v], dim=-1), network).detach().cpu().numpy()
                action = np.argmax(out)

                return action, False

        elif self.player_type == 'manual':
            if dice == 1:
                action = input("Choose your action (0, 1, 2, r) : ")
                reroll = False
                while action not in ['0', '1', '2', 'r'] or (not can_reroll and action == 'r'):
                    action = input("Choose your action (0, 1, 2, r) : ")
                if action == 'r':
                    reroll = True
                else:
                    action = int(action)
                return action, reroll
            else:
                action = input("Choose your action : ").split(' ')
                action = [int(n) for n in action]
                action = v2p[action[0] - 2] * 3 + action[1] - 1
                return action, False

    def reset(self):
        self.soldiers = 18
        self.clear_buffer()
        

    def clear_buffer(self):
        self.buffer_s = []


    def get_buffer(self):
        return np.array(self.buffer_s)


    def check_best_condition(self, score):
        each_best = score[self.all_prob]
        each_best = np.sort(np.max(each_best, axis=1))
        return each_best


    def check_reroll(self, score, ops):
        each_condition_best = self.check_best_condition(score)
        thresh = np.sort(each_condition_best)[int(216 * self.threshold)]
        thresh = max(thresh, 0.1)
        
        reroll = False
        if np.max(score[ops]) < thresh:
            reroll = True
            
        return reroll, thresh
