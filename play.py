from utils.game import Game
from utils.player import Player
import numpy as np
import torch
from copy import deepcopy
import os
import multiprocessing as mp
from functools import partial
import time
from utils.check_models import find_best
import warnings
import cv2

warnings.filterwarnings('ignore')
os.environ['CUDA_VISIBLE_DEVICES'] = '1'

def simulate(game, player_id, search_time, action):
    points = []
    cnt = 0
    t1 = time.time()
    n_players = game.player_num
    while True:
        game_sim = deepcopy(game)
        for i in range(n_players):
            if i != player_id:
                game_sim.players[i].player_type = 'agent'
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
    return np.array(points)

def search(game, player_id, search_time):
    with mp.Pool(processes=4) as pool:
        func = partial(simulate, game, player_id, search_time)
        result = pool.map(func, range(33))

    sim_points, search_times = zip(*result)
    
    # sim_points : 33 * [L, 3]
    # search_times : 33 * []
    res = []
    for points in sim_points:
        rank = np.argsort(points, axis=1)[:, -1]
        res.append(np.where(rank == player_id)[0].shape[0] / rank.shape[0])

    search_times = np.array(search_times)
    res = np.array(res)

    return res, search_times

def play(game, which_ai, player_names):
    flag = False
    agent_cnt = 0
    while not flag:
        player_id = agent_cnt % game.player_num
        
        if game.players[player_id].soldiers > 0:
            if player_id in which_ai:
                for k in range(game.player_num):
                    game.players[k].random = True
                game.players[player_id].random = False
                
                search_result, search_times = search(game, player_id, 5)
                print(search_result.reshape(11, 3))
                
                print(f"Step {agent_cnt // game.player_num}, avg search times : {np.mean(search_times):.1f}")
                p, success = game.step(player_id=player_id, by_search=True, search_result=search_result, verbose=True)
            else:
                p, success = game.step(player_id=player_id, verbose=True)

            p = game.v2p[p[0]]
            
        score = game.get_current_score()
        flag = game.terminal()
        for k in range(game.player_num):
            print(f"Player {k+1} remain {game.players[k].soldiers:.0f} soldiers")
        draw_map(game.values, game.cnt, player_names, [p, player_id], score)
        
        agent_cnt += 1
        
    final_pts = game.get_current_score(final=True)
    print(f"final score : {final_pts}\n")
    
    return final_pts

def main(game, which_ai, player_names):
    
    game.reset()
    draw_map(game.values, game.cnt, player_names)
    play(game, which_ai, player_names)

def draw_map(values, state, player_names, highlight=[], score=[]):
    image = cv2.imread("map.png")
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1
    colors = [
        (40, 40, 220),      # Rich Red
        (230, 60, 90),      # Electric Blue
        (90, 50, 230),      # Vivid Rose
        (0, 110, 255),      # Bold Orange
        (240, 160, 40),     # Strong Sky Blue
        (10, 60, 160),      # Strong Brown
        (10, 200, 90),      # Sharp Olive
        (120, 220, 40),     # Fresh Green
        (200, 200, 0),      # Deep Teal
        (20, 200, 20),      # Vivid Green
    ]
    thickness = 2
    
    positions = [(110, 216),
                 (216, 222),
                 (557, 181),
                 (671, 105),
                 (339, 308),
                 (458, 306),
                 (672, 228),
                 (148, 409),
                 (96, 570),
                 (367, 474),
                 (559, 522)]
    
    numbers = [str(v) for v in values]
    
    for pos, num in zip(positions, numbers):
        cv2.putText(image, num, pos, font, font_scale, colors[0], thickness, cv2.LINE_AA)
        
    idx = 0
    for pos, s in zip(positions, state):
        if idx == 0 or idx == 4:
            pos = (pos[0] - 80, pos[1] - 30)
        else:
            pos = (pos[0] - 20, pos[1] - 30)
        for i in range(len(s)-1, -1, -1):
            text = f"{player_names[i]}: {s[i]:.0f}"
            if len(highlight) != 0 and idx == highlight[0] and i == highlight[1]:
                cv2.putText(image, text, pos, font, 0.7, colors[-1], 2, cv2.LINE_AA)
            else:
                cv2.putText(image, text, pos, font, 0.7, colors[i+1], 2, cv2.LINE_AA)
            pos = (pos[0], pos[1] - 20)
        idx += 1
        
    pos = (9, 28)
    for i in range(len(score)):
        text = f"{player_names[i]}: {score[i]:.0f}"
        cv2.putText(image, text, pos, font, 0.8, colors[i+1], 2, cv2.LINE_AA)
        pos = (pos[0], pos[1] + 30)
        
    cv2.imwrite("value_map.png", image)

if __name__ == '__main__':
    mp.set_start_method('spawn')
    
    stage = int(input("Model stage : "))
    n_players = int(input("Player number : "))
    dice = int(input("Dice Mode or not : "))
    which_ai = input("Set ai index (separate by ,) : ")
    which_ai = [int(i) for i in which_ai.split(',')]
    player_names = input("Set player name (separate by ,) : ").split(',')
    
    best_model_config = find_best(stage, n_players).loc[0]
    model_name = f'../mdtx-noguess/model_offline/{stage}-{n_players}/{best_model_config["model_dir"]}/best_model.pth'
    
    players = []
    for i in range(n_players):
        if i in which_ai:
            players.append(Player('agent',
                                  player_num=n_players,
                                  model_config=best_model_config,
                                  player_id=i))
        else:
            players.append(Player('manual',
                                  player_num=n_players,
                                  model_config=best_model_config,
                                  player_id=i))
            
        players[i].model.load_state_dict(torch.load(model_name))
        print(f"Player {i+1} load model from {model_name}")
        players[i].epsilon = 0.1
        players[i].random = False
        players[i].model.eval()
    
    game = Game(players=players, dice=dice)
    main(game, which_ai, player_names)
