"""
Multi-Criteria Motorbike Route Optimization (T1 Layer).
Author: AI Researcher & Lead Engineer
Target: Generates and evaluates Pareto-optimal candidate routes for urban motorbikes in Ho Chi Minh City.
"""

from __future__ import annotations

import math
import pickle
import os
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import networkx as nx

SPEED_PROFILE_KMH = {
    "primary": 32.0,
    "primary_link": 28.0,
    "secondary": 28.0,
    "secondary_link": 24.0,
    "tertiary": 24.0,
    "tertiary_link": 20.0,
    "residential": 20.0,
    "living_street": 14.0,
    "service": 14.0,
    "unclassified": 20.0,
    "default": 22.0,
}

ALLEY_HIGHWAY_TYPES = {"service", "living_street", "residential"}


def calculate_bearing(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calculates compass bearing (degrees) from p1(lat, lon) to p2(lat, lon)."""
    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(dlon))
    initial_bearing = math.atan2(x, y)
    compass_bearing = (math.degrees(initial_bearing) + 360) % 360
    return compass_bearing


def turn_classification(bearing_in: float, bearing_out: float) -> str:
    """
    Classifies turn relative to incoming heading.
    0 deg = straight ahead.
    90 deg = right turn.
    270 deg = left turn (cuts opposing traffic in right-hand traffic).
    """
    turn_angle = (bearing_out - bearing_in + 360) % 360
    if 200.0 <= turn_angle <= 340.0:
        return "LEFT"
    elif 20.0 <= turn_angle <= 160.0:
        return "RIGHT"
    elif 160.0 < turn_angle < 200.0:
        return "UTURN"
    return "STRAIGHT"


class MultiCriteriaRouter:
    """
    Evaluates candidate routes across multiple operational criteria:
    - Distance (meters)
    - Expected travel time (minutes)
    - 90th percentile travel time p90 (minutes)
    - Number of turns and left turns cutting opposing traffic
    - Percentage of alley segments
    - Traffic light / signalized nodes
    """

    def __init__(
        self,
        graph: nx.DiGraph,
        rain_factor: float = 1.0,
        noise_sigma: float = 0.20,
        left_turn_penalty_sec: float = 12.0,
        light_penalty_sec: float = 25.0,
    ):
        self.graph = graph
        self.rain_factor = rain_factor
        self.noise_sigma = noise_sigma
        self.left_turn_penalty_sec = left_turn_penalty_sec
        self.light_penalty_sec = light_penalty_sec
        self._init_graph_attributes()

    def _init_graph_attributes(self):
        """Precomputes edge weights for multi-criteria corridor generation."""
        for u, v, data in self.graph.edges(data=True):
            length = float(data.get("length", 50.0))
            speed = self._get_edge_speed_kph(data)
            travel_time = length / (speed / 3.6)
            data["travel_time_sec"] = travel_time
            # Comfort: penalize intersections and signalized junctions
            is_junction = (
                self.graph.nodes[v].get("highway") == "traffic_signals"
                or self.graph.degree(v) >= 4
            )
            data["comfort_cost"] = travel_time + (self.light_penalty_sec if is_junction else 0.0)
            # Stable: penalize arterial roads prone to severe congestion under rain
            hw = str(data.get("highway", ""))
            data["stable_cost"] = travel_time * (1.30 if "primary" in hw else 1.0)

    @classmethod
    def from_hcmc_subgraph(
        cls,
        graph_path: str = "data/hcmc_compact_graph.pickle",
        center_lat: float = 10.8012,
        center_lon: float = 106.7145,
        radius_km: float = 1.5,
    ) -> "MultiCriteriaRouter":
        """Extracts strongly connected motorbike subgraph from the comprehensive HCMC graph."""
        with open(graph_path, "rb") as f:
            full_G = pickle.load(f)

        selected_nodes = []
        for n, data in full_G.nodes(data=True):
            lat = data.get("y") or data.get("lat")
            lon = data.get("x") or data.get("lon")
            if lat and lon:
                d_lat = (lat - center_lat) * 111.0
                d_lon = (lon - center_lon) * 111.0 * math.cos(math.radians(center_lat))
                dist = math.sqrt(d_lat**2 + d_lon**2)
                if dist <= radius_km:
                    selected_nodes.append(n)

        subG = full_G.subgraph(selected_nodes).copy()
        sccs = list(nx.strongly_connected_components(subG))
        largest_scc = max(sccs, key=len)
        
        # Collapse into a clean nx.DiGraph taking the shortest edge if parallel edges exist
        diG = nx.DiGraph()
        for n in largest_scc:
            diG.add_node(n, **subG.nodes[n])
        for u, v, k, data in subG.edges(keys=True, data=True):
            if u in largest_scc and v in largest_scc:
                if not diG.has_edge(u, v) or data.get("length", 1e9) < diG[u][v].get("length", 1e9):
                    diG.add_edge(u, v, **data)

        return cls(diG)

    def _get_edge_speed_kph(self, edge_data: Dict[str, Any]) -> float:
        hw = edge_data.get("highway")
        if isinstance(hw, list):
            hw = hw[0]
        return SPEED_PROFILE_KMH.get(str(hw), SPEED_PROFILE_KMH["default"])

    def _is_alley(self, edge_data: Dict[str, Any]) -> bool:
        hw = edge_data.get("highway")
        if isinstance(hw, list):
            hw = hw[0]
        return str(hw) in ALLEY_HIGHWAY_TYPES

    def generate_candidate_paths(
        self, origin: int, destination: int, k_target: int = 15
    ) -> List[List[int]]:
        """
        Generates diverse candidate paths using multi-objective edge weights,
        iterative edge penalization, and k-shortest paths.
        """
        candidates: List[List[int]] = []

        # 1. Base paths across multiple criteria weights
        base_weights = ["travel_time_sec", "length", "comfort_cost", "stable_cost"]
        for w in base_weights:
            try:
                p = nx.shortest_path(self.graph, origin, destination, weight=w)
                if p not in candidates:
                    candidates.append(p)
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                pass

        if not candidates:
            return []

        # 2. Iterative edge penalization to discover alternative parallel corridors
        penalized_G = self.graph.copy()
        for base_p in list(candidates):
            for u, v in zip(base_p[:-1], base_p[1:]):
                if penalized_G.has_edge(u, v):
                    penalized_G[u][v]["travel_time_sec"] *= 1.40
                    penalized_G[u][v]["length"] *= 1.40
                    penalized_G[u][v]["comfort_cost"] *= 1.40

            for w in ["travel_time_sec", "length", "comfort_cost"]:
                try:
                    p_pen = nx.shortest_path(penalized_G, origin, destination, weight=w)
                    if p_pen not in candidates:
                        candidates.append(p_pen)
                except Exception:
                    pass

        # 3. Supplement with k-shortest paths by travel time
        try:
            gen = nx.shortest_simple_paths(self.graph, origin, destination, weight="travel_time_sec")
            for p in gen:
                if p not in candidates:
                    candidates.append(p)
                if len(candidates) >= k_target:
                    break
        except Exception:
            pass

        return candidates[:k_target]

    def evaluate_path(
        self, path: List[int], num_monte_carlo: int = 200, seed: int = 2026
    ) -> Dict[str, Any]:
        """
        Evaluates a candidate path across all physical and operational criteria.
        """
        total_length_m = 0.0
        base_time_sec = 0.0
        alley_length_m = 0.0
        num_turns = 0
        num_left_turns = 0
        num_signals = 0

        coords: List[Tuple[float, float]] = []
        for n in path:
            d = self.graph.nodes[n]
            coords.append((d.get("y") or d.get("lat"), d.get("x") or d.get("lon")))

        # Check turn bearings
        headings = []
        for i in range(len(coords) - 1):
            headings.append(calculate_bearing(coords[i], coords[i + 1]))

        for i in range(len(headings) - 1):
            turn_type = turn_classification(headings[i], headings[i + 1])
            if turn_type != "STRAIGHT":
                num_turns += 1
                if turn_type == "LEFT":
                    num_left_turns += 1

        # Check edges
        edge_lengths = []
        edge_speeds = []
        for u, v in zip(path[:-1], path[1:]):
            edge_data = self.graph[u][v]
            length = edge_data.get("length", 50.0)
            speed = self._get_edge_speed_kph(edge_data)
            edge_lengths.append(length)
            edge_speeds.append(speed)

            total_length_m += length
            if self._is_alley(edge_data):
                alley_length_m += length

            # Node signal
            v_data = self.graph.nodes[v]
            if v_data.get("highway") == "traffic_signals" or self.graph.degree(v) >= 4:
                num_signals += 1

        # Travel times
        edge_lengths_arr = np.array(edge_lengths)
        edge_speeds_arr = np.array(edge_speeds) / 3.6  # m/s
        base_edge_times_sec = edge_lengths_arr / edge_speeds_arr

        static_turn_penalty_sec = (
            num_left_turns * self.left_turn_penalty_sec
            + (num_turns - num_left_turns) * 4.0
            + num_signals * self.light_penalty_sec
        )

        # Monte Carlo stochastic simulation
        rng = np.random.default_rng(seed)
        sampled_times_min = np.zeros(num_monte_carlo)

        for m in range(num_monte_carlo):
            noise = rng.normal(0, self.noise_sigma, len(edge_lengths))
            stochastic_edge_sec = (
                base_edge_times_sec * self.rain_factor * np.exp(noise)
            )
            total_trip_sec = np.sum(stochastic_edge_sec) + static_turn_penalty_sec
            sampled_times_min[m] = total_trip_sec / 60.0

        mean_time_min = float(np.mean(sampled_times_min))
        p90_time_min = float(np.percentile(sampled_times_min, 90))
        alley_ratio_pct = float(
            (alley_length_m / total_length_m * 100.0) if total_length_m > 0 else 0.0
        )

        # Ease of riding penalty score: lower is easier
        ease_penalty_score = float(
            num_turns * 1.0
            + num_left_turns * 2.5
            + num_signals * 3.0
            + (alley_ratio_pct / 20.0)
        )

        return {
            "path_nodes": path,
            "coords": coords,
            "distance_m": float(round(total_length_m, 1)),
            "expected_time_min": float(round(mean_time_min, 2)),
            "p90_time_min": float(round(p90_time_min, 2)),
            "num_turns": int(num_turns),
            "num_left_turns": int(num_left_turns),
            "alley_ratio_pct": float(round(alley_ratio_pct, 1)),
            "num_signals": int(num_signals),
            "ease_penalty_score": float(round(ease_penalty_score, 2)),
        }

    def filter_pareto(self, evaluated_routes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filters non-dominated routes in the Pareto sense across operational criteria:
        distance, expected time, p90 time, left turns, and ease of riding.
        """
        pareto_routes = []
        for i, r1 in enumerate(evaluated_routes):
            dominated = False
            for j, r2 in enumerate(evaluated_routes):
                if i == j:
                    continue
                # r2 dominates r1 if r2 is <= in all criteria and strictly < in at least one
                better_or_equal = (
                    r2["distance_m"] <= r1["distance_m"]
                    and r2["expected_time_min"] <= r1["expected_time_min"]
                    and r2["p90_time_min"] <= r1["p90_time_min"]
                    and r2["num_left_turns"] <= r1["num_left_turns"]
                    and r2["ease_penalty_score"] <= r1["ease_penalty_score"]
                )
                strictly_better = (
                    r2["distance_m"] < r1["distance_m"]
                    or r2["expected_time_min"] < r1["expected_time_min"]
                    or r2["p90_time_min"] < r1["p90_time_min"]
                    or r2["num_left_turns"] < r1["num_left_turns"]
                    or r2["ease_penalty_score"] < r1["ease_penalty_score"]
                )
                if better_or_equal and strictly_better:
                    dominated = True
                    break
            if not dominated and r1 not in pareto_routes:
                pareto_routes.append(r1)

        return pareto_routes if pareto_routes else evaluated_routes[:4]

    def select_four_labeled_routes(
        self, origin: int, destination: int, k_candidates: int = 15
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generates candidate paths, computes Pareto set, and selects 4 labeled archetypes:
        1. Nhanh nhất kỳ vọng (Fastest Expected)
        2. Ngắn nhất cự ly (Shortest Distance)
        3. Ổn định nhất (Most Stable p90)
        4. Dễ đi nhất (Easiest Ride)
        """
        paths = self.generate_candidate_paths(origin, destination, k_target=k_candidates)
        if not paths:
            return {}

        evaluated = [self.evaluate_path(p) for p in paths]
        pareto = self.filter_pareto(evaluated)

        def pick_distinct_best(pool: List[Dict[str, Any]], key_fn, chosen_nodes: List[List[int]]) -> Dict[str, Any]:
            # First try to find best from pool not already chosen
            candidates = [r for r in pool if r["path_nodes"] not in chosen_nodes]
            if candidates:
                return min(candidates, key=key_fn)
            return min(pool, key=key_fn)

        chosen = []
        # 1. Fastest Expected
        fastest = min(pareto, key=lambda r: r["expected_time_min"])
        chosen.append(fastest["path_nodes"])

        # 2. Shortest Distance
        shortest = pick_distinct_best(pareto, lambda r: r["distance_m"], chosen)
        chosen.append(shortest["path_nodes"])

        # 3. Most Stable (Lowest p90)
        stable = pick_distinct_best(pareto, lambda r: r["p90_time_min"], chosen)
        chosen.append(stable["path_nodes"])

        # 4. Easiest Ride
        easiest = pick_distinct_best(pareto, lambda r: r["ease_penalty_score"], chosen)
        chosen.append(easiest["path_nodes"])

        return {
            "fastest": {**fastest, "label": "Nhanh nhất kỳ vọng", "tag": "FASTEST"},
            "shortest": {**shortest, "label": "Ngắn nhất cự ly", "tag": "SHORTEST"},
            "stable": {**stable, "label": "Ổn định nhất (p90)", "tag": "STABLE_P90"},
            "easiest": {**easiest, "label": "Dễ đi nhất (Ít rẽ, hẻm, đèn)", "tag": "EASIEST"},
        }
