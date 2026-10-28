"""Live Traffic Fallback Adapter for HCMC Urban Routing.
Implements 3-layer resilience pipeline:
Layer 1 (Primary): TomTom Traffic Routing API (2,500 req/day free tier)
Layer 2 (Secondary Fallback): HERE Routing API
Layer 3 (Offline Fallback): Local Road Matrix * Simulated C(t) Congestion Multiplier
"""

import os
from typing import Dict, Any, Optional
import urllib.request
import json
from src.agents.attention_model.time_dependent_env import get_congestion_factor


class LiveTrafficAdapter:
    """Manages real-time traffic queries with automated fallback cascades."""

    def __init__(self):
        self.tomtom_key = os.getenv("TOMTOM_API_KEY", "")
        self.here_key = os.getenv("HERE_API_KEY", "")

    def get_segment_travel_time(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        departure_hour: float = 8.0,
    ) -> Dict[str, Any]:
        """Fetch travel duration and distance between two points with 3-layer fallback.
        
        Returns:
            Dict containing duration_min, distance_km, and source ('TOMTOM_LIVE' | 'HERE_LIVE' | 'SYNTHETIC_OFFLINE').
        """
        # Layer 1: TomTom Traffic Routing API
        if self.tomtom_key:
            res = self._query_tomtom(origin_lat, origin_lon, dest_lat, dest_lon)
            if res is not None:
                return res

        # Layer 2: HERE Routing API
        if self.here_key:
            res = self._query_here(origin_lat, origin_lon, dest_lat, dest_lon)
            if res is not None:
                return res

        # Layer 3: Offline Fallback via Haversine & Empirical C(t)
        return self._offline_fallback(origin_lat, origin_lon, dest_lat, dest_lon, departure_hour)

    def _query_tomtom(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> Optional[Dict[str, Any]]:
        """Query TomTom Calculate Route API with traffic consideration."""
        try:
            url = (
                f"https://api.tomtom.com/routing/1/calculateRoute/{lat1},{lon1}:{lat2},{lon2}/json"
                f"?key={self.tomtom_key}&traffic=true&travelMode=motorcycle"
            )
            req = urllib.request.Request(url, headers={"User-Agent": "HotWAY-Routing-Engine/7.1"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    summary = data["routes"][0]["summary"]
                    return {
                        "duration_min": round(summary["travelTimeInSeconds"] / 60.0, 2),
                        "distance_km": round(summary["lengthInMeters"] / 1000.0, 2),
                        "source": "TOMTOM_LIVE",
                    }
        except Exception:
            pass
        return None

    def _query_here(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> Optional[Dict[str, Any]]:
        """Query HERE Routing v8 API as secondary live provider."""
        try:
            url = (
                f"https://router.hereapi.com/v8/routes?transportMode=scooter"
                f"&origin={lat1},{lon1}&destination={lat2},{lon2}&return=summary&apiKey={self.here_key}"
            )
            req = urllib.request.Request(url, headers={"User-Agent": "HotWAY-Routing-Engine/7.1"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    summary = data["routes"][0]["sections"][0]["summary"]
                    return {
                        "duration_min": round(summary["duration"] / 60.0, 2),
                        "distance_km": round(summary["length"] / 1000.0, 2),
                        "source": "HERE_LIVE",
                    }
        except Exception:
            pass
        return None

    def _offline_fallback(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
        departure_hour: float,
    ) -> Dict[str, Any]:
        """Layer 3: Offline calculation with HCMC road curvature and empirical C(t)."""
        import numpy as np

        rlat1, rlon1 = np.radians(lat1), np.radians(lon1)
        rlat2, rlon2 = np.radians(lat2), np.radians(lon2)
        dlat = rlat2 - rlat1
        dlon = rlon2 - rlon1

        a = np.sin(dlat / 2.0) ** 2 + np.cos(rlat1) * np.cos(rlat2) * np.sin(dlon / 2.0) ** 2
        c = 2.0 * np.arcsin(np.sqrt(a))
        dist_km = 6371.0 * c * 1.35  # 1.35 curvature proxy for HCMC

        c_factor = get_congestion_factor(departure_hour)
        speed_kmh = max(8.0, 24.0 / c_factor)
        dur_min = (dist_km / speed_kmh) * 60.0

        return {
            "duration_min": round(dur_min, 2),
            "distance_km": round(dist_km, 2),
            "source": "SYNTHETIC_OFFLINE",
        }
