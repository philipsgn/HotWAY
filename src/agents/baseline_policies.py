"""
Baseline Policies for Real-Time Adaptive Routing (T3 Layer).
Implements Static Dijkstra and Dynamic (At-Every-Node) Dijkstra Rerouting.
"""

from __future__ import annotations

from typing import Any, List, Optional
import networkx as nx


class StaticDijkstraPolicy:
    """Precomputes fixed path at departure using average/free-flow travel times."""

    def __init__(self, env: Any):
        self.env = env
        self.cached_path: List[int] = []

    def reset(self, source: int, target: int) -> None:
        G_time = nx.DiGraph()
        for u in self.env.nodes:
            for v in self.env.adj[u]:
                edge_data = self.env.graph[u][v]
                length_m = float(edge_data.get("length", 50.0))
                hw = str(edge_data.get("highway", "residential"))
                # Base expected travel time
                t_sec = self.env.traffic_provider.get_edge_travel_time_sec(
                    u, v, length_m, hw, time_of_day_min=480.0, rain=False
                )
                G_time.add_edge(u, v, weight=t_sec)

        try:
            self.cached_path = nx.shortest_path(G_time, source, target, weight="weight")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            self.cached_path = []

    def select_action(self, current_node: int) -> int:
        succs = self.env.adj[current_node]
        if not succs:
            return 0

        if current_node in self.cached_path:
            idx = self.cached_path.index(current_node)
            if idx + 1 < len(self.cached_path):
                next_planned = self.cached_path[idx + 1]
                if next_planned in succs:
                    return succs.index(next_planned)

        # Fallback to shortest length if off-route
        return min(range(len(succs)), key=lambda i: self.env.graph[current_node][succs[i]].get("length", 1e9))


class DynamicDijkstraPolicy:
    """
    Recomputes Dijkstra shortest path dynamically at every single decision node
    using instantaneous observed edge travel times.
    """

    def __init__(self, env: Any):
        self.env = env

    def select_action(self, current_node: int, target_node: int) -> int:
        succs = self.env.adj[current_node]
        if not succs:
            return 0

        # Construct instantaneous weighted graph
        G_instant = nx.DiGraph()
        for u in self.env.nodes:
            for v in self.env.adj[u]:
                edge_data = self.env.graph[u][v]
                length_m = float(edge_data.get("length", 50.0))
                hw = str(edge_data.get("highway", "residential"))
                t_sec = self.env.traffic_provider.get_edge_travel_time_sec(
                    u, v, length_m, hw, self.env.current_time_min, self.env.rain
                )
                G_instant.add_edge(u, v, weight=t_sec)

        try:
            path = nx.shortest_path(G_instant, current_node, target_node, weight="weight")
            if len(path) >= 2:
                next_node = path[1]
                if next_node in succs:
                    return succs.index(next_node)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            pass

        return 0
