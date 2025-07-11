from utils.game import Game
from utils.player import Player
from tqdm import trange
import numpy as np
from copy import deepcopy
import os
import multiprocessing as mp
from functools import partial
import time
from utils.check_models import find_best
import warnings
import argparse
import torch

warnings.filterwarnings('ignore')
os.environ['CUDA_VISIBLE_DEVICES'] = '0'

def parallel_sim(game, player_id, search_time, action):
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
        if (t - t1) >= search_time:
            break
    return np.mean(points)

def save_print(file, text):
    with open(file, 'a') as f:
        f.write(text + '\n')
    print(text)

def save_buffer(data_dir, gt, net, state):
    try:
        data = np.load(data_dir)
        gt = np.concatenate([data['gt'], gt], axis=0)
        net = np.concatenate([data['net'], net], axis=0)
        state = np.concatenate([data['s'], state], axis=0)
    except Exception as e:
        print(e)
        pass
    np.savez(data_dir, gt=gt, net=net, s=state)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--player_num', type=int, default=2)
    parser.add_argument('--stage', type=int, default=0)
    parser.add_argument('--random_sim', type=float, default=1.0)
    parser.add_argument('--explore', type=float, default=0.5)
    parser.add_argument('--round', type=int, default=10)
    parser.add_argument('--search_time', type=float, default=1.0)

    args = parser.parse_args()
    return args

def main():
    mp.set_start_method('spawn')

    args = parse_args()
    stage = args.stage
    n_players = args.player_num

    if not os.path.exists(f'./models/{stage}-{n_players}'):
        os.makedirs(f'./models/{stage}-{n_players}')

    data_dir = f'./buffer/{stage}-{n_players}'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    log_file = f'./models/{stage}-{n_players}/log.txt'

    model_config = {
        "embed_dim": 256,
        "nlayer": 4,
        "gcn": 1,
    }

    players = [Player('agent',
                      player_num=n_players,
                      model_config=model_config,
                      player_id=pid,
                      log_file=log_file) for pid in range(n_players)]
    for j in range(n_players):
        players[j].epsilon = args.random_sim
        players[j].random = True
        if args.stage >= 1:
            prev_stage = args.stage - 1
            best_model_config = find_best(prev_stage, n_players).loc[0]
            model_name = f'./model_offline/{prev_stage}-{n_players}/{best_model_config["model_dir"]}/best_model.pth'
            players[j].model.load_state_dict(torch.load(model_name))
            print(f"player {j+1} load model form {model_name}")

    game = Game(players=players, dice=0)

    res_list = []
    buffer_size = [0, 0, 0, 0]
    sim_round = args.round
    for i in trange(sim_round, ncols=100):
        gt = []
        state = []
        net = []

        for sim_times in range(3):
            game.reset()
            flag = False
            points = []
            while not flag:
                for j in range(game.player_num):
                    if game.players[j].soldiers == 0:
                        continue
                    
                    for k in range(n_players):
                        game.players[k].epsilon = args.random_sim

                    with mp.Pool(processes=4) as pool:
                        func = partial(parallel_sim, game, j, args.search_time)
                        point = pool.map(func, range(33))
                    
                    point = np.array(point)
                    points.append(point)

                    game.players[j].epsilon = args.explore

                    game.step(j, by_search=True, search_result=point, verbose=True)

                    flag = game.terminal()

            res = game.get_current_score()
            print(res)

            for j in range(n_players):
                buffer_s = game.players[j].get_buffer()
                points_arr = np.array(points)
                if len(buffer_s) <= len(points_arr):
                    points_subset = points_arr[:len(buffer_s)]
                else:
                    points_subset = points_arr
                    
                graph = game.get_graph()
                graph = np.tile(graph, (len(buffer_s), 1, 1))

                state.append(buffer_s)
                gt.append(points_subset)
                net.append(graph)

        res_list.append(res)

        gt = np.concatenate(gt, axis=0)
        net = np.concatenate(net, axis=0)
        state = np.concatenate(state, axis=0)
        save_buffer(os.path.join(data_dir, 'data.npz'), gt, net, state)

        buffer_size.pop(0)
        buffer_size.append(gt.shape[0])
        print(buffer_size)

        for j in range(n_players):
            game.players[j].clear_buffer()

        if i % 10 == 0:
            res_list_continue = res_list
            res_list_np = np.array(res_list)
            ranking = np.argsort(res_list_np, axis=1)[:, -1]
            res_list_mean = np.mean(res_list_np, axis=0)
            winrate = []
            for k in range(len(players)):
                winrate.append(np.where(ranking == k)[0].shape[0] / ranking.shape[0])

            save_print(log_file, f'Simulation {i}\nPlayer' + ' ' * 6 + 'Win rate' + ' ' * 6 + 'Score')
            save_print(log_file, '='*40)
            for k in range(len(players)):
                save_print(log_file, f'{k}' + ' ' * 7 + f'{100 * winrate[k]:.2f} %' + ' ' * 7 + f'{res_list_mean[k]:.2f}')
            res_list = res_list_continue


if __name__ == '__main__':
    main()
