"""Deep Q-Network (DQN) for Single-Order Delivery Routing on Full Road Graph.

Module: src.rl.train_dqn
Features: #16 (Deep Q-Network Algorithm)
Reference: survey_rl.md §7.2, PROJECT.md
"""

from __future__ import annotations

import argparse
import random
from collections import deque
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim


class DQNetwork(nn.Module):
    """Q-Network approximating action-values for delivery dispatching."""

    def __init__(self, obs_dim: int = 40, act_dim: int = 7):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(obs_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, act_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class ReplayBuffer:
    """Experience replay buffer storing masked transitions."""

    def __init__(self, capacity: int = 50000):
        self.buffer = deque(maxlen=capacity)

    def push(
        self,
        obs: np.ndarray,
        action: int,
        reward: float,
        next_obs: np.ndarray,
        done: bool,
        mask: np.ndarray,
        next_mask: np.ndarray,
    ):
        self.buffer.append((obs, action, reward, next_obs, done, mask, next_mask))

    def sample(self, batch_size: int):
        batch = random.sample(self.buffer, batch_size)
        obs, action, reward, next_obs, done, mask, next_mask = zip(*batch)
        return (
            torch.FloatTensor(np.array(obs)),
            torch.LongTensor(action).unsqueeze(1),
            torch.FloatTensor(reward).unsqueeze(1),
            torch.FloatTensor(np.array(next_obs)),
            torch.FloatTensor(done).unsqueeze(1),
            torch.BoolTensor(np.array(mask)),
            torch.BoolTensor(np.array(next_mask)),
        )

    def __len__(self):
        return len(self.buffer)


class DQNAgent:
    """Double DQN Agent with Action Masking."""

    def __init__(
        self,
        obs_dim: int = 40,
        act_dim: int = 7,
        lr: float = 3e-4,
        gamma: float = 0.99,
        tau: float = 0.005,
        device: str = "cpu",
    ):
        self.act_dim = act_dim
        self.gamma = gamma
        self.tau = tau
        self.device = torch.device(device)

        self.online_net = DQNetwork(obs_dim, act_dim).to(self.device)
        self.target_net = DQNetwork(obs_dim, act_dim).to(self.device)
        self.target_net.load_state_dict(self.online_net.state_dict())
        self.target_net.eval()

        self.optimizer = optim.Adam(self.online_net.parameters(), lr=lr)

    def select_action(
        self, obs: np.ndarray, action_mask: np.ndarray, epsilon: float
    ) -> int:
        if random.random() < epsilon:
            valid_indices = np.where(action_mask)[0]
            if len(valid_indices) == 0:
                return 6  # RETURN_DEPOT fallback
            return int(random.choice(valid_indices))

        with torch.no_grad():
            obs_tensor = torch.FloatTensor(obs).unsqueeze(0).to(self.device)
            q_values = self.online_net(obs_tensor).squeeze(0).cpu().numpy()
            q_values[~action_mask] = -1e9  # Mask invalid actions
            return int(np.argmax(q_values))

    def train_step(self, buffer: ReplayBuffer, batch_size: int = 64) -> float:
        if len(buffer) < batch_size:
            return 0.0

        obs, act, rew, next_obs, done, mask, next_mask = buffer.sample(batch_size)
        obs = obs.to(self.device)
        act = act.to(self.device)
        rew = rew.to(self.device)
        next_obs = next_obs.to(self.device)
        done = done.to(self.device)
        next_mask = next_mask.to(self.device)

        current_q = self.online_net(obs).gather(1, act)

        with torch.no_grad():
            next_q_online = self.online_net(next_obs)
            next_q_online[~next_mask] = -1e9
            best_next_actions = torch.argmax(next_q_online, dim=1, keepdim=True)
            next_q_target = self.target_net(next_obs).gather(1, best_next_actions)
            target_q = rew + (1.0 - done) * self.gamma * next_q_target

        loss = F.smooth_l1_loss(current_q, target_q)
        self.optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.online_net.parameters(), max_norm=10.0)
        self.optimizer.step()

        for target_p, online_p in zip(
            self.target_net.parameters(), self.online_net.parameters()
        ):
            target_p.data.copy_(self.tau * online_p.data + (1.0 - self.tau) * target_p.data)

        return float(loss.item())

    def save(self, filepath: str):
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        torch.save(self.online_net.state_dict(), filepath)

    def load(self, filepath: str):
        self.online_net.load_state_dict(torch.load(filepath, map_location=self.device))
        self.target_net.load_state_dict(self.online_net.state_dict())


def train_dqn(
    timesteps: int = 5000,
    save_path: str = "models/dqn/dqn_hanggon.pt",
    seed: int = 42,
) -> DQNAgent:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    from src.rl.delivery_env import HangGonDeliveryEnv
    env = HangGonDeliveryEnv(seed=seed)

    agent = DQNAgent(obs_dim=40, act_dim=7, lr=3e-4)
    buffer = ReplayBuffer(capacity=50000)

    obs, _ = env.reset()
    mask = env.action_masks()
    epsilon = 1.0
    epsilon_decay = 0.9995
    epsilon_min = 0.05

    for step in range(timesteps):
        action = agent.select_action(obs, mask, epsilon)
        next_obs, reward, terminated, truncated, _ = env.step(action)
        done = terminated or truncated
        next_mask = env.action_masks()

        buffer.push(obs, action, reward, next_obs, done, mask, next_mask)
        loss = agent.train_step(buffer, batch_size=32)

        if done:
            obs, _ = env.reset()
            mask = env.action_masks()
        else:
            obs = next_obs
            mask = next_mask

        epsilon = max(epsilon_min, epsilon * epsilon_decay)

    agent.save(save_path)
    return agent


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train DQN for Single-Order Routing")
    parser.add_argument("--timesteps", type=int, default=5000)
    parser.add_argument("--save-path", type=str, default="models/dqn/dqn_hanggon.pt")
    args = parser.parse_args()

    train_dqn(timesteps=args.timesteps, save_path=args.save_path)
    print(f"[OK] DQN training completed. Model saved to {args.save_path}")
