"""Time-Dependent Urban TSP Environment for HCMC Motorbike Logistics.
Simulates traffic dynamics using empirical peak-hour multiplier function C(t).
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import torch


def get_congestion_factor(hour_of_day: float) -> float:
    """Empirical congestion multiplier function C(t) for TP.HCM urban traffic."""
    h = hour_of_day % 24.0

    if 22.0 <= h or h < 6.0:
        return 1.00  # Off-peak night
    elif 6.0 <= h < 7.0:
        return 1.15  # Early morning buildup
    elif 7.0 <= h < 8.5:
        return 2.10  # Peak morning rush (Điện Biên Phủ, Xô Viết Nghệ Tĩnh)
    elif 8.5 <= h < 11.5:
        return 1.25  # Mid-morning
    elif 11.5 <= h < 13.5:
        return 1.35  # Mid-day lunch traffic
    elif 13.5 <= h < 16.5:
        return 1.20  # Afternoon normal
    elif 16.5 <= h < 19.0:
        return 2.25  # Peak evening rush
    elif 19.0 <= h < 22.0:
        return 1.30  # Evening normal
    return 1.00


class TimeDependentTSPEnv:
    """TSP Environment with time-dependent transit costs and real road graph topologies."""

    def __init__(
        self,
        matrix_path: str = "data/matrix_standard.npz",
        address_pool_path: str = "data/address_pool_standard.json",
        default_speed_kmh: float = 24.0,
    ):
        self.default_speed_kmh = default_speed_kmh
        self.matrix_path = Path(matrix_path)
        self.address_pool_path = Path(address_pool_path)

        # Load distance & base duration matrices
        if self.matrix_path.exists():
            data = np.load(self.matrix_path)
            self.dist_matrix = data["dist_matrix"]  # meters
            self.time_matrix = data["time_matrix"]  # seconds
        else:
            # Fallback synthetic matrix if data path not mounted
            self.dist_matrix = np.ones((50, 50)) * 1500.0
            np.fill_diagonal(self.dist_matrix, 0.0)
            self.time_matrix = self.dist_matrix / (default_speed_kmh * 1000.0 / 3600.0)

        # Load address coordinates
        if self.address_pool_path.exists():
            with open(self.address_pool_path, "r", encoding="utf-8") as f:
                self.addresses = json.load(f)
        else:
            self.addresses = [
                {"id": f"ADDR_{i}", "lat": 10.8016 + i * 0.001, "lon": 106.7115 + i * 0.001}
                for i in range(len(self.dist_matrix))
            ]

    def generate_batch(
        self,
        batch_size: int,
        n_nodes: int = 20,
        departure_hour_range: Tuple[float, float] = (7.0, 9.0),
        seed: int = None,
    ) -> Dict[str, torch.Tensor]:
        """Generate a batch of instances for Attention Model training.
        
        Each instance consists of:
        - Depot (node 0) + (n_nodes - 1) delivery points sampled from address pool.
        - Node features: [norm_lat, norm_lon, departure_hour_norm].
        """
        if seed is not None:
            np.random.seed(seed)

        total_pool_size = len(self.addresses)
        nodes_batch = []
        indices_batch = []
        dep_hours = []

        for _ in range(batch_size):
            # Select random subset of addresses
            sampled_indices = np.random.choice(total_pool_size, size=n_nodes, replace=False)
            indices_batch.append(sampled_indices)

            dep_hour = np.random.uniform(departure_hour_range[0], departure_hour_range[1])
            dep_hours.append(dep_hour)

            coords = []
            for idx in sampled_indices:
                addr = self.addresses[idx]
                norm_lat = (addr["lat"] - 10.70) / 0.20  # Normalized to [0, 1] for HCMC
                norm_lon = (addr["lon"] - 106.60) / 0.20
                coords.append([norm_lat, norm_lon, dep_hour / 24.0])

            nodes_batch.append(coords)

        return {
            "nodes": torch.tensor(nodes_batch, dtype=torch.float32),
            "indices": np.array(indices_batch),
            "departure_hours": np.array(dep_hours),
        }

    def evaluate_tour(
        self,
        tour: np.ndarray,
        node_indices: np.ndarray,
        departure_hour: float,
    ) -> Dict[str, float]:
        """Compute exact cumulative duration and distance for a decoded tour.
        
        Args:
            tour: Permutation array [0, pi_1, pi_2, ..., pi_{n-1}]
            node_indices: Indices in the full address pool/matrix
            departure_hour: Start time in hours (e.g. 7.5 = 7:30 AM)
        """
        curr_time_sec = departure_hour * 3600.0
        total_dist_m = 0.0
        n = len(tour)

        for i in range(n):
            u_local = tour[i]
            v_local = tour[(i + 1) % n]  # Return to depot at end

            u_global = node_indices[u_local]
            v_global = node_indices[v_local]

            base_dist = float(self.dist_matrix[u_global, v_global])
            base_dur_sec = float(self.time_matrix[u_global, v_global])

            # Apply dynamic congestion factor at current clock time
            clock_hour = (curr_time_sec / 3600.0) % 24.0
            c_factor = get_congestion_factor(clock_hour)
            actual_dur_sec = base_dur_sec * c_factor

            total_dist_m += base_dist
            curr_time_sec += actual_dur_sec

        total_duration_min = (curr_time_sec - departure_hour * 3600.0) / 60.0
        total_dist_km = total_dist_m / 1000.0

        return {
            "duration_min": round(total_duration_min, 2),
            "distance_km": round(total_dist_km, 2),
            "congestion_penalty_min": round(total_duration_min - (total_dist_km / (self.default_speed_kmh / 60.0)), 2),
        }
