"""
Tabular Q-Learning Agent and Convergence Checker for GĐ1 (Adaptive Routing).
Verifies mathematical convergence against ExactValueIteration Ground Truth.
"""

from __future__ import annotations

import time
from typing import Dict, Tuple, Any, List
import numpy as np

from src.envs.routing_env import RoutingEnv
from src.envs.exact_dp import ExactValueIteration


class TabularQLearningAgent:
    def __init__(
        self,
        env: RoutingEnv,
        alpha: float = 0.1,
        gamma: float = 1.0,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.05,
        epsilon_decay_episodes: int = 500,
    ):
        self.env = env
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon_start = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay_episodes

        # Q-table: mapping (node, congestion_tuple) -> Q-values array of length max_out_degree
        self.q_table: Dict[Tuple[int, Tuple[int, ...]], np.ndarray] = {}

    def get_q(self, state: Tuple[int, Tuple[int, ...]]) -> np.ndarray:
        if state not in self.q_table:
            # Initialize with small negative values
            self.q_table[state] = np.zeros(self.env.max_out_degree, dtype=np.float64)
        return self.q_table[state]

    def select_action(self, state: Tuple[int, Tuple[int, ...]], epsilon: float, rng: np.random.Generator) -> int:
        u = state[0]
        deg = len(self.env.adj[u])
        if deg == 0:
            return 0
        if rng.random() < epsilon:
            return int(rng.integers(0, deg))
        q = self.get_q(state)
        # Select argmax among valid outgoing edges
        valid_q = q[:deg]
        best_actions = np.where(valid_q == np.max(valid_q))[0]
        return int(rng.choice(best_actions))

    def train(self, num_episodes: int = 1000, seed: int = 2026) -> Dict[str, Any]:
        t0 = time.perf_counter()
        rng = np.random.default_rng(seed)
        rewards_history = []

        for ep in range(num_episodes):
            frac = min(1.0, ep / self.epsilon_decay)
            eps = self.epsilon_start + frac * (self.epsilon_end - self.epsilon_start)

            obs, info = self.env.reset(seed=int(rng.integers(1, 100000)))
            curr_state = (self.env.current_node, info["state_key"][2])
            ep_reward = 0.0
            terminated = False
            truncated = False

            while not (terminated or truncated):
                act = self.select_action(curr_state, eps, rng)
                obs, r, terminated, truncated, step_info = self.env.step(act)
                ep_reward += r

                next_state = (self.env.current_node, step_info["state_key"][2])
                q_curr = self.get_q(curr_state)

                if terminated:
                    target = r
                else:
                    u_next = next_state[0]
                    deg_next = len(self.env.adj[u_next])
                    q_next = self.get_q(next_state)[:deg_next]
                    target = r + self.gamma * (np.max(q_next) if deg_next > 0 else 0.0)

                q_curr[act] += self.alpha * (target - q_curr[act])
                curr_state = next_state

            rewards_history.append(ep_reward)

        train_duration = time.perf_counter() - t0
        return {
            "num_episodes": num_episodes,
            "train_time_sec": train_duration,
            "final_reward_mean": float(np.mean(rewards_history[-100:])),
        }

    def evaluate_against_ground_truth(self, vi: ExactValueIteration) -> Dict[str, float]:
        """Measures policy agreement and value gap against exact DP."""
        agreements = []
        val_diffs = []

        for s, true_act in vi.policy.items():
            u, cong = s
            deg = len(self.env.adj[u])
            if deg == 0 or u == self.env.dest_node:
                continue

            q = self.get_q(s)[:deg]
            learned_act = int(np.argmax(q))
            agreements.append(float(learned_act == true_act))

            learned_v = float(np.max(q))
            idx = vi.state_to_idx[s]
            true_v = vi.V[idx]
            val_diffs.append(abs(learned_v - true_v))

        return {
            "policy_agreement_rate": float(np.mean(agreements)) if agreements else 1.0,
            "max_value_error": float(np.max(val_diffs)) if val_diffs else 0.0,
            "mean_value_error": float(np.mean(val_diffs)) if val_diffs else 0.0,
        }
