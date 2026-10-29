"""
RoutingEnv: Gymnasium Environment for GĐ1 (Time-Dependent Stochastic Routing).
Agent navigates from source node A to destination node B on a strongly connected
subgraph of HCMC street network with Markovian traffic congestion.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import gymnasium as gym
from gymnasium import spaces
import networkx as nx
import numpy as np


class RoutingEnv(gym.Env):
    """
    Gymnasium environment for adaptive shortest path under Markovian traffic congestion.
    """
    metadata = {"render_modes": ["ansi"]}

    def __init__(
        self,
        subgraph_path: str | Path = "data/urban_routing_subgraph.pickle",
        source_node: Optional[int] = None,
        dest_node: Optional[int] = None,
        free_speed_mps: float = 8.33,  # 30 km/h in m/s
        max_steps: int = 50,
        render_mode: Optional[str] = None,
    ):
        super().__init__()
        self.subgraph_path = Path(subgraph_path)
        with open(self.subgraph_path, "rb") as f:
            self.graph: nx.MultiDiGraph = pickle.load(f)

        self.nodes = sorted(list(self.graph.nodes()))
        self.node_to_idx = {n: i for i, n in enumerate(self.nodes)}
        self.idx_to_node = {i: n for i, n in enumerate(self.nodes)}
        self.n_nodes = len(self.nodes)

        # Build adjacency mapping
        self.adj: Dict[int, List[int]] = {}
        self.edge_lengths: Dict[Tuple[int, int], float] = {}
        for u in self.nodes:
            self.adj[u] = []
            for v in self.graph.successors(u):
                self.adj[u].append(v)
                # shortest edge length if multiple edges exist
                min_len = min(
                    d.get("length", 100.0)
                    for d in self.graph.get_edge_data(u, v).values()
                )
                self.edge_lengths[(u, v)] = float(min_len)

        self.max_out_degree = max(len(succs) for succs in self.adj.values())
        self.free_speed_mps = free_speed_mps
        self.max_steps = max_steps
        self.render_mode = render_mode

        # Congestion levels: 0: Clear (1.0x), 1: Slow (1.8x), 2: Congested (3.5x)
        self.congestion_multipliers = np.array([1.0, 1.8, 3.5], dtype=np.float32)

        # Stationary Markov transition matrix for congestion states
        # P[c_curr, c_next]
        self.P_traffic = np.array([
            [0.70, 0.25, 0.05],  # Clear tends to stay clear
            [0.25, 0.55, 0.20],  # Slow can clear up or congest
            [0.10, 0.35, 0.55],  # Congested tends to stay congested
        ], dtype=np.float64)

        # Default source and destination
        self.source_node = source_node if source_node is not None else self.nodes[0]
        self.dest_node = dest_node if dest_node is not None else self.nodes[-1]

        # Action space: choice of outgoing edge index (0 .. max_out_degree - 1)
        self.action_space = spaces.Discrete(self.max_out_degree)

        # Observation space: (current_node_idx, dest_node_idx, congestion_vector)
        # Vector size: 2 + max_out_degree
        self.observation_space = spaces.Box(
            low=0.0,
            high=max(self.n_nodes, 3.0),
            shape=(2 + self.max_out_degree,),
            dtype=np.float32,
        )

        # Internal state
        self.current_node: int = self.source_node
        self.current_step: int = 0
        self.congestion_state: Dict[Tuple[int, int], int] = {}
        self.np_random = np.random.default_rng(2026)

    def _get_obs(self) -> np.ndarray:
        obs = np.zeros(2 + self.max_out_degree, dtype=np.float32)
        obs[0] = float(self.node_to_idx[self.current_node])
        obs[1] = float(self.node_to_idx[self.dest_node])

        succs = self.adj[self.current_node]
        for i, v in enumerate(succs):
            edge = (self.current_node, v)
            obs[2 + i] = float(self.congestion_state.get(edge, 0))
        # Zero-pad remaining outgoing slots
        return obs

    def get_state_key(self) -> Tuple[int, int, Tuple[int, ...]]:
        """Compact tuple representation for Tabular Q-learning and Value Iteration."""
        succs = self.adj[self.current_node]
        cong_tuple = tuple(self.congestion_state.get((self.current_node, v), 0) for v in succs)
        return (self.current_node, self.dest_node, cong_tuple)

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        super().reset(seed=seed)
        if seed is not None:
            self.np_random = np.random.default_rng(seed)

        self.current_node = self.source_node
        self.current_step = 0

        # Sample initial congestion for all edges
        self.congestion_state = {}
        for edge in self.edge_lengths:
            self.congestion_state[edge] = int(self.np_random.choice(3, p=[0.6, 0.3, 0.1]))

        obs = self._get_obs()
        info = {
            "current_node": self.current_node,
            "dest_node": self.dest_node,
            "state_key": self.get_state_key(),
        }
        return obs, info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        self.current_step += 1
        succs = self.adj[self.current_node]

        if len(succs) == 0:
            # Dead end (should not happen in SCC)
            return self._get_obs(), -100.0, True, False, {"error": "no_outgoing_edges"}

        # Wrap or clip action if out of range
        actual_action = action % len(succs)
        next_node = succs[actual_action]
        edge = (self.current_node, next_node)

        # Travel time calculation
        length_m = self.edge_lengths[edge]
        cong_level = self.congestion_state.get(edge, 0)
        multiplier = float(self.congestion_multipliers[cong_level])
        travel_time_sec = (length_m / self.free_speed_mps) * multiplier

        # Transition congestion states according to Markov matrix
        new_congestion = {}
        for e, c_prev in self.congestion_state.items():
            c_next = int(self.np_random.choice(3, p=self.P_traffic[c_prev]))
            new_congestion[e] = c_next
        self.congestion_state = new_congestion

        # Advance node
        self.current_node = next_node

        # Reward = negative travel time (seconds)
        reward = -travel_time_sec

        terminated = bool(self.current_node == self.dest_node)
        truncated = bool(self.current_step >= self.max_steps and not terminated)

        obs = self._get_obs()
        info = {
            "current_node": self.current_node,
            "dest_node": self.dest_node,
            "travel_time_sec": travel_time_sec,
            "edge": edge,
            "state_key": self.get_state_key(),
            "terminated": terminated,
        }
        return obs, reward, terminated, truncated, info
