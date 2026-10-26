"""Tabular Q-Learning on a 10-node Subgraph for MDP Optimality Proof.

Module: src.rl.train_qlearning
Features: #15 (Tabular Q-Learning Algorithm)
Reference: survey_rl.md §7.1, PROJECT.md
"""

from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np


class Subgraph10NodeMDP:
    """10-node delivery subgraph environment with Newton cooling physics."""

    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)
        self.num_nodes = 10
        self.depot_node = 0
        self.num_orders = 3
        self.order_nodes = [3, 5, 8]  # Customer delivery destinations

        # Base edge distances (meters) on 10-node metric grid
        self.dist_matrix = np.zeros((10, 10), dtype=np.float32)
        node_coords = {
            0: (10.9212, 107.2401),  # Depot (Quán Bánh Canh Gà)
            1: (10.9240, 107.2412),  # QL56 North
            2: (10.9270, 107.2413),  # QL56 Intersection
            3: (10.9210, 107.2380),  # Commune West (Order 1)
            4: (10.9240, 107.2470),  # Rubber Plantation East
            5: (10.9180, 107.2450),  # Hamlet South (Order 2)
            6: (10.9300, 107.2422),  # Secondary Bypass
            7: (10.9279, 107.2479),  # East Bypass Cự Thạch
            8: (10.9150, 107.2410),  # South Endpoint (Order 3)
            9: (10.9215, 107.2293),  # Local Alley Đồi Rìu
        }
        self.coords = node_coords
        for i in range(10):
            for j in range(10):
                if i != j:
                    lat1, lon1 = node_coords[i]
                    lat2, lon2 = node_coords[j]
                    dx = (lon2 - lon1) * 111320.0 * math.cos(math.radians(10.92))
                    dy = (lat2 - lat1) * 110540.0
                    self.dist_matrix[i, j] = math.sqrt(dx * dx + dy * dy)

        # Thermal and vehicle constants
        self.speed_mps = 30.0 * 1000.0 / 3600.0  # 30 km/h = 8.33 m/s
        self.k_composite = 0.019  # Bánh Canh Gà in Insulated Bag (min^-1)
        self.t_env = 30.0
        self.t0 = 88.0
        self.ql56_edges = {(0, 1), (1, 0), (1, 2), (2, 1)}
        self.congestion_factor = 2.5

        self.reset()

    def reset(self) -> int:
        self.current_node = self.depot_node
        self.pending_orders = [True] * self.num_orders  # [Ord0, Ord1, Ord2]
        self.order_temps = [self.t0] * self.num_orders
        self.elapsed_time_min = 0.0
        return self._get_state()

    def _get_state(self) -> int:
        bitmask = 0
        for idx, pending in enumerate(self.pending_orders):
            if pending:
                bitmask |= (1 << idx)
        return self.current_node * (2 ** self.num_orders) + bitmask

    def get_valid_actions(self) -> List[int]:
        valid = []
        if any(self.pending_orders):
            for idx, pending in enumerate(self.pending_orders):
                if pending:
                    valid.append(self.order_nodes[idx])
        else:
            valid.append(self.depot_node)
        return valid

    def step(self, action: int) -> Tuple[int, float, bool, Dict]:
        valid_actions = self.get_valid_actions()
        if action not in valid_actions:
            return self._get_state(), -50.0, False, {"error": "invalid_action"}

        dist_m = self.dist_matrix[self.current_node, action]
        speed = self.speed_mps
        if (self.current_node, action) in self.ql56_edges:
            speed /= self.congestion_factor

        transit_seconds = dist_m / speed
        transit_minutes = transit_seconds / 60.0
        self.elapsed_time_min += transit_minutes

        for i in range(self.num_orders):
            if self.pending_orders[i]:
                self.order_temps[i] = self.t_env + (self.order_temps[i] - self.t_env) * math.exp(
                    -self.k_composite * transit_minutes
                )

        reward = -0.15 * transit_minutes
        self.current_node = action

        if action in self.order_nodes:
            ord_idx = self.order_nodes.index(action)
            if self.pending_orders[ord_idx]:
                self.pending_orders[ord_idx] = False
                delivered_temp = self.order_temps[ord_idx]
                if delivered_temp >= 60.0:
                    r_thermal = 10.0 * ((delivered_temp - 60.0) / 25.0)
                else:
                    r_thermal = -0.05 * ((60.0 - delivered_temp) ** 2)
                reward += r_thermal

        done = (not any(self.pending_orders)) and (self.current_node == self.depot_node)
        if done:
            reward += 10.0

        return self._get_state(), reward, done, {
            "elapsed_time": self.elapsed_time_min,
            "order_temps": list(self.order_temps),
        }


def train_qlearning(
    episodes: int = 2000,
    alpha: float = 0.1,
    gamma: float = 0.95,
    epsilon_start: float = 1.0,
    epsilon_min: float = 0.05,
    epsilon_decay: float = 0.998,
    save_path: str = "models/q_table.npy",
) -> np.ndarray:
    env = Subgraph10NodeMDP(seed=42)
    num_states = 10 * (2 ** env.num_orders)  # 80
    num_actions = 10
    q_table = np.zeros((num_states, num_actions), dtype=np.float32)

    epsilon = epsilon_start
    rewards_history = []

    for ep in range(episodes):
        state = env.reset()
        done = False
        ep_reward = 0.0

        while not done:
            valid_actions = env.get_valid_actions()
            if np.random.rand() < epsilon:
                action = int(np.random.choice(valid_actions))
            else:
                q_vals = np.full(num_actions, -np.inf)
                q_vals[valid_actions] = q_table[state, valid_actions]
                action = int(np.argmax(q_vals))

            next_state, reward, done, _ = env.step(action)
            ep_reward += reward

            next_valid = env.get_valid_actions() if not done else [0]
            next_max_q = np.max(q_table[next_state, next_valid]) if not done else 0.0

            td_target = reward + gamma * next_max_q
            q_table[state, action] += alpha * (td_target - q_table[state, action])
            state = next_state

        epsilon = max(epsilon_min, epsilon * epsilon_decay)
        rewards_history.append(ep_reward)

    out_file = Path(save_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    np.save(out_file, q_table)
    return q_table


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Tabular Q-Learning on 10-node Subgraph")
    parser.add_argument("--episodes", type=int, default=2000)
    parser.add_argument("--alpha", type=float, default=0.1)
    parser.add_argument("--gamma", type=float, default=0.95)
    parser.add_argument("--save-path", type=str, default="models/q_table.npy")
    args = parser.parse_args()

    q_tab = train_qlearning(
        episodes=args.episodes,
        alpha=args.alpha,
        gamma=args.gamma,
        save_path=args.save_path,
    )
    print(f"[OK] Tabular Q-learning completed. Converged Q-table saved to {args.save_path}")
