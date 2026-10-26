"""
PyTorch Deep Q-Network (DQN & Double DQN) for HotWAY GĐ2 Dispatch Semi-MDP.
Compact, memory-efficient MLP (2x64) tailored for CPU execution.
"""

from __future__ import annotations

import collections
import random
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from src.envs.dispatch_env import DispatchEnv


class QNetwork(nn.Module):
    def __init__(self, state_dim: int = 12, action_dim: int = 5, hidden_dim: int = 64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class ReplayBuffer:
    def __init__(self, capacity: int = 20000):
        self.buffer = collections.deque(maxlen=capacity)

    def push(self, state: np.ndarray, action: int, reward: float, next_state: np.ndarray, done: bool) -> None:
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        return (
            torch.tensor(np.array(states), dtype=torch.float32),
            torch.tensor(actions, dtype=torch.int64).unsqueeze(1),
            torch.tensor(rewards, dtype=torch.float32).unsqueeze(1),
            torch.tensor(np.array(next_states), dtype=torch.float32),
            torch.tensor(dones, dtype=torch.float32).unsqueeze(1),
        )

    def __len__(self) -> int:
        return len(self.buffer)


class DQNAgent:
    def __init__(
        self,
        state_dim: int = 12,
        action_dim: int = 5,
        hidden_dim: int = 64,
        lr: float = 1e-3,
        gamma: float = 0.99,
        is_double: bool = False,
        buffer_capacity: int = 20000,
        batch_size: int = 64,
        target_update_freq: int = 200,
        name: Optional[str] = None,
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.is_double = is_double
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq
        self.name = name if name else ("Double_DQN" if is_double else "DQN")

        self.q_net = QNetwork(state_dim, action_dim, hidden_dim)
        self.target_net = QNetwork(state_dim, action_dim, hidden_dim)
        self.target_net.load_state_dict(self.q_net.state_dict())
        self.target_net.eval()

        self.optimizer = optim.Adam(self.q_net.parameters(), lr=lr)
        self.loss_fn = nn.SmoothL1Loss()  # Huber Loss
        self.buffer = ReplayBuffer(buffer_capacity)
        self.train_step_count = 0

    def select_action(self, state: np.ndarray, epsilon: float = 0.0) -> int:
        if random.random() < epsilon:
            return random.randint(0, self.action_dim - 1)
        with torch.no_grad():
            s_t = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
            q_values = self.q_net(s_t)
            return int(torch.argmax(q_values, dim=1).item())

    def update(self) -> Optional[float]:
        if len(self.buffer) < self.batch_size:
            return None

        states, actions, rewards, next_states, dones = self.buffer.sample(self.batch_size)

        curr_q = self.q_net(states).gather(1, actions)

        with torch.no_grad():
            if self.is_double:
                # Double DQN: action selected by online net, evaluated by target net
                best_actions = self.q_net(next_states).argmax(dim=1, keepdim=True)
                next_q = self.target_net(next_states).gather(1, best_actions)
            else:
                # Standard DQN: max_a over target net
                next_q = self.target_net(next_states).max(dim=1, keepdim=True)[0]

            target_q = rewards + (1.0 - dones) * (self.gamma * next_q)

        loss = self.loss_fn(curr_q, target_q)

        self.optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.q_net.parameters(), max_norm=10.0)
        self.optimizer.step()

        self.train_step_count += 1
        if self.train_step_count % self.target_update_freq == 0:
            self.target_net.load_state_dict(self.q_net.state_dict())

        return float(loss.item())

    def save(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            "model_state": self.q_net.state_dict(),
            "is_double": self.is_double,
            "train_step_count": self.train_step_count,
        }, p)

    def load(self, path: str | Path) -> None:
        ckpt = torch.load(path, map_location="cpu")
        self.q_net.load_state_dict(ckpt["model_state"])
        self.target_net.load_state_dict(self.q_net.state_dict())
