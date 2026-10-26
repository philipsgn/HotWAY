"""Google OR-Tools VRPTW Solver Baseline.

Solves Vehicle Routing Problem with Time Windows using MIP routing model.
Includes graceful fallback to Greedy if OR-Tools is unavailable.

Authoritative References:
- PRD.md §3.4
- survey_rl.md §3.3
- TEST_INFRA.md Feature 14
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List
import networkx as nx

from src.baselines import BaselineResult
from src.baselines.greedy_solver import GreedyNearestSolver
from src.rl.delivery_env import HangGonDeliveryEnv

logger = logging.getLogger("hotway.baselines.ortools")

try:
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2
    HAS_ORTOOLS = True
except ImportError:
    HAS_ORTOOLS = False
    logger.warning("google-ortools not installed. ORToolsVRPSolver will fallback to Greedy.")


class ORToolsVRPSolver:
    """Combinatorial VRP solver using Google OR-Tools with Time Windows."""

    def __init__(self, name: str = "OR_Tools_VRPTW", time_limit_seconds: int = 3):
        self.name = name
        self.time_limit_seconds = time_limit_seconds

    def solve(self, env: HangGonDeliveryEnv) -> BaselineResult:
        if not HAS_ORTOOLS:
            logger.info("Falling back to GreedyNearestSolver due to missing OR-Tools.")
            fallback = GreedyNearestSolver(name=f"{self.name}_GreedyFallback")
            return fallback.solve(env)

        start_clock = time.perf_counter()

        nodes = [env.depot_node] + [o.dest_node for o in env.orders]
        n_locations = len(nodes)

        time_matrix = [[0] * n_locations for _ in range(n_locations)]
        dist_matrix = [[0] * n_locations for _ in range(n_locations)]

        for i in range(n_locations):
            for j in range(n_locations):
                if i != j:
                    try:
                        d = nx.shortest_path_length(env.graph, nodes[i], nodes[j], weight="length")
                    except (nx.NetworkXNoPath, nx.NodeNotFound):
                        d = 1000.0
                    dist_matrix[i][j] = int(d)
                    time_matrix[i][j] = int(d / 8.33)  # ~30 km/h = 8.33 m/s

        time_windows = [(0, 7200)]  # Depot open window
        for o in env.orders:
            remaining_sec = max(300, int((o.deadline_minutes - env.tau_current) * 60))
            time_windows.append((0, remaining_sec))

        try:
            manager = pywrapcp.RoutingIndexManager(n_locations, 1, 0)
            routing = pywrapcp.RoutingModel(manager)

            def time_callback(from_index, to_index):
                from_node = manager.IndexToNode(from_index)
                to_node = manager.IndexToNode(to_index)
                service = 120 if from_node != 0 else 0
                return time_matrix[from_node][to_node] + service

            transit_callback_index = routing.RegisterTransitCallback(time_callback)
            routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

            time_dimension_name = "Time"
            routing.AddDimension(
                transit_callback_index,
                1800,   # 30 min max waiting time
                10800,  # 3 hours horizon
                False,  # don't force start cumul to zero
                time_dimension_name,
            )
            time_dimension = routing.GetDimensionOrDie(time_dimension_name)

            for loc_idx, (open_t, close_t) in enumerate(time_windows):
                index = manager.NodeToIndex(loc_idx)
                time_dimension.CumulVar(index).SetRange(open_t, close_t)

            search_parameters = pywrapcp.DefaultRoutingSearchParameters()
            search_parameters.first_solution_strategy = (
                routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
            )
            search_parameters.local_search_metaheuristic = (
                routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
            )
            search_parameters.time_limit.seconds = self.time_limit_seconds

            solution = routing.SolveWithParameters(search_parameters)

            if not solution:
                logger.warning("OR-Tools failed to find feasible route. Falling back to Greedy.")
                fallback = GreedyNearestSolver(name=f"{self.name}_GreedyFallback")
                return fallback.solve(env)

            index = routing.Start(0)
            order_sequence: List[int] = []
            while not routing.IsEnd(index):
                node_idx = manager.IndexToNode(index)
                if node_idx > 0:
                    order_sequence.append(node_idx - 1)
                index = solution.Value(routing.NextVar(index))

        except Exception as e:
            logger.warning("OR-Tools raised exception: %s. Falling back to Greedy.", e)
            fallback = GreedyNearestSolver(name=f"{self.name}_GreedyFallback")
            return fallback.solve(env)

        total_reward = 0.0
        delivered_temps: Dict[str, float] = {}
        route_nodes: List[Any] = [env.depot_node]

        for action in order_sequence:
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            order = env.orders[action]
            delivered_temps[order.order_id] = order.final_temp_c
            route_nodes.append(order.dest_node)

        # Return to depot
        obs, reward, terminated, truncated, info = env.step(env.ACTION_RETURN_DEPOT)
        total_reward += reward
        route_nodes.append(env.depot_node)

        solve_latency_ms = (time.perf_counter() - start_clock) * 1000.0

        temps = list(delivered_temps.values())
        avg_temp = float(sum(temps) / len(temps)) if temps else 0.0
        min_temp = float(min(temps)) if temps else 0.0
        on_time_count = sum(
            1 for o in env.orders if o.delivered and o.delivery_time_min <= o.deadline_minutes
        )
        on_time_rate = float(on_time_count / len(env.orders)) if env.orders else 0.0

        total_time = env.tau_current - env.tau_start
        total_dist_km = 0.0
        for i in range(len(route_nodes) - 1):
            try:
                l = nx.shortest_path_length(env.graph, route_nodes[i], route_nodes[i + 1], weight="length")
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                l = 1000.0
            total_dist_km += l / 1000.0

        return BaselineResult(
            algorithm=self.name,
            route_nodes=route_nodes,
            order_sequence=order_sequence,
            total_time_min=total_time,
            total_distance_km=total_dist_km,
            delivered_temps=delivered_temps,
            avg_delivered_temp_c=avg_temp,
            min_delivered_temp_c=min_temp,
            on_time_rate=on_time_rate,
            total_reward=total_reward,
            solve_latency_ms=solve_latency_ms,
        )
