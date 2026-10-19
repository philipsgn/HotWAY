"""Baseline Routing Solvers (Dijkstra, Greedy Nearest-Neighbor, OR-Tools VRP)."""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class BaselineResult:
    """Standardized output from baseline solvers."""
    algorithm: str
    route_nodes: List[Any]
    order_sequence: List[int]
    total_time_min: float
    total_distance_km: float
    delivered_temps: Dict[str, float]
    avg_delivered_temp_c: float
    min_delivered_temp_c: float
    on_time_rate: float
    total_reward: float
    solve_latency_ms: float


from src.baselines.dijkstra_router import DijkstraRouter
from src.baselines.greedy_solver import GreedyNearestSolver
from src.baselines.ortools_vrp import ORToolsVRPSolver

__all__ = [
    "BaselineResult",
    "DijkstraRouter",
    "GreedyNearestSolver",
    "ORToolsVRPSolver",
]
