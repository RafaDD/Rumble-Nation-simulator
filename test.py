from utils.game import Game
from utils.player import Player
from tqdm import trange, tqdm
import numpy as np
import torch
from copy import deepcopy
import os
import multiprocessing as mp
from datetime import datetime
from functools import partial
import time
from utils.check_models import find_best
import warnings
import argparse

warnings.filterwarnings('ignore')
os.environ['CUDA_VISIBLE_DEVICES'] = '1'

def save_print(log_file, text):
    with open(log_file, 'a') as f:
        f.write(text + '\n')
    print(text)

def parallel_sim(game, player_id, action):
    points = []
    cnt = 0
    t1 = time.time()
    n_players = game.player_num
    while True:
        game_sim = deepcopy(game)
        game_sim.step(player_id, action)
        idx = (player_id + 1) % n_players
        while True:
            game_sim.step(idx)
            idx = (idx + 1) % n_players
            flag = game_sim.terminal()
            if flag:
                break
        score = game_sim.get_current_score()
        points.append(1 if score[player_id] == np.max(score) else 0)
        cnt += 1
        t = time.time()
        if (t - t1) >= 3:
            break
    return np.mean(points), cnt

def search(game, test_id):
    with mp.Pool(processes=4) as pool:
        func = partial(parallel_sim, game, test_id)
        result = pool.map(func, range(33))

    sim_points, search_times = zip(*result)

    sim_points = np.array(sim_points)
    search_times = np.array(search_times)

    return sim_points, search_times

def simulate(game, verbose=False, log_file=None, IsSearch=False, test_id=0):
    flag = False
    agent_cnt = 0
    while not flag:
        player_id = agent_cnt % game.player_num
        if game.players[player_id].soldiers > 0:
            if IsSearch and player_id == test_id:
                search_result, search_times = search(game)
                save_print(log_file, f"Step {agent_cnt // game.player_num}, avg search times : {np.mean(search_times):.1f}")
                game.step(player_id=player_id, by_search=True, search_result=search_result, verbose=True)
            else:
                game.step(player_id=player_id, verbose=False)
        flag = game.terminal()
        agent_cnt += 1

    final_pts = game.get_current_score(final=verbose)
    if IsSearch:
        save_print(log_file, f"final score : {final_pts}\n")

    return final_pts

def main(game, sim_round=10, log_file=None, IsSearch=False, test_id=0):
    res_list = []
    win_rate = []
    loop = tqdm(range(sim_round), ncols=120)
    for i in loop:
        if IsSearch:
            save_print(log_file, f"Round {i+1}")
        game.reset()
        res = simulate(game, False, log_file, IsSearch, test_id)
        win_rate.append(1 if res[test_id] == np.max(res) else 0)
        res_list.append(res)
        loop.set_postfix(agent_win_rate=f"{np.mean(win_rate)*100:.2f} %")

    res_list = np.array(res_list)
    return res_list

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--player_num', type=int, default=2)
    parser.add_argument('--stage', type=int, default=1)
    parser.add_argument('--round', type=int, default=1000)
    parser.add_argument('--search', type=int, default=0)
    parser.add_argument('--test_id', type=int, default=0)
    parser.add_argument('--dice', type=int, default=1)
    parser.add_argument('--all_agent', type=int, default=0)

    args = parser.parse_args()
    return args

if __name__ == '__main__':
    mp.set_start_method('spawn')
    args = parse_args()

    now = datetime.now()
    datetime_str = now.strftime("%Y%m%d%H%M%S")
    log_file = f'./result/{datetime_str}/log.txt'
    if not os.path.exists(f'./result/{datetime_str}'):
        os.makedirs(f'./result/{datetime_str}')

    stage = args.stage
    IsSearch = False if args.search == 0 else True
    simround = args.round
    n_players = args.player_num

    best_model_config = find_best(stage, n_players).loc[0]
    model_name = f'./model_offline/{stage}-{n_players}/{best_model_config["model_dir"]}/best_model.pth'
    players = []
    for pid in range(n_players):
        if pid != args.test_id and args.all_agent == 0:
            players.append(Player('random',
                                  player_id=pid,
                                  player_num=n_players))
        else:
            players.append(Player('agent',
                                  player_num=n_players,
                                  model_config=best_model_config,
                                  player_id=pid,
                                  log_file=log_file))
        
            players[pid].model.load_state_dict(torch.load(model_name))
            save_print(log_file, f"model : {model_name}")
            players[pid].epsilon = 0.0
            players[pid].random = False
            players[pid].model.eval()

    game = Game(players, args.dice)
    res_list = main(game, sim_round=simround, log_file=log_file, IsSearch=IsSearch, test_id=args.test_id)
    ranking = np.argsort(res_list, axis=1)[:, -1]

    res_list = np.mean(res_list, axis=0)
    winrate = []
    for i in range(len(players)):
        winrate.append(np.where(ranking == i)[0].shape[0] / ranking.shape[0])

    save_print(log_file, '\nPlayer' + ' ' * 6 + 'Win rate' + ' ' * 6 + 'Score' + ' ' * 6 + 'Type')
    save_print(log_file, '=' * 47)
    for i in range(len(players)):
        save_print(log_file, f'{i}' + ' ' * 7 + f'{100 * winrate[i]:.2f} %' + ' ' * 7 + f'{res_list[i]:.2f}' + ' ' * 6 + players[i].player_type)
