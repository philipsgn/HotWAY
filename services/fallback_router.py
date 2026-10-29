"""
3-Tier Fallback Manager for Real-Time & Offline Traffic Routing.
Tier 1: TomTom Traffic Flow API (Live real-time)
Tier 2: HERE Maps Routing API
Tier 3: Local Offline Fallback: OSRM Matrix * Empirical Traffic Multiplier C(t)
"""

from __future__ import annotations

import math
import os
from typing import Any, Dict, List, Optional, Tuple

from env.traffic_tsp_env import compute_traffic_multiplier
from services.osrm_client import OSRMClient
from services.tomtom_client import TomTomClient
from src.services.live_traffic_adapter import LiveTrafficAdapter


class FallbackRouter:
    """Manages the 3-Tier traffic routing fallback cascade."""

    def __init__(
        self,
        tomtom_key: Optional[str] = None,
        here_key: Optional[str] = None,
        osrm_url: Optional[str] = None
    ):
        self.tomtom_client = TomTomClient(api_key=tomtom_key)
        self.osrm_client = OSRMClient(base_url=osrm_url)
        self.adapter = LiveTrafficAdapter()
        if tomtom_key:
            self.adapter.tomtom_key = tomtom_key
        if here_key:
            self.adapter.here_key = here_key

    def get_segment_cost(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        departure_hour: float = 8.0,
    ) -> Dict[str, Any]:
        """Query segment cost with 3-tier fallback."""
        # Tier 1: TomTom
        res = self.tomtom_client.get_travel_time(origin, destination)
        if res is not None:
            return res

        # Tier 2 & 3: Handled by LiveTrafficAdapter (HERE -> Offline C(t))
        return self.adapter.get_segment_travel_time(
            origin[0], origin[1], destination[0], destination[1], departure_hour
        )

    def compute_tour_metrics(
        self,
        coordinates: List[Tuple[float, float]],
        route: List[int],
        departure_hour: float = 8.0
    ) -> Dict[str, Any]:
        """Compute metrics for full multi-stop tour with fallback cascade."""
        total_dist = 0.0
        total_dur = 0.0
        sources_used = set()
        curr_time = 0.0

        for i in range(len(route) - 1):
            u, v = route[i], route[i + 1]
            h = (departure_hour + curr_time / 60.0) % 24.0
            seg = self.get_segment_cost(coordinates[u], coordinates[v], departure_hour=h)
            d = seg["distance_km"]
            t = seg["duration_min"]
            total_dist += d
            total_dur += t
            curr_time += t
            sources_used.add(seg["source"])

        return {
            "total_dist_km": round(total_dist, 2),
            "total_duration_min": round(total_dur, 2),
            "sources": list(sources_used),
            "primary_tier": "TOMTOM_LIVE" if "TOMTOM_LIVE" in sources_used else ("HERE_LIVE" if "HERE_LIVE" in sources_used else "SYNTHETIC_OFFLINE")
        }

