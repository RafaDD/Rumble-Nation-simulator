import torch
import torch.nn as nn
import torch.nn.functional as F

class GCN(nn.Module):
    def __init__(self, embed_dim, layers, gamma):
        super().__init__()
        self.fc = nn.ModuleList([
            nn.Sequential(nn.Linear(embed_dim, embed_dim),
                          nn.ReLU()) for _ in range(layers)
        ])
        self.gamma = gamma
        self.layers = layers

    def forward(self, x, g):
        # x : [B, N, D]
        # g : [B, N, N]
        for i in range(self.layers):
            x = x + (self.gamma ** (i + 1)) * torch.einsum('bnk,bkd->bnd', g, x)
            x = self.fc[i](x)
        return x

class Transformer_model(nn.Module):
    def __init__(self, player_num, embed_dim=128, nlayers=2, gcn=1):
        super().__init__()
        self.player_num = player_num
        self.nlayers = nlayers
        self.use_gcn = gcn

        self.embed = nn.Linear(2*player_num+1, embed_dim, bias=False)
        self.gcn = GCN(embed_dim=embed_dim,
                       layers=3,
                       gamma=0.3)
        self.attn = nn.ModuleList([AttentionLayer(embed_dim=embed_dim,
                                                  num_heads=8,
                                                  dropout=0.2) for _ in range(nlayers)])
        self.fc = nn.Linear(embed_dim * 11, 33, bias=False)

    def forward(self, state, net):
        cnt, net = self.process_feature(state, net)
        B = cnt.shape[0]
        h = self.embed(cnt)
        if self.nlayers == 0:
            h = F.relu(h)

        if self.use_gcn == 1:
            h = self.gcn(h, net)

        for i in range(self.nlayers):
            h = self.attn[i](h)

        h = h.reshape(B, -1)
        out = self.fc(h).squeeze()
        return out

    def process_feature(self, state, net):
        if len(state.shape) == 2:
            B = state.shape[0]
        else:
            state = state.unsqueeze(0)
            B = 1

        cnt = state[:, :-11].reshape(B, 11, -1) / 18 * 11
        empty = torch.sign(torch.sum(-cnt[:, :, :3], dim=-1, keepdim=True) + 1e-3)
        empty = (empty + 1) / 2

        diff_cnt = cnt[:, :, :1] - cnt[:, :, 1:]
        value = state[:, -11:] / 7
        cnt = torch.cat([cnt, diff_cnt, empty, value.unsqueeze(-1)], dim=-1)

        if len(net.shape) == 2:
            net = net.unsqueeze(0)
        net = net - torch.eye(11).unsqueeze(0).to(net.device)
        return cnt, net

class AttentionLayer(nn.Module):
    def __init__(self, embed_dim, num_heads, dropout):
        super(AttentionLayer, self).__init__()
        self.attn = nn.MultiheadAttention(embed_dim=embed_dim,
                                          num_heads=num_heads,
                                          dropout=dropout,
                                          batch_first=True)
        self.norm_1 = nn.LayerNorm(embed_dim)
        self.norm_2 = nn.LayerNorm(embed_dim)
        self.ffn = nn.Sequential(nn.Linear(embed_dim, 1024),
                                 nn.GELU(),
                                 nn.Linear(1024, embed_dim))

    def forward(self, x):
        x_norm = self.norm_1(x)
        x = self.attn(x_norm, x_norm, x_norm)[0] + x
        x_norm = self.norm_2(x)
        out = self.ffn(x_norm) + x
        return out
