"""
Candidate Edge-Scoring Deep Q-Network for Real-Time Motorbike Adaptive Routing (T3 Layer).
HotWAY Gate G4: Reinforcement Learning & Dynamic Routing Agent.
Permutation-invariant MLP that scores candidate outgoing edges to handle arbitrary node degrees.
"""

from __future__ import annotations

import collections
import random
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from src.routing.multicriteria_router import calculate_bearing, turn_classification


class CandidateEdgeScoringNetwork(nn.Module):
    """
    MLP that scores a candidate edge e = (u, v) given current state and destination.
    Takes feature vector x(s, e) in R^10 and predicts expected cumulative return Q(s, e).
    """

    def __init__(self, in_features: int = 10, hidden_dim: int = 64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: Tensor of shape (K, in_features) or (B, in_features)
        Returns: Tensor of shape (K,) or (B,) with scalar Q-values.
        """
        return self.net(x).squeeze(-1)


def extract_candidate_edge_features(
    env: Any,
    current_node: int,
    target_node: int,
    prev_node: Optional[int],
    current_time_min: float,
    rain: bool = False,
) -> Tuple[np.ndarray, List[int]]:
    """
    Extracts 10-dimensional feature vector for each outgoing edge from current_node:
    1. Curr node lat norm
    2. Curr node lon norm
    3. Target node lat norm
    4. Target node lon norm
    5. Destination distance progress: dist(u, D) - dist(v, D) (km)
    6. Edge length (km)
    7. Edge congestion status [0.0, 0.5, 1.0]
    8. Edge base speed limit normalized
    9. Traffic signal / major junction indicator (1.0 or 0.0)
    10. Left turn penalty flag (1.0 if left turn, else 0.0)
    """
    G = env.graph
    succs = env.adj[current_node]
    K = len(succs)
    if K == 0:
        return np.zeros((1, 10), dtype=np.float32), []

    lat_range = max(1e-5, env.max_lat - env.min_lat)
    lon_range = max(1e-5, env.max_lon - env.min_lon)

    u_lat, u_lon = env.coords[current_node]
    d_lat, d_lon = env.coords[target_node]

    # Euclidean distance to target in km
    dist_u_target = np.sqrt(
        ((u_lat - d_lat) * 111.0) ** 2
        + ((u_lon - d_lon) * 111.0 * np.cos(np.radians(u_lat))) ** 2
    )

    p_prev = env.coords[prev_node] if prev_node is not None else None
    features = np.zeros((K, 10), dtype=np.float32)

    for i, v in enumerate(succs):
        v_lat, v_lon = env.coords[v]
        dist_v_target = np.sqrt(
            ((v_lat - d_lat) * 111.0) ** 2
            + ((v_lon - d_lon) * 111.0 * np.cos(np.radians(v_lat))) ** 2
        )
        progress_km = dist_u_target - dist_v_target

        edge_data = G[current_node][v]
        length_km = float(edge_data.get("length", 50.0)) / 1000.0
        hw = str(edge_data.get("highway", "residential"))
        c_state = env.traffic_provider.get_edge_state(current_node, v, hw, current_time_min)
        cong_norm = float(c_state) / 2.0  # 0.0, 0.5, 1.0

        # Base speed
        speed = env.traffic_provider.get_edge_speed_kph(current_node, v, hw, current_time_min, rain)
        speed_norm = speed / 40.0

        # Signal / high degree
        is_signal = 1.0 if (G.nodes[v].get("highway") == "traffic_signals" or len(env.adj[v]) >= 4) else 0.0

        # Turn classification
        is_left_turn = 0.0
        if p_prev is not None:
            b_in = calculate_bearing(p_prev, (u_lat, u_lon))
            b_out = calculate_bearing((u_lat, u_lon), (v_lat, v_lon))
            if turn_classification(b_in, b_out) == "LEFT":
                is_left_turn = 1.0

        features[i] = [
            (u_lat - env.min_lat) / lat_range,
            (u_lon - env.min_lon) / lon_range,
            (d_lat - env.min_lat) / lat_range,
            (d_lon - env.min_lon) / lon_range,
            progress_km,
            length_km,
            cong_norm,
            speed_norm,
            is_signal,
            is_left_turn,
        ]

    return features, succs


class EdgeScoringDQNAgent:
    """
    Deep Q-Network Agent with Candidate Edge Scoring MLP.
    Permutation-invariant and handles variable node degrees seamlessly.
    """

    def __init__(
        self,
        in_features: int = 10,
        hidden_dim: int = 64,
        lr: float = 5e-4,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.05,
        epsilon_decay_steps: int = 1500,
        buffer_size: int = 15000,
        batch_size: int = 32,
        target_update_interval: int = 100,
        device: str = "cpu",
    ):
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = (epsilon_start - epsilon_end) / max(1, epsilon_decay_steps)
        self.batch_size = batch_size
        self.target_update_interval = target_update_interval
        self.device = torch.device(device)

        self.policy_net = CandidateEdgeScoringNetwork(in_features, hidden_dim).to(self.device)
        self.target_net = CandidateEdgeScoringNetwork(in_features, hidden_dim).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=lr)
        self.loss_fn = nn.SmoothL1Loss()

        self.replay_buffer = collections.deque(maxlen=buffer_size)
        self.total_steps = 0

    def select_action(
        self,
        features: np.ndarray,
        deterministic: bool = False,
    ) -> int:
        """Selects action index among available candidate edges."""
        K = len(features)
        if K <= 1:
            return 0

        if not deterministic and random.random() < self.epsilon:
            return random.randrange(K)

        with torch.no_grad():
            x = torch.from_numpy(features).float().to(self.device)
            q_vals = self.policy_net(x).cpu().numpy()
            return int(np.argmax(q_vals))

    def decay_epsilon(self) -> None:
        self.epsilon = max(self.epsilon_end, self.epsilon - self.epsilon_decay)

    def store_transition(
        self,
        curr_feat: np.ndarray,      # Feature vector of chosen edge: shape (10,)
        reward: float,
        next_feats: np.ndarray,     # Features of all outgoing edges from next node: shape (K_next, 10)
        done: bool,
    ) -> None:
        self.replay_buffer.append((curr_feat, reward, next_feats, done))

    def update(self) -> Optional[float]:
        if len(self.replay_buffer) < self.batch_size:
            return None

        batch = random.sample(self.replay_buffer, self.batch_size)
        curr_feats, rewards, next_feats_list, dones = zip(*batch)

        curr_x = torch.tensor(np.array(curr_feats), dtype=torch.float32, device=self.device)
        pred_q = self.policy_net(curr_x)

        target_q_list = []
        with torch.no_grad():
            for r, next_f, done in zip(rewards, next_feats_list, dones):
                if done or len(next_f) == 0:
                    target_q_list.append(r)
                else:
                    nx_t = torch.tensor(next_f, dtype=torch.float32, device=self.device)
                    max_next_q = self.target_net(nx_t).max().item()
                    target_q_list.append(r + self.gamma * max_next_q)

        target_q = torch.tensor(target_q_list, dtype=torch.float32, device=self.device)

        loss = self.loss_fn(pred_q, target_q)
        self.optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.policy_net.parameters(), 5.0)
        self.optimizer.step()

        self.total_steps += 1
        if self.total_steps % self.target_update_interval == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())

        return float(loss.item())

    def save(self, path: str) -> None:
        torch.save({
            "model_state": self.policy_net.state_dict(),
            "total_steps": self.total_steps,
            "epsilon": self.epsilon,
        }, path)

    def load(self, path: str) -> None:
        ckpt = torch.load(path, map_location=self.device)
        self.policy_net.load_state_dict(ckpt["model_state"])
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.total_steps = ckpt.get("total_steps", 0)
        self.epsilon = ckpt.get("epsilon", self.epsilon_end)
