"""
Adaptive Routing Environment (Semi-MDP) and Exact Value Iteration Ground Truth for T3.
HotWAY Gate G2: Reinforcement Learning & Stochastic Shortest Path Environment.
"""

from __future__ import annotations

import itertools
import math
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import gymnasium as gym
from gymnasium import spaces
import networkx as nx
import numpy as np

from src.routing.multicriteria_router import calculate_bearing, turn_classification
from src.traffic.provider import TrafficProvider, SyntheticProvider, TrafficState


class AdaptiveRoutingEnv(gym.Env):
    """
    Gymnasium Environment for Adaptive Real-Time Motorbike Routing under Traffic Congestion.
    Formulated as a Stochastic Shortest Path (SSP) MDP:
    - State: (current_node, target_node, outgoing_edge_states, time_of_day)
    - Action: Choice of outgoing edge index from current_node
    - Reward: - travel_time_min (including edge traversal, turn delays, and signal delays)
    - Terminal: Reaching target_node or exceeding max_steps
    """

    metadata = {"render_modes": ["ansi"]}

    def __init__(
        self,
        graph: Optional[Union[nx.DiGraph, nx.MultiDiGraph, str, Path]] = None,
        traffic_provider: Optional[TrafficProvider] = None,
        source_node: Optional[int] = None,
        target_node: Optional[int] = None,
        rain: bool = False,
        max_steps: int = 60,
        render_mode: Optional[str] = None,
    ):
        super().__init__()

        # 1. Load Graph
        if graph is None:
            graph_path = Path("data/binhthanh_routing_subgraph.pickle")
            with open(graph_path, "rb") as f:
                loaded = pickle.load(f)
        elif isinstance(graph, (str, Path)):
            with open(graph, "rb") as f:
                loaded = pickle.load(f)
        else:
            loaded = graph

        # Normalize to DiGraph taking minimum length edge
        if loaded.is_multigraph():
            self.graph = nx.DiGraph()
            for n, d in loaded.nodes(data=True):
                self.graph.add_node(n, **d)
            for u, v, k, d in loaded.edges(keys=True, data=True):
                if not self.graph.has_edge(u, v) or d.get("length", 1e9) < self.graph[u][v].get("length", 1e9):
                    self.graph.add_edge(u, v, **d)
        else:
            self.graph = loaded.copy()

        self.nodes = sorted(list(self.graph.nodes()))
        self.node_to_idx = {n: i for i, n in enumerate(self.nodes)}
        self.idx_to_node = {i: n for i, n in enumerate(self.nodes)}
        self.n_nodes = len(self.nodes)

        # Adjacency and Edge attributes
        self.adj: Dict[int, List[int]] = {}
        for u in self.nodes:
            self.adj[u] = sorted(list(self.graph.successors(u)))

        self.max_out_degree = max(len(succs) for succs in self.adj.values()) if self.adj else 1

        # Node coordinates
        self.coords: Dict[int, Tuple[float, float]] = {}
        lats, lons = [], []
        for n in self.nodes:
            d = self.graph.nodes[n]
            lat = float(d.get("y") or d.get("lat", 10.80))
            lon = float(d.get("x") or d.get("lon", 106.71))
            self.coords[n] = (lat, lon)
            lats.append(lat)
            lons.append(lon)

        self.min_lat, self.max_lat = min(lats), max(lats)
        self.min_lon, self.max_lon = min(lons), max(lons)

        # Traffic provider
        self.traffic_provider = traffic_provider or SyntheticProvider(seed=2026)
        self.rain = rain
        self.max_steps = max_steps
        self.render_mode = render_mode

        # Configurable endpoints
        self.source_node = source_node if source_node is not None else self.nodes[0]
        self.target_node = target_node if target_node is not None else self.nodes[-1]

        # Action Space: index of outgoing edge [0 .. max_out_degree - 1]
        self.action_space = spaces.Discrete(self.max_out_degree)

        # Observation Space:
        # [curr_lat, curr_lon, target_lat, target_lon, time_norm] (5 dims)
        # + outgoing_congestion (max_out_degree dims)
        # + outgoing_length_km (max_out_degree dims)
        obs_dim = 5 + 2 * self.max_out_degree
        self.observation_space = spaces.Box(
            low=-1.0, high=2.0, shape=(obs_dim,), dtype=np.float32
        )

        # Dynamic episode variables
        self.current_node: int = self.source_node
        self.prev_node: Optional[int] = None
        self.step_count: int = 0
        self.current_time_min: float = 480.0  # 8:00 AM
        self.total_travel_time_sec: float = 0.0
        self.path_history: List[int] = []

    def _get_action_mask(self, node: int) -> np.ndarray:
        """Returns boolean mask of valid outgoing actions from node."""
        deg = len(self.adj[node])
        mask = np.zeros(self.max_out_degree, dtype=bool)
        mask[:deg] = True
        return mask

    def _get_obs(self) -> np.ndarray:
        """Constructs flat observation vector for RL agent."""
        curr_lat, curr_lon = self.coords[self.current_node]
        targ_lat, targ_lon = self.coords[self.target_node]

        lat_range = max(1e-5, self.max_lat - self.min_lat)
        lon_range = max(1e-5, self.max_lon - self.min_lon)

        c_lat_norm = (curr_lat - self.min_lat) / lat_range
        c_lon_norm = (curr_lon - self.min_lon) / lon_range
        t_lat_norm = (targ_lat - self.min_lat) / lat_range
        t_lon_norm = (targ_lon - self.min_lon) / lon_range
        time_norm = (self.current_time_min % 1440.0) / 1440.0

        succs = self.adj[self.current_node]
        deg = len(succs)

        # Outgoing congestion states normalized to [0, 1] (-1 for padded)
        cong_arr = np.full(self.max_out_degree, -1.0, dtype=np.float32)
        dist_arr = np.full(self.max_out_degree, 0.0, dtype=np.float32)

        for i, v in enumerate(succs):
            edge_data = self.graph[self.current_node][v]
            hw = str(edge_data.get("highway", "residential"))
            state = self.traffic_provider.get_edge_state(
                self.current_node, v, hw, self.current_time_min
            )
            cong_arr[i] = float(state) / 2.0  # 0.0: Clear, 0.5: Slow, 1.0: Congested
            length_m = float(edge_data.get("length", 50.0))
            dist_arr[i] = float(length_m / 1000.0)  # in km

        obs = np.concatenate([
            [c_lat_norm, c_lon_norm, t_lat_norm, t_lon_norm, time_norm],
            cong_arr,
            dist_arr,
        ]).astype(np.float32)

        return obs

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        super().reset(seed=seed)
        if seed is not None:
            self.traffic_provider.reset(seed)

        if options:
            if "source_node" in options:
                self.source_node = options["source_node"]
            if "target_node" in options:
                self.target_node = options["target_node"]
            if "rain" in options:
                self.rain = options["rain"]
            if "time_of_day_min" in options:
                self.current_time_min = float(options["time_of_day_min"])

        self.current_node = self.source_node
        self.prev_node = None
        self.step_count = 0
        self.total_travel_time_sec = 0.0
        self.path_history = [self.current_node]

        obs = self._get_obs()
        info = {
            "current_node": self.current_node,
            "target_node": self.target_node,
            "action_mask": self._get_action_mask(self.current_node),
            "step_count": self.step_count,
            "total_travel_time_sec": self.total_travel_time_sec,
        }
        return obs, info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        self.step_count += 1
        succs = self.adj[self.current_node]
        deg = len(succs)

        # Invalid action check
        if action < 0 or action >= deg:
            # Action outside out-degree: penalty and stay at node
            reward = -2.0  # Heavy penalty in minutes
            terminated = False
            truncated = (self.step_count >= self.max_steps)
            obs = self._get_obs()
            info = {
                "current_node": self.current_node,
                "target_node": self.target_node,
                "action_mask": self._get_action_mask(self.current_node),
                "invalid_action": True,
            }
            return obs, reward, terminated, truncated, info

        next_node = succs[action]
        edge_data = self.graph[self.current_node][next_node]
        length_m = float(edge_data.get("length", 50.0))
        hw = str(edge_data.get("highway", "residential"))

        # 1. Travel time on edge
        edge_travel_sec = self.traffic_provider.get_edge_travel_time_sec(
            self.current_node, next_node, length_m, hw, self.current_time_min, self.rain
        )

        # 2. Turn penalty (Left turn cuts opposing traffic)
        turn_delay_sec = 0.0
        if self.prev_node is not None:
            p_prev = self.coords[self.prev_node]
            p_curr = self.coords[self.current_node]
            p_next = self.coords[next_node]
            b_in = calculate_bearing(p_prev, p_curr)
            b_out = calculate_bearing(p_curr, p_next)
            t_type = turn_classification(b_in, b_out)
            if t_type == "LEFT":
                turn_delay_sec += 12.0
            elif t_type == "RIGHT":
                turn_delay_sec += 4.0
            elif t_type == "UTURN":
                turn_delay_sec += 16.0

        # 3. Traffic signal junction delay
        if self.graph.nodes[next_node].get("highway") == "traffic_signals" or len(self.adj[next_node]) >= 4:
            turn_delay_sec += 25.0

        step_duration_sec = edge_travel_sec + turn_delay_sec
        self.total_travel_time_sec += step_duration_sec
        self.current_time_min += (step_duration_sec / 60.0)

        # Update node state
        self.prev_node = self.current_node
        self.current_node = next_node
        self.path_history.append(self.current_node)

        # Reward = negative travel time in minutes
        reward = float(- step_duration_sec / 60.0)

        terminated = (self.current_node == self.target_node)
        truncated = (self.step_count >= self.max_steps and not terminated)

        obs = self._get_obs()
        info = {
            "current_node": self.current_node,
            "target_node": self.target_node,
            "action_mask": self._get_action_mask(self.current_node),
            "step_duration_sec": step_duration_sec,
            "total_travel_time_sec": self.total_travel_time_sec,
            "total_travel_time_min": self.total_travel_time_sec / 60.0,
            "path_history": list(self.path_history),
        }

        return obs, reward, terminated, truncated, info


class ValueIterationSolver:
    """
    Exact Dynamic Programming (Value Iteration) for Stochastic Shortest Path.
    Provides mathematical Ground Truth V*(s) for the MDP with zero approximation error.
    """

    def __init__(
        self,
        env: AdaptiveRoutingEnv,
        discount_gamma: float = 1.0,
        epsilon: float = 1e-9,
        max_iter: int = 1000,
    ):
        self.env = env
        self.gamma = discount_gamma
        self.epsilon = epsilon
        self.max_iter = max_iter

    def solve(
        self,
        target_node: Optional[int] = None,
        edge_costs: Optional[Dict[Tuple[int, int], float]] = None,
    ) -> Tuple[Dict[int, float], Dict[int, int]]:
        """
        Solves the Bellman optimality equation for expected minimal travel time to target_node.
        V*(u) = min_v [ c(u, v) + gamma * V*(v) ]
        Returns:
            V_star: mapping from node -> expected minimal travel time in minutes
            optimal_policy: mapping from node -> optimal successor node
        """
        target = target_node if target_node is not None else self.env.target_node

        # Initialize V: 0.0 at target, large value elsewhere
        V: Dict[int, float] = {n: 1e9 for n in self.env.nodes}
        V[target] = 0.0
        policy: Dict[int, int] = {}

        # Precompute expected edge costs in minutes if not provided
        if edge_costs is None:
            edge_costs = {}
            for u in self.env.nodes:
                for v in self.env.adj[u]:
                    edge_data = self.env.graph[u][v]
                    length_m = float(edge_data.get("length", 50.0))
                    hw = str(edge_data.get("highway", "residential"))
                    # Base expected time
                    t_sec = self.env.traffic_provider.get_edge_travel_time_sec(
                        u, v, length_m, hw, time_of_day_min=480.0, rain=self.env.rain
                    )
                    edge_costs[(u, v)] = t_sec / 60.0

        for it in range(self.max_iter):
            max_delta = 0.0
            new_V = V.copy()

            for u in self.env.nodes:
                if u == target:
                    continue

                best_val = 1e9
                best_succ = -1

                for v in self.env.adj[u]:
                    c_uv = edge_costs[(u, v)]
                    val = c_uv + self.gamma * V[v]
                    if val < best_val:
                        best_val = val
                        best_succ = v

                delta = abs(new_V[u] - best_val)
                if delta > max_delta:
                    max_delta = delta

                new_V[u] = best_val
                if best_succ != -1:
                    policy[u] = best_succ

            V = new_V
            if max_delta < self.epsilon:
                break

        return V, policy
