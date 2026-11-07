"""
Graph Step-by-Step Pathfinding Engine for Interactive Algorithm Visualization.
Supports:
1. Dijkstra (Uniform Cost Radial Wavefront)
2. A* Search (Heuristic-Guided Elliptical Wavefront)
3. Bidirectional Search (Dual Fronts Meeting in the Center)
4. HotWAY Dynamic Dijkstra (Traffic Congestion C(t) Adaptive Wavefront)
"""

from __future__ import annotations

import heapq
import math
import pickle
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx
import numpy as np
from scipy.spatial import KDTree

EARTH_RADIUS_METERS = 6371000.0


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance in meters between two WGS84 GPS points."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    return EARTH_RADIUS_METERS * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


class GraphStepEngine:
    _instance: Optional["GraphStepEngine"] = None

    def __init__(self, graph_path: Optional[Path] = None):
        if graph_path is None:
            # Check candidate locations
            candidates = [
                Path("data/visualizer_graph_scc.pickle"),
                Path("data/hcmc_compact_graph.pickle"),
            ]
            for c in candidates:
                if c.exists():
                    graph_path = c
                    break

        if not graph_path or not graph_path.exists():
            raise FileNotFoundError("Could not find visualizer graph file.")

        with open(graph_path, "rb") as f:
            self.graph: nx.MultiDiGraph = pickle.load(f)

        self.nodes_list = list(self.graph.nodes())
        self.coords_array = np.array([
            [self.graph.nodes[n]["y"], self.graph.nodes[n]["x"]]
            for n in self.nodes_list
        ], dtype=np.float64)

        # Build KDTree for sub-millisecond nearest node search
        self.kdtree = KDTree(self.coords_array)

        # Calculate bounding box
        min_lat, min_lon = self.coords_array.min(axis=0)
        max_lat, max_lon = self.coords_array.max(axis=0)
        self.bounds = {
            "min_lat": float(min_lat),
            "max_lat": float(max_lat),
            "min_lon": float(min_lon),
            "max_lon": float(max_lon),
            "center": [float((min_lat + max_lat) / 2.0), float((min_lon + max_lon) / 2.0)],
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
        }

    @classmethod
    def get_instance(cls) -> "GraphStepEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def find_nearest_node(self, lat: float, lon: float) -> Tuple[int, float, float]:
        """Finds nearest node in graph and returns (node_id, lat, lon)."""
        dist, idx = self.kdtree.query([lat, lon])
        node_id = self.nodes_list[idx]
        node_data = self.graph.nodes[node_id]
        return node_id, float(node_data["y"]), float(node_data["x"])

    def solve(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        algorithm: str = "a_star",
        max_steps: int = 1200,
    ) -> Dict[str, Any]:
        """Executes selected algorithm and records chronological exploration steps."""
        if not (-90.0 <= start_lat <= 90.0 and -180.0 <= start_lon <= 180.0):
            raise ValueError(f"Invalid start coordinates: ({start_lat}, {start_lon})")
        if not (-90.0 <= end_lat <= 90.0 and -180.0 <= end_lon <= 180.0):
            raise ValueError(f"Invalid end coordinates: ({end_lat}, {end_lon})")

        start_node, s_lat, s_lon = self.find_nearest_node(start_lat, start_lon)
        end_node, e_lat, e_lon = self.find_nearest_node(end_lat, end_lon)

        t0 = time.perf_counter()

        algo_lower = algorithm.lower().replace("-", "_").replace(" ", "_")
        if algo_lower in ("a_star", "astar", "a*"):
            steps, path, final_cost = self._run_astar(start_node, end_node)
            algo_display = "A* Search (Heuristic-Guided)"
        elif algo_lower in ("bidirectional", "bi_directional", "bi_astar"):
            steps, path, final_cost = self._run_bidirectional(start_node, end_node)
            algo_display = "Bidirectional Search (Dual Wavefront)"
        elif algo_lower in ("dynamic_c_t", "dynamic", "rl", "dynamic_dijkstra"):
            steps, path, final_cost = self._run_dynamic_c_t(start_node, end_node)
            algo_display = "HotWAY Dynamic Dijkstra (Traffic C(t) Adaptive)"
        else:
            steps, path, final_cost = self._run_dijkstra(start_node, end_node)
            algo_display = "Dijkstra (Uniform Cost Search)"

        compute_ms = (time.perf_counter() - t0) * 1000.0

        # Sample steps if too large to ensure 60 FPS animation performance
        sampled_steps = self._sample_steps(steps, max_steps)

        # Build path coordinates
        path_coords = [
            [float(self.graph.nodes[n]["y"]), float(self.graph.nodes[n]["x"])]
            for n in path
        ]

        # Calculate actual path length in km
        total_dist_m = 0.0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            if self.graph.has_edge(u, v):
                min_l = min(d.get("length", 10.0) for d in self.graph[u][v].values())
            else:
                nd_u = self.graph.nodes[u]
                nd_v = self.graph.nodes[v]
                min_l = haversine(float(nd_u["y"]), float(nd_u["x"]), float(nd_v["y"]), float(nd_v["x"]))
            total_dist_m += min_l

        return {
            "algorithm": algo_display,
            "algorithm_id": algo_lower,
            "start": {"id": start_node, "lat": s_lat, "lon": s_lon},
            "destination": {"id": end_node, "lat": e_lat, "lon": e_lon},
            "metrics": {
                "compute_time_ms": round(compute_ms, 2),
                "total_steps_recorded": len(steps),
                "sampled_steps_count": len(sampled_steps),
                "nodes_visited_count": len(steps),
                "distance_km": round(total_dist_m / 1000.0, 3),
                "estimated_time_min": round((total_dist_m / 1000.0) / 25.0 * 60.0, 1),
            },
            "steps": sampled_steps,
            "final_path": path_coords,
        }

    def _run_dijkstra(self, start: int, target: int) -> Tuple[List[Dict[str, Any]], List[int], float]:
        """Standard Dijkstra algorithm with step recording."""
        distances: Dict[int, float] = {start: 0.0}
        predecessors: Dict[int, int] = {}
        visited: Set[int] = set()
        pq: List[Tuple[float, int]] = [(0.0, start)]
        steps: List[Dict[str, Any]] = []

        step_idx = 0
        found = False

        while pq:
            cost, u = heapq.heappop(pq)
            if u in visited:
                continue
            visited.add(u)
            step_idx += 1

            u_node = self.graph.nodes[u]
            u_lat, u_lon = float(u_node["y"]), float(u_node["x"])

            # Sample current frontier (top 5 from pq)
            frontier_sample = [
                [float(self.graph.nodes[item[1]]["y"]), float(self.graph.nodes[item[1]]["x"])]
                for item in pq[:5]
                if item[1] in self.graph
            ]

            steps.append({
                "i": step_idx,
                "lat": u_lat,
                "lon": u_lon,
                "cost": round(cost, 1),
                "frontier": frontier_sample,
                "dir": "fwd",
            })

            if u == target:
                found = True
                break

            for v in self.graph.neighbors(u):
                if v in visited:
                    continue
                min_len = min(d.get("length", 10.0) for d in self.graph[u][v].values())
                new_cost = cost + min_len
                if new_cost < distances.get(v, float("inf")):
                    distances[v] = new_cost
                    predecessors[v] = u
                    heapq.heappush(pq, (new_cost, v))

        path = self._reconstruct_path(predecessors, start, target) if found else []
        return steps, path, distances.get(target, 0.0)

    def _run_astar(self, start: int, target: int) -> Tuple[List[Dict[str, Any]], List[int], float]:
        """A* Search algorithm using Haversine heuristic."""
        t_node = self.graph.nodes[target]
        t_lat, t_lon = float(t_node["y"]), float(t_node["x"])

        def h(node_id: int) -> float:
            nd = self.graph.nodes[node_id]
            return haversine(float(nd["y"]), float(nd["x"]), t_lat, t_lon)

        g_scores: Dict[int, float] = {start: 0.0}
        f_scores: Dict[int, float] = {start: h(start)}
        predecessors: Dict[int, int] = {}
        visited: Set[int] = set()
        pq: List[Tuple[float, float, int]] = [(f_scores[start], 0.0, start)]
        steps: List[Dict[str, Any]] = []

        step_idx = 0
        found = False

        while pq:
            f, g, u = heapq.heappop(pq)
            if u in visited:
                continue
            visited.add(u)
            step_idx += 1

            u_node = self.graph.nodes[u]
            u_lat, u_lon = float(u_node["y"]), float(u_node["x"])

            frontier_sample = [
                [float(self.graph.nodes[item[2]]["y"]), float(self.graph.nodes[item[2]]["x"])]
                for item in pq[:5]
                if item[2] in self.graph
            ]

            steps.append({
                "i": step_idx,
                "lat": u_lat,
                "lon": u_lon,
                "cost": round(g, 1),
                "f_score": round(f, 1),
                "frontier": frontier_sample,
                "dir": "fwd",
            })

            if u == target:
                found = True
                break

            for v in self.graph.neighbors(u):
                if v in visited:
                    continue
                min_len = min(d.get("length", 10.0) for d in self.graph[u][v].values())
                tentative_g = g + min_len
                if tentative_g < g_scores.get(v, float("inf")):
                    g_scores[v] = tentative_g
                    f_scores[v] = tentative_g + h(v)
                    predecessors[v] = u
                    heapq.heappush(pq, (f_scores[v], tentative_g, v))

        path = self._reconstruct_path(predecessors, start, target) if found else []
        return steps, path, g_scores.get(target, 0.0)

    def _run_bidirectional(self, start: int, target: int) -> Tuple[List[Dict[str, Any]], List[int], float]:
        """Bidirectional Dijkstra search meeting in the middle."""
        dist_fwd: Dict[int, float] = {start: 0.0}
        dist_bwd: Dict[int, float] = {target: 0.0}
        pred_fwd: Dict[int, int] = {}
        pred_bwd: Dict[int, int] = {}
        visited_fwd: Set[int] = set()
        visited_bwd: Set[int] = set()

        pq_fwd: List[Tuple[float, int]] = [(0.0, start)]
        pq_bwd: List[Tuple[float, int]] = [(0.0, target)]

        steps: List[Dict[str, Any]] = []
        step_idx = 0
        meeting_node: Optional[int] = None

        while pq_fwd and pq_bwd:
            # Forward step
            cost_f, u_f = heapq.heappop(pq_fwd)
            if u_f not in visited_fwd:
                visited_fwd.add(u_f)
                step_idx += 1
                nd_f = self.graph.nodes[u_f]
                steps.append({
                    "i": step_idx,
                    "lat": float(nd_f["y"]),
                    "lon": float(nd_f["x"]),
                    "cost": round(cost_f, 1),
                    "dir": "fwd",
                })
                if u_f in visited_bwd:
                    meeting_node = u_f
                    break
                for v in self.graph.neighbors(u_f):
                    if v not in visited_fwd:
                        min_l = min(d.get("length", 10.0) for d in self.graph[u_f][v].values())
                        new_cost = cost_f + min_l
                        if new_cost < dist_fwd.get(v, float("inf")):
                            dist_fwd[v] = new_cost
                            pred_fwd[v] = u_f
                            heapq.heappush(pq_fwd, (new_cost, v))

            # Backward step
            cost_b, u_b = heapq.heappop(pq_bwd)
            if u_b not in visited_bwd:
                visited_bwd.add(u_b)
                step_idx += 1
                nd_b = self.graph.nodes[u_b]
                steps.append({
                    "i": step_idx,
                    "lat": float(nd_b["y"]),
                    "lon": float(nd_b["x"]),
                    "cost": round(cost_b, 1),
                    "dir": "bwd",
                })
                if u_b in visited_fwd:
                    meeting_node = u_b
                    break
                # Explore predecessors in directed graph
                for pred in self.graph.predecessors(u_b):
                    if pred not in visited_bwd:
                        min_l = min(d.get("length", 10.0) for d in self.graph[pred][u_b].values())
                        new_cost = cost_b + min_l
                        if new_cost < dist_bwd.get(pred, float("inf")):
                            dist_bwd[pred] = new_cost
                            pred_bwd[pred] = u_b
                            heapq.heappush(pq_bwd, (new_cost, pred))

        # Reconstruct path from meeting point
        path: List[int] = []
        if meeting_node is not None:
            # Forward part
            curr: Optional[int] = meeting_node
            fwd_part = []
            while curr is not None:
                fwd_part.append(curr)
                curr = pred_fwd.get(curr)
            fwd_part.reverse()

            # Backward part
            curr = pred_bwd.get(meeting_node)
            bwd_part = []
            while curr is not None:
                bwd_part.append(curr)
                curr = pred_bwd.get(curr)

            path = fwd_part + bwd_part

        return steps, path, (dist_fwd.get(meeting_node or 0, 0.0) + dist_bwd.get(meeting_node or 0, 0.0))

    def _run_dynamic_c_t(self, start: int, target: int) -> Tuple[List[Dict[str, Any]], List[int], float]:
        """HotWAY Dynamic Dijkstra: Incorporates dynamic congestion penalty C(t)."""
        # Define synthetic central bottleneck corridors (e.g., Dien Bien Phu / Hang Xanh bottleneck)
        center_lat = (self.graph.nodes[start]["y"] + self.graph.nodes[target]["y"]) / 2.0
        center_lon = (self.graph.nodes[start]["x"] + self.graph.nodes[target]["x"]) / 2.0

        def get_traffic_multiplier(u: int, v: int) -> float:
            nd = self.graph.nodes[u]
            lat, lon = nd["y"], nd["x"]
            # Distance from bottleneck core
            dist_to_jam = haversine(lat, lon, center_lat, center_lon)
            if dist_to_jam < 600.0:
                # Congestion zone: 3.5x penalty
                return 3.5
            elif dist_to_jam < 1200.0:
                return 1.8
            return 1.0

        distances: Dict[int, float] = {start: 0.0}
        predecessors: Dict[int, int] = {}
        visited: Set[int] = set()
        pq: List[Tuple[float, int]] = [(0.0, start)]
        steps: List[Dict[str, Any]] = []

        step_idx = 0
        found = False

        while pq:
            cost, u = heapq.heappop(pq)
            if u in visited:
                continue
            visited.add(u)
            step_idx += 1

            u_node = self.graph.nodes[u]
            u_lat, u_lon = float(u_node["y"]), float(u_node["x"])

            # Check if this node is in jam zone
            is_jammed = haversine(u_lat, u_lon, center_lat, center_lon) < 600.0

            steps.append({
                "i": step_idx,
                "lat": u_lat,
                "lon": u_lon,
                "cost": round(cost, 1),
                "jam": is_jammed,
                "dir": "fwd",
            })

            if u == target:
                found = True
                break

            for v in self.graph.neighbors(u):
                if v in visited:
                    continue
                base_len = min(d.get("length", 10.0) for d in self.graph[u][v].values())
                multiplier = get_traffic_multiplier(u, v)
                effective_cost = base_len * multiplier
                new_cost = cost + effective_cost

                if new_cost < distances.get(v, float("inf")):
                    distances[v] = new_cost
                    predecessors[v] = u
                    heapq.heappush(pq, (new_cost, v))

        path = self._reconstruct_path(predecessors, start, target) if found else []
        return steps, path, distances.get(target, 0.0)

    @staticmethod
    def _reconstruct_path(predecessors: Dict[int, int], start: int, target: int) -> List[int]:
        path = []
        curr: Optional[int] = target
        while curr is not None:
            path.append(curr)
            if curr == start:
                break
            curr = predecessors.get(curr)
        path.reverse()
        return path if path and path[0] == start else []

    @staticmethod
    def _sample_steps(steps: List[Dict[str, Any]], max_steps: int) -> List[Dict[str, Any]]:
        if len(steps) <= max_steps:
            return steps
        stride = math.ceil(len(steps) / max_steps)
        sampled = steps[::stride]
        # Always retain final step
        if steps and (not sampled or sampled[-1]["i"] != steps[-1]["i"]):
            sampled.append(steps[-1])
        return sampled
