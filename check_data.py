import numpy as np
import matplotlib.pyplot as plt
import sys

stage = sys.argv[1]
n_player = sys.argv[2]

def mask_gt(gt, min=0.1, max=0.95):
    max_gt = np.max(gt, axis=-1)
    max_mask = max_gt >= min
    min_gt = np.min(gt, axis=-1)
    min_mask = min_gt <= max
    mask = max_mask & min_mask
    return mask

gt = np.load(f'./buffer/{stage}-{n_player}/data.npz')['gt']
print(gt.shape)

mask = mask_gt(gt)
gt = gt[mask]
print(gt.shape)

gt = gt.reshape(-1)
mean_gt = np.mean(gt)
std_gt = np.std(gt)

# Plot
plt.figure(figsize=(10, 4))
plt.hist(gt, bins=20, range=(0, 1))
plt.axvline(mean_gt, color='red', linestyle='--', label=f'Mean = {mean_gt:.2f}')
plt.axvline(mean_gt+std_gt, color='blue', linestyle='--', label=f'Std = {std_gt:.2f}')
plt.axvline(mean_gt-std_gt, color='blue', linestyle='--')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(f'./imgs/hist-{stage}-{n_player}.png', dpi=200)
