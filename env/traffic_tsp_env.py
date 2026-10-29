"""
Unified Gymnasium Environment for Dynamic, Traffic-Aware Multi-Stop Routing in Vietnam.
Supports all 4 benchmark models: Dueling DQN, Pointer Network, Attention Model, and OR-Tools.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import torch


def compute_traffic_multiplier(hour_float: float) -> float:
    """
    Empirical traffic congestion factor C(t) for Vietnamese metropolitan roadways.
    Peaks around 07:00-08:30 (Morning rush) and 17:00-18:30 (Evening rush).
    """
    t = hour_float % 24.0
    if 7.0 <= t < 8.5:
        return 2.10
    elif 8.5 <= t < 9.0:
        return 1.50
    elif 9.0 <= t < 16.5:
        return 1.20
    elif 16.5 <= t < 17.0:
        return 1.60
    elif 17.0 <= t < 18.5:
        return 2.25
    elif 18.5 <= t < 20.0:
        return 1.40
    elif 20.0 <= t < 22.0:
        return 1.10
    else:
        return 1.00


def compute_traffic_multiplier_tensor(hour: torch.Tensor) -> torch.Tensor:
    """Tensor equivalent of compute_traffic_multiplier with identical interval edges."""
    t = torch.remainder(hour, 24.0)
    value = torch.ones_like(t)
    value = torch.where((t >= 20.0) & (t < 22.0), 1.10, value)
    value = torch.where((t >= 18.5) & (t < 20.0), 1.40, value)
    value = torch.where((t >= 17.0) & (t < 18.5), 2.25, value)
    value = torch.where((t >= 16.5) & (t < 17.0), 1.60, value)
    value = torch.where((t >= 9.0) & (t < 16.5), 1.20, value)
    value = torch.where((t >= 8.5) & (t < 9.0), 1.50, value)
    value = torch.where((t >= 7.0) & (t < 8.5), 2.10, value)
    return value


def simulate_route(instance: Dict[str, Any], route: List[int]) -> Tuple[float, float]:
    """Return distance and elapsed duration for a closed route using base durations.

    ``duration_matrix_min`` must contain free-flow durations. Congestion is applied
    exactly once per edge at the hour that edge is entered.
    """
    dist = np.asarray(instance["dist_matrix_km"], dtype=np.float64)
    base_duration = np.asarray(instance["duration_matrix_min"], dtype=np.float64)
    departure_hour = float(instance.get("departure_hour", 8.0))
    total_distance = 0.0
    elapsed_min = 0.0
    for u, v in zip(route, route[1:]):
        hour = (departure_hour + elapsed_min / 60.0) % 24.0
        leg_min = float(base_duration[u, v]) * compute_traffic_multiplier(hour)
        total_distance += float(dist[u, v])
        elapsed_min += leg_min
    return total_distance, elapsed_min


class TrafficTSPEnv(gym.Env):
    """
    Gymnasium Environment for Time-Dependent Traveling Salesperson Problem (TD-TSP).
    Node 0 is always the Depot. Nodes 1..N are delivery stops.
    Episode ends when all stops are visited and the vehicle returns to the depot.
    """

    metadata = {"render_modes": ["ansi"]}

    def __init__(
        self,
        instance_dict: Optional[Dict[str, Any]] = None,
        alpha_dist: float = 0.4,
        beta_duration: float = 0.6,
        gamma_peak_penalty: float = 2.0,
        fixed_max_nodes: int = 20,
    ):
        super().__init__()
        self.alpha_dist = alpha_dist
        self.beta_duration = beta_duration
        self.gamma_peak_penalty = gamma_peak_penalty
        self.fixed_max_nodes = fixed_max_nodes

        self.instance_dict = instance_dict
        if instance_dict is not None:
            self._load_instance(instance_dict)
        else:
            self._load_default_instance()

    def _load_instance(self, inst: Dict[str, Any]):
        self.instance_id = inst.get("instance_id", "custom_inst")
        self.num_stops = inst.get("num_stops", len(inst.get("stops", [])))
        self.total_nodes = self.num_stops + 1  # 0 is depot, 1..N are stops

        self.dist_matrix = np.array(inst["dist_matrix_km"], dtype=np.float32)
        self.duration_matrix = np.array(inst["duration_matrix_min"], dtype=np.float32)

        depot = inst.get("depot", {"lat": 10.8012, "lon": 106.7145})
        coords = [[depot["lat"], depot["lon"]]]
        for s in inst.get("stops", []):
            coords.append([s["lat"], s["lon"]])
        self.coords = np.array(coords, dtype=np.float32)
        coord_min = self.coords.min(axis=0)
        coord_range = np.maximum(self.coords.max(axis=0) - coord_min, 1e-6)
        self.normalized_coords = (self.coords - coord_min) / coord_range

        self.departure_hour = float(inst.get("departure_hour", 8.0))
        self.visited = np.zeros(self.total_nodes, dtype=bool)
        self.visited[0] = True
        self.current_node = 0
        self.current_time_min = 0.0

        # Action space: choice of next node to visit [0 .. total_nodes - 1]
        self.action_space = spaces.Discrete(self.total_nodes)

        # Observation space
        self.observation_space = spaces.Dict({
            "current_node": spaces.Discrete(self.total_nodes),
            "visited": spaces.MultiBinary(self.total_nodes),
            "current_time_min": spaces.Box(low=0.0, high=1440.0, shape=(1,), dtype=np.float32),
            "traffic_factor": spaces.Box(low=1.0, high=3.0, shape=(1,), dtype=np.float32),
        })

    def _load_default_instance(self):
        bench_path = Path("data/benchmark_100_vietnam_pois.json")
        if bench_path.exists():
            with open(bench_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._load_instance(data["instances"][0])
        else:
            # Fallback tiny synthetic instance
            n = 10
            rng = np.random.RandomState(42)
            coords = rng.uniform(10.7, 10.9, size=(n + 1, 2)).astype(np.float32)
            dist_mat = np.zeros((n + 1, n + 1), dtype=np.float32)
            for i in range(n + 1):
                for j in range(n + 1):
                    dist_mat[i, j] = np.linalg.norm(coords[i] - coords[j]) * 111.0
            time_mat = dist_mat / (25.0 / 60.0)
            self._load_instance({
                "instance_id": "default_synth_N10",
                "num_stops": n,
                "depot": {"lat": coords[0, 0], "lon": coords[0, 1]},
                "stops": [{"lat": coords[i, 0], "lon": coords[i, 1]} for i in range(1, n + 1)],
                "departure_hour": 8.0,
                "dist_matrix_km": dist_mat.tolist(),
                "duration_matrix_min": time_mat.tolist()
            })

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        super().reset(seed=seed)
        if options and "instance" in options:
            self._load_instance(options["instance"])

        self.current_node = 0  # Start at Depot
        self.visited = np.zeros(self.total_nodes, dtype=bool)
        self.visited[0] = True  # Depot is initial starting point
        self.route_history = [0]
        self.current_time_min = 0.0
        self.total_dist_km = 0.0
        self.total_duration_min = 0.0
        self.total_cost = 0.0

        current_hour = (self.departure_hour + self.current_time_min / 60.0) % 24.0
        self.current_traffic_factor = compute_traffic_multiplier(current_hour)

        obs = self._get_obs()
        info = {
            "valid_action_mask": self.get_valid_action_mask(),
            "remaining_stops": int(np.sum(~self.visited[1:])),
            "instance_id": self.instance_id
        }
        return obs, info

    def get_valid_action_mask(self) -> np.ndarray:
        """
        Binary mask of valid actions.
        Unvisited stops (1..N) are valid.
        Depot (0) is valid ONLY when all stops (1..N) have been visited.
        """
        mask = np.zeros(self.total_nodes, dtype=bool)
        unvisited_stops = np.where(~self.visited[1:])[0] + 1
        if len(unvisited_stops) > 0:
            mask[unvisited_stops] = True
        else:
            mask[0] = True  # Return to depot allowed only at the end
        return mask

    def step(self, action: int) -> Tuple[Dict[str, Any], float, bool, bool, Dict[str, Any]]:
        action = int(action)
        mask = self.get_valid_action_mask()

        # Infeasible action check
        if action < 0 or action >= len(mask) or not mask[action]:
            # Heavy penalty for invalid action
            penalty = -100.0
            return self._get_obs(), penalty, False, False, {
                "error": "infeasible_action",
                "action": action,
                "valid_mask": mask
            }

        prev_node = self.current_node
        curr_hour = (self.departure_hour + self.current_time_min / 60.0) % 24.0
        c_t = compute_traffic_multiplier(curr_hour)

        dist = float(self.dist_matrix[prev_node, action])
        base_dur = float(self.duration_matrix[prev_node, action])
        adj_dur = base_dur * c_t

        edge_cost = self.alpha_dist * dist + self.beta_duration * adj_dur

        peak_penalty = 0.0
        if c_t >= 2.0:
            peak_penalty = self.gamma_peak_penalty * (c_t - 1.0)

        step_reward = - (edge_cost + peak_penalty)

        # Update state
        self.current_node = action
        self.visited[action] = True
        self.route_history.append(action)
        self.current_time_min += adj_dur
        self.total_dist_km += dist
        self.total_duration_min += adj_dur
        self.total_cost += edge_cost + peak_penalty

        # Episode termination: back at depot and all stops visited
        terminated = bool(self.current_node == 0 and np.all(self.visited[1:]))

        obs = self._get_obs()
        info = {
            "valid_action_mask": self.get_valid_action_mask() if not terminated else np.zeros(self.total_nodes, dtype=bool),
            "step_edge_cost": edge_cost,
            "step_dist_km": dist,
            "step_duration_min": adj_dur,
            "traffic_factor": c_t,
            "total_dist_km": self.total_dist_km,
            "total_duration_min": self.total_duration_min,
            "total_cost": self.total_cost,
            "route": list(self.route_history)
        }
        return obs, float(step_reward), terminated, False, info

    def _get_obs(self) -> Dict[str, Any]:
        curr_hour = (self.departure_hour + self.current_time_min / 60.0) % 24.0
        return {
            "current_node": int(self.current_node),
            "visited": self.visited.copy(),
            "current_time_min": np.array([self.current_time_min], dtype=np.float32),
            "traffic_factor": np.array([compute_traffic_multiplier(curr_hour)], dtype=np.float32),
        }

    def get_dqn_state_vector(self, max_nodes: int = 20) -> Tuple[np.ndarray, np.ndarray]:
        """
        Produce fixed-length 1D state vector for Model 1 (DQN MLP with action masking).
        Pads or truncates to max_nodes + 1 (depot + max_nodes stops).
        Returns:
            (state_vector, action_mask)
        """
        dim = max_nodes + 1
        mask = np.zeros(dim, dtype=bool)
        raw_mask = self.get_valid_action_mask()
        for i in range(min(self.total_nodes, dim)):
            mask[i] = raw_mask[i]

        # Flattened features:
        # [current_x, current_y, departure_hour, current_time_min, traffic_factor] (5)
        # + visited_mask_padded (dim)
        # + dist_to_all_nodes_padded (dim)
        curr_coord = self.normalized_coords[self.current_node]
        curr_hour = (self.departure_hour + self.current_time_min / 60.0) % 24.0
        c_t = compute_traffic_multiplier(curr_hour)

        base_feats = np.array([
            curr_coord[0], curr_coord[1],
            self.departure_hour / 24.0,
            self.current_time_min / 360.0,
            c_t / 3.0
        ], dtype=np.float32)

        visited_padded = np.ones(dim, dtype=np.float32)  # Default padded nodes marked visited
        for i in range(min(self.total_nodes, dim)):
            visited_padded[i] = 1.0 if self.visited[i] else 0.0

        dist_padded = np.zeros(dim, dtype=np.float32)
        for i in range(min(self.total_nodes, dim)):
            dist_padded[i] = self.dist_matrix[self.current_node, i] / 20.0

        flat_vector = np.concatenate([base_feats, visited_padded, dist_padded], axis=0).astype(np.float32)
        return flat_vector, mask

