"""Dijkstra Shortest Path Baseline Router.

Optimizes static road network shortest paths without thermal or dynamic traffic awareness.
Dispatches orders sequentially in First-Come-First-Served (FCFS) order then returns to depot.

Authoritative References:
- PRD.md §3.4
- survey_rl.md §3.1
- TEST_INFRA.md Feature 12
"""

from __future__ import annotations

import time
from typing import Any, Dict, List
import networkx as nx

from src.baselines import BaselineResult
from src.rl.delivery_env import HangGonDeliveryEnv


class DijkstraRouter:
    """Baseline solver using Dijkstra shortest path routing."""

    def __init__(self, name: str = "Dijkstra_Static"):
        self.name = name

    def solve(self, env: HangGonDeliveryEnv) -> BaselineResult:
        """Executes delivery orders in sequential order (0..M-1) then returns to depot.

        Evaluates physical performance against the exact environmental step dynamics.
        """
        start_clock = time.perf_counter()
        order_sequence = list(range(env.max_orders))

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

        # Extract summary metrics
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
