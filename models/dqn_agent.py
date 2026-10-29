"""
Model 1: Dueling Deep Q-Network with Action Masking and Prioritized Experience Replay (PER).
Retrospective Baseline & Ablation Focus: Demonstrates the mathematical and structural failure modes
of applying value-based MLP reinforcement learning to combinatorial, variable-sized routing graphs.
"""

from __future__ import annotations

import math
import random
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from env.traffic_tsp_env import TrafficTSPEnv


class DuelingDQNNetwork(nn.Module):
    """
    4-layer Deep MLP with Dueling Architecture (Value Stream V(s) and Advantage Stream A(s, a)).
    Fixed input dimension: 5 base features + 2 * (max_nodes + 1) [visited + distance].
    Fixed output dimension: max_nodes + 1.
    """

    def __init__(self, max_nodes: int = 20, hidden_dims: Tuple[int, ...] = (256, 512, 256, 128)):
        super().__init__()
        self.max_nodes = max_nodes
        self.action_dim = max_nodes + 1
        self.state_dim = 5 + 2 * self.action_dim  # 5 + 42 = 47 for max_nodes=20

        # Shared feature extractor
        self.fc1 = nn.Linear(self.state_dim, hidden_dims[0])
        self.fc2 = nn.Linear(hidden_dims[0], hidden_dims[1])
        self.fc3 = nn.Linear(hidden_dims[1], hidden_dims[2])
        self.fc4 = nn.Linear(hidden_dims[2], hidden_dims[3])

        # Value stream: V(s) -> scalar
        self.value_head = nn.Linear(hidden_dims[3], 1)

        # Advantage stream: A(s, a) -> action_dim
        self.advantage_head = nn.Linear(hidden_dims[3], self.action_dim)

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        h = F.relu(self.fc1(x))
        h = F.relu(self.fc2(h))
        h = F.relu(self.fc3(h))
        h = F.relu(self.fc4(h))

        v = self.value_head(h)
        a = self.advantage_head(h)

        # Dueling formula: Q(s, a) = V(s) + (A(s, a) - mean(A(s, a')))
        q = v + (a - a.mean(dim=-1, keepdim=True))

        if mask is not None:
            # Action masking with large negative constant
            q = torch.where(mask, q, torch.tensor(-1e9, device=q.device, dtype=q.dtype))
        return q


class PrioritizedReplayBuffer:
    """Prioritized Experience Replay (PER) for sample-efficient DQN training."""

    def __init__(self, capacity: int = 20000, alpha: float = 0.6):
        self.capacity = capacity
        self.alpha = alpha
        self.buffer: List[Tuple[np.ndarray, int, float, np.ndarray, bool, np.ndarray]] = []
        self.priorities = np.zeros((capacity,), dtype=np.float32)
        self.pos = 0

    def push(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
        next_mask: np.ndarray
    ):
        max_prio = self.priorities.max() if self.buffer else 1.0
        if len(self.buffer) < self.capacity:
            self.buffer.append((state, action, reward, next_state, done, next_mask))
        else:
            self.buffer[self.pos] = (state, action, reward, next_state, done, next_mask)
        self.priorities[self.pos] = max_prio
        self.pos = (self.pos + 1) % self.capacity

    def sample(self, batch_size: int = 64, beta: float = 0.4):
        if len(self.buffer) == 0:
            return None
        prios = self.priorities[:len(self.buffer)]
        probs = prios ** self.alpha
        probs /= probs.sum()

        indices = np.random.choice(len(self.buffer), batch_size, p=probs)
        samples = [self.buffer[idx] for idx in indices]

        total = len(self.buffer)
        weights = (total * probs[indices]) ** (-beta)
        weights /= weights.max()
        return samples, indices, np.array(weights, dtype=np.float32)

    def update_priorities(self, indices: List[int], priorities: np.ndarray):
        for idx, prio in zip(indices, priorities):
            self.priorities[idx] = max(prio, 1e-5)

    def __len__(self):
        return len(self.buffer)


class DQNAgent:
    """Double Dueling DQN Agent with Action Masking."""

    def __init__(
        self,
        max_nodes: int = 20,
        lr: float = 1e-4,
        gamma: float = 0.99,
        device: str = "cpu"
    ):
        self.max_nodes = max_nodes
        self.gamma = gamma
        self.device = torch.device(device)

        self.q_net = DuelingDQNNetwork(max_nodes=max_nodes).to(self.device)
        self.target_net = DuelingDQNNetwork(max_nodes=max_nodes).to(self.device)
        self.target_net.load_state_dict(self.q_net.state_dict())
        self.target_net.eval()

        self.optimizer = optim.Adam(self.q_net.parameters(), lr=lr)
        self.memory = PrioritizedReplayBuffer()
        self.epsilon = 1.0
        self.epsilon_min = 0.05
        self.epsilon_decay = 0.995

    def select_action(self, state: np.ndarray, mask: np.ndarray, eval_mode: bool = False) -> int:
        valid_actions = np.where(mask)[0]
        if len(valid_actions) == 0:
            return 0

        if not eval_mode and random.random() < self.epsilon:
            return int(random.choice(valid_actions))

        with torch.no_grad():
            s_tensor = torch.tensor(state, dtype=torch.float32, device=self.device).unsqueeze(0)
            m_tensor = torch.tensor(mask, dtype=torch.bool, device=self.device).unsqueeze(0)
            q_vals = self.q_net(s_tensor, m_tensor)
            action = int(torch.argmax(q_vals, dim=-1).item())
            if action not in valid_actions:
                action = int(valid_actions[0])
            return action

    def train_step(self, batch_size: int = 64) -> Optional[float]:
        if len(self.memory) < batch_size:
            return None

        sample_res = self.memory.sample(batch_size)
        if sample_res is None:
            return None
        samples, indices, weights = sample_res

        b_state, b_action, b_reward, b_next_state, b_done, b_next_mask = zip(*samples)

        s_t = torch.tensor(np.array(b_state), dtype=torch.float32, device=self.device)
        a_t = torch.tensor(b_action, dtype=torch.long, device=self.device).unsqueeze(1)
        r_t = torch.tensor(b_reward, dtype=torch.float32, device=self.device).unsqueeze(1)
        ns_t = torch.tensor(np.array(b_next_state), dtype=torch.float32, device=self.device)
        d_t = torch.tensor(b_done, dtype=torch.float32, device=self.device).unsqueeze(1)
        nm_t = torch.tensor(np.array(b_next_mask), dtype=torch.bool, device=self.device)
        w_t = torch.tensor(weights, dtype=torch.float32, device=self.device).unsqueeze(1)

        # Double DQN target calculation
        current_q = self.q_net(s_t).gather(1, a_t)

        with torch.no_grad():
            next_q_online = self.q_net(ns_t, nm_t)
            next_best_action = torch.argmax(next_q_online, dim=1, keepdim=True)
            next_q_target = self.target_net(ns_t).gather(1, next_best_action)
            expected_q = r_t + (1.0 - d_t) * self.gamma * next_q_target

        td_errors = torch.abs(current_q - expected_q).detach().cpu().numpy()
        loss = (w_t * F.smooth_l1_loss(current_q, expected_q, reduction="none")).mean()

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        self.memory.update_priorities(indices, td_errors.flatten())
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        return float(loss.item())

    def update_target(self):
        self.target_net.load_state_dict(self.q_net.state_dict())


class DQNSolver:
    """Wrapper Solver for evaluation across the 100 POI benchmark."""

    def __init__(self, agent: Optional[DQNAgent] = None, max_nodes: int = 20, weights_path: Optional[str] = None):
        self.max_nodes = max_nodes
        if agent is not None:
            self.agent = agent
        else:
            self.agent = DQNAgent(max_nodes=max_nodes)
            if weights_path:
                try:
                    self.agent.q_net.load_state_dict(torch.load(weights_path, map_location="cpu"))
                    self.agent.q_net.eval()
                except Exception as e:
                    print(f"Notice: Could not load DQN weights ({e}), using initialized agent.")

    def solve(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Solve an itinerary instance using DQN.
        If instance has N > max_nodes, documents the fatal flaw of truncation/padding failure.
        """
        start_time = time.perf_counter()
        env = TrafficTSPEnv(instance_dict=instance, fixed_max_nodes=self.max_nodes)
        obs, info = env.reset()

        num_stops = instance.get("num_stops", len(instance.get("stops", [])))
        is_overflow = bool(num_stops > self.max_nodes)

        done = False
        step_count = 0
        max_allowed_steps = min(num_stops + 2, self.max_nodes + 2)

        while not done and step_count < max_allowed_steps:
            step_count += 1
            state_vec, action_mask = env.get_dqn_state_vector(max_nodes=self.max_nodes)
            action = self.agent.select_action(state_vec, action_mask, eval_mode=True)
            
            # Map back to valid environment action
            if action >= env.total_nodes:
                valid_acts = np.where(env.get_valid_action_mask())[0]
                action = int(valid_acts[0]) if len(valid_acts) > 0 else 0

            obs, rew, terminated, truncated, step_info = env.step(action)
            done = terminated or truncated

        solve_time_ms = (time.perf_counter() - start_time) * 1000.0

        # If not cleanly terminated (e.g. stopped at max steps or N > max_nodes), complete route naively to depot
        route = list(env.route_history)
        if route[-1] != 0:
            route.append(0)

        # Recalculate full duration and distance
        total_dist = 0.0
        total_dur = 0.0
        dep_hour = instance.get("departure_hour", 8.0)
        curr_time = 0.0
        for i in range(len(route) - 1):
            u, v = route[i], route[i + 1]
            c_t = env.current_traffic_factor
            d = instance["dist_matrix_km"][u][v]
            t_base = instance["duration_matrix_min"][u][v]
            adj_t = t_base * c_t
            total_dist += d
            total_dur += adj_t
            curr_time += adj_t

        return {
            "model": "Dueling DQN (Masked)",
            "route": route,
            "total_dist_km": round(total_dist, 2),
            "total_duration_min": round(total_dur, 2),
            "solve_time_ms": round(solve_time_ms, 2),
            "is_overflow": is_overflow,
            "failure_note": "Rigid N_max=20 limit exceeded; required truncation/masking" if is_overflow else None
        }

    def measure_permutation_invariance_violation(self, instance: Dict[str, Any]) -> float:
        """
        Diagnostic measurement: Feed exact same locations in shuffled orders.
        Calculate standard deviation of predicted Q-values (measures Lack of Permutation Invariance).
        """
        env = TrafficTSPEnv(instance_dict=instance, fixed_max_nodes=self.max_nodes)
        env.reset()
        state_vec, mask = env.get_dqn_state_vector(max_nodes=self.max_nodes)
        with torch.no_grad():
            s_t = torch.tensor(state_vec, dtype=torch.float32).unsqueeze(0)
            m_t = torch.tensor(mask, dtype=torch.bool).unsqueeze(0)
            q_original = self.agent.q_net(s_t, m_t).squeeze(0).numpy()

        # Shuffle stops in state vector representation
        q_variances = []
        for _ in range(5):
            perm = np.random.permutation(self.max_nodes)
            # Permute distance features
            shuffled_vec = state_vec.copy()
            shuffled_vec[5 + (self.max_nodes + 1):] = state_vec[5 + (self.max_nodes + 1):][np.append([0], perm + 1)]
            with torch.no_grad():
                s_shuf = torch.tensor(shuffled_vec, dtype=torch.float32).unsqueeze(0)
                q_shuf = self.agent.q_net(s_shuf, m_t).squeeze(0).numpy()
            q_variances.append(np.mean(np.abs(q_original - q_shuf)))

        return float(np.mean(q_variances))

