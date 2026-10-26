"""
PyTorch Proximal Policy Optimization (PPO) for HotWAY GĐ2 Dispatch Semi-MDP.
Actor-Critic architecture with GAE advantage estimation and clipped surrogate objective.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical


class ActorCritic(nn.Module):
    def __init__(self, state_dim: int = 12, action_dim: int = 5, hidden_dim: int = 64):
        super().__init__()
        # Shared feature extractor
        self.feature_net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
        )
        self.actor_head = nn.Linear(hidden_dim, action_dim)
        self.critic_head = nn.Linear(hidden_dim, 1)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        features = self.feature_net(x)
        logits = self.actor_head(features)
        value = self.critic_head(features)
        return logits, value

    def get_action_and_value(self, x: torch.Tensor, action: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        logits, value = self.forward(x)
        dist = Categorical(logits=logits)
        if action is None:
            action = dist.sample()
        return action, dist.log_prob(action), dist.entropy(), value.squeeze(-1)


class PPOAgent:
    def __init__(
        self,
        state_dim: int = 12,
        action_dim: int = 5,
        hidden_dim: int = 64,
        lr: float = 3e-4,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        clip_epsilon: float = 0.2,
        c_val: float = 0.5,
        c_ent: float = 0.01,
        epochs_per_update: int = 4,
        batch_size: int = 64,
        name: str = "PPO",
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.clip_epsilon = clip_epsilon
        self.c_val = c_val
        self.c_ent = c_ent
        self.epochs = epochs_per_update
        self.batch_size = batch_size
        self.name = name

        self.ac = ActorCritic(state_dim, action_dim, hidden_dim)
        self.optimizer = optim.Adam(self.ac.parameters(), lr=lr)

    def select_action(self, state: np.ndarray) -> Tuple[int, float, float]:
        with torch.no_grad():
            s_t = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
            action, log_prob, _, value = self.ac.get_action_and_value(s_t)
            return int(action.item()), float(log_prob.item()), float(value.item())

    def update(
        self,
        states: List[np.ndarray],
        actions: List[int],
        log_probs: List[float],
        rewards: List[float],
        dones: List[bool],
        values: List[float],
    ) -> Dict[str, float]:
        if len(states) < self.batch_size:
            return {"loss": 0.0}

        # Convert to tensors
        states_t = torch.tensor(np.array(states), dtype=torch.float32)
        actions_t = torch.tensor(actions, dtype=torch.int64)
        old_log_probs_t = torch.tensor(log_probs, dtype=torch.float32)

        # GAE Advantage calculation
        T = len(rewards)
        advantages = np.zeros(T, dtype=np.float32)
        last_gae = 0.0
        for t in reversed(range(T)):
            next_val = values[t + 1] if t + 1 < T and not dones[t] else 0.0
            delta = rewards[t] + self.gamma * next_val * (1.0 - float(dones[t])) - values[t]
            last_gae = delta + self.gamma * self.gae_lambda * (1.0 - float(dones[t])) * last_gae
            advantages[t] = last_gae

        returns_t = torch.tensor(advantages + np.array(values), dtype=torch.float32)
        advantages_t = torch.tensor(advantages, dtype=torch.float32)
        if advantages_t.std() > 1e-8:
            advantages_t = (advantages_t - advantages_t.mean()) / (advantages_t.std() + 1e-8)

        # PPO epochs
        dataset_size = T
        indices = np.arange(dataset_size)
        total_loss_acc = 0.0

        for _ in range(self.epochs):
            np.random.shuffle(indices)
            for start in range(0, dataset_size, self.batch_size):
                end = start + self.batch_size
                b_idx = indices[start:end]

                b_states = states_t[b_idx]
                b_actions = actions_t[b_idx]
                b_old_log_probs = old_log_probs_t[b_idx]
                b_advantages = advantages_t[b_idx]
                b_returns = returns_t[b_idx]

                _, new_log_probs, entropy, new_values = self.ac.get_action_and_value(b_states, b_actions)

                # Ratio
                ratio = torch.exp(new_log_probs - b_old_log_probs)

                # Clipped surrogate loss
                surr1 = ratio * b_advantages
                surr2 = torch.clamp(ratio, 1.0 - self.clip_epsilon, 1.0 + self.clip_epsilon) * b_advantages
                policy_loss = -torch.min(surr1, surr2).mean()

                # Value loss
                value_loss = 0.5 * ((new_values - b_returns) ** 2).mean()

                # Entropy loss
                entropy_loss = -entropy.mean()

                total_loss = policy_loss + self.c_val * value_loss + self.c_ent * entropy_loss

                self.optimizer.zero_grad()
                total_loss.backward()
                nn.utils.clip_grad_norm_(self.ac.parameters(), max_norm=0.5)
                self.optimizer.step()
                total_loss_acc += float(total_loss.item())

        return {"loss": total_loss_acc}

    def save(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        torch.save(self.ac.state_dict(), p)

    def load(self, path: str | Path) -> None:
        self.ac.load_state_dict(torch.load(path, map_location="cpu"))
