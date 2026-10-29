"""
Model 4: Google OR-Tools Routing Engine (Industrial Benchmark).
Constraint Programming (CP) engine with Guided Local Search (GLS) meta-heuristics.
Provides a bounded-time heuristic reference; it does not certify optimality.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from env.traffic_tsp_env import simulate_route

try:
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False


class ORToolsSolver:
    """Bounded-time OR-Tools routing heuristic with dynamic post-solve scoring."""

    def __init__(self, time_limit_sec: int = 5):
        self.time_limit_sec = time_limit_sec

    def solve(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.perf_counter()

        num_stops = instance.get("num_stops", len(instance.get("stops", [])))
        total_nodes = num_stops + 1

        dist_mat = np.array(instance["dist_matrix_km"], dtype=np.float32)
        dur_mat = np.array(instance["duration_matrix_min"], dtype=np.float32)
        dep_hour = float(instance.get("departure_hour", 8.0))

        # Base cost matrix combining distance and base duration with initial hour C(t)
        # Static surrogate objective; route duration is re-simulated dynamically below.
        cost_mat = 0.4 * dist_mat + 0.6 * dur_mat
        # Scale to integer for OR-Tools CP solver
        scaled_cost = (cost_mat * 1000).astype(int).tolist()

        route = [0]
        if ORTOOLS_AVAILABLE:
            manager = pywrapcp.RoutingIndexManager(total_nodes, 1, 0)
            routing = pywrapcp.RoutingModel(manager)

            def distance_callback(from_idx: int, to_idx: int) -> int:
                f = manager.IndexToNode(from_idx)
                t = manager.IndexToNode(to_idx)
                return scaled_cost[f][t]

            transit_callback_index = routing.RegisterTransitCallback(distance_callback)
            routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

            search_parameters = pywrapcp.DefaultRoutingSearchParameters()
            search_parameters.first_solution_strategy = (
                routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
            )
            search_parameters.local_search_metaheuristic = (
                routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
            )
            search_parameters.time_limit.seconds = self.time_limit_sec

            solution = routing.SolveWithParameters(search_parameters)
            if solution:
                index = routing.Start(0)
                route = []
                while not routing.IsEnd(index):
                    node = manager.IndexToNode(index)
                    route.append(node)
                    index = solution.Value(routing.NextVar(index))
                route.append(0)
            else:
                route = self._fallback_nearest_neighbor(cost_mat)
        else:
            route = self._fallback_nearest_neighbor(cost_mat)

        solve_time_ms = (time.perf_counter() - start_time) * 1000.0

        # Calculate exact dynamic duration and distance under C(t)
        total_dist, total_dur = simulate_route(instance, route)

        return {
            "model": "Google OR-Tools (Guided Local Search)",
            "route": route,
            "total_dist_km": round(float(total_dist), 2),
            "total_duration_min": round(float(total_dur), 2),
            "solve_time_ms": round(solve_time_ms, 2),
            "valid": len(route) == total_nodes + 1 and len(set(route[:-1])) == total_nodes
        }

    def _fallback_nearest_neighbor(self, cost_mat: np.ndarray) -> List[int]:
        n = len(cost_mat)
        visited = [False] * n
        visited[0] = True
        curr = 0
        route = [0]
        for _ in range(n - 1):
            best_next = -1
            best_cost = 1e9
            for j in range(n):
                if not visited[j] and cost_mat[curr, j] < best_cost:
                    best_cost = cost_mat[curr, j]
                    best_next = j
            visited[best_next] = True
            route.append(best_next)
            curr = best_next
        route.append(0)
        return route

