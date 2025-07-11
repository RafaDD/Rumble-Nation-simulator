from utils.model import Transformer_model
from utils.dataset import game_dataset
import torch
import torch.nn as nn
from datetime import datetime
from torch.utils.data import DataLoader
import os
import numpy as np
import argparse
import pandas as pd
from utils.check_models import find_best
import warnings

warnings.filterwarnings('ignore')
os.environ['CUDA_VISIBLE_DEVICES'] = '0'

def save_print(file, text):
    with open(file, 'a') as f:
        f.write(text + '\n')
    print(text)

def set_seed(seed):
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--nlayer', type=int, default=4)
    parser.add_argument('--embed_dim', type=int, default=256)
    parser.add_argument('--gcn', type=int, default=1)
    parser.add_argument('--epochs', type=int, default=400)
    parser.add_argument('--player_num', type=int, default=2)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--bs', type=int, default=512)
    parser.add_argument('--min', type=float, default=0.0)
    parser.add_argument('--max', type=float, default=1.0)
    parser.add_argument('--stage', type=int, default=1)
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    set_seed(args.seed)

    now = datetime.now()
    datetime_str = now.strftime("%Y%m%d%H%M%S")
    log_dir = f"./model_offline/{args.stage}-{args.player_num}/{datetime_str}"
    log_file = os.path.join(log_dir, 'log.txt')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    device = 'cuda'

    if args.stage > 1:
        stage = args.stage - 1
        best_model_config = find_best(stage, n_player=args.player_num).loc[0]
        model = Transformer_model(player_num=args.player_num,
                                  embed_dim=best_model_config["embed_dim"],
                                  nlayers=best_model_config["nlayer"],
                                  gcn=best_model_config["gcn"]).to(device)
        model.load_state_dict(torch.load(f"./model_offline/{stage}-{args.player_num}/{best_model_config['model_dir']}/best_model.pth"))
        print(f"load from " + f"./model_offline/{stage}-{args.player_num}/{best_model_config['model_dir']}/best_model.pth")
        lr = 3e-4
    else:
        model = Transformer_model(player_num=args.player_num,
                                  embed_dim=args.embed_dim,
                                  nlayers=args.nlayer,
                                  gcn=args.gcn).to(device)
        lr = 5e-4

    optim = torch.optim.Adam(model.parameters(),
                             lr=lr,
                             weight_decay=1e-4)
    criterion = nn.MSELoss()

    data_file = f"./buffer/{args.stage}-{args.player_num}/data.npz"
    length = np.load(data_file)['gt'].shape[0]
    seq = torch.randperm(length)

    train_dataset = game_dataset(file=data_file,
                                 mode='train',
                                 n_player=args.player_num,
                                 seq=seq,
                                 min=args.min,
                                 max=args.max)
    test_dataset = game_dataset(file=data_file,
                                mode='test',
                                n_player=args.player_num,
                                seq=seq,
                                min=args.min,
                                max=args.max)

    train_loader = DataLoader(dataset=train_dataset,
                              batch_size=args.bs,
                              shuffle=True,
                              num_workers=16,
                              drop_last=True)
    test_loader = DataLoader(dataset=test_dataset,
                             batch_size=2048,
                             shuffle=False,
                             num_workers=16,
                             drop_last=False)

    best_loss = 9999999
    epochs = args.epochs
    test_interval = 5

    for e in range(epochs):
        model.train()
        total_loss = 0
        for state, net, gt in train_loader:
            optim.zero_grad()
            state, net, gt = state.to(device), net.to(device), gt.to(device)
            pred = model(state, net)
            loss = criterion(pred, gt)

            loss.backward()
            optim.step()

            total_loss += loss.item()

        if e % test_interval == 0 or e == epochs - 1:
            save_print(log_file, f"Epoch [{e+1}/{epochs}], Train Loss: {total_loss/len(train_loader):.4f}")
            model.eval()
            test_total_loss = 0

            idx = 0
            for state, net, gt in test_loader:
                state, net, gt = state.to(device), net.to(device), gt.to(device)
                pred = model(state, net)
                loss = criterion(pred, gt)

                test_total_loss += loss.item()
                idx += 1

            test_total_loss = test_total_loss / len(test_loader)
            save_print(log_file, f"Epoch [{e+1}/{epochs}], Eval Loss: {test_total_loss:.4f}")

            if test_total_loss < best_loss:
                best_loss = test_total_loss
                torch.save(model.state_dict(), os.path.join(log_dir, 'best_model.pth'))
                save_print(log_file, f"Best model saved.")

    args.test_loss = best_loss
    args_dict = vars(args)
    df = pd.DataFrame([args_dict])
    df.to_csv(os.path.join(log_dir, 'args.csv'), index=False)
    torch.save(model.state_dict(), os.path.join(log_dir, 'final_model.pth'))

if __name__ == '__main__':
    main()
