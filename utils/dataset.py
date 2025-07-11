import torch
import numpy as np
from torch.utils.data import Dataset
import math

class game_dataset(Dataset):
    def __init__(self, file, mode, n_player, seq, min, max):
        super().__init__()

        self.file = file
        self.mode = mode
        self.n_player = n_player
        self.seq = seq
        self.min = min
        self.max = max
        self.load_data()

    def load_data(self):
        data = np.load(self.file)

        gt = torch.from_numpy(data['gt'])[self.seq].float()
        net = torch.from_numpy(data['net'])[self.seq].float()
        state = torch.from_numpy(data['s'])[self.seq].float()

        mask = self.mask_gt(gt)
        self.gt = gt[mask]
        self.net = net[mask]
        self.state = state[mask]

        cut = int(self.gt.shape[0] * 0.8)

        if self.mode == 'test':
            self.gt = self.gt[cut:]
            self.net = self.net[cut:]
            self.state = self.state[cut:]
        elif self.mode == 'train':
            self.gt = self.gt[:cut]
            self.net = self.net[:cut]
            self.state = self.state[:cut]

        self.gt = self.norm_by_dist(self.gt)
        self.len = self.gt.shape[0]
        print(f"{self.mode} dataset: {self.len} samples")

    def norm_by_dist(self, x):
        mean = 1 / self.n_player
        std = 1 / 4
        x = (x - mean) / std
        return x

    def mask_gt(self, gt):
        max_gt = torch.max(gt, dim=-1).values
        max_mask = max_gt >= self.min
        min_gt = torch.min(gt, dim=-1).values
        min_mask = min_gt <= self.max
        mask = max_mask & min_mask
        return mask

    def __len__(self):
        return self.len

    def __getitem__(self, index):
        return self.state[index], self.net[index], self.gt[index]
