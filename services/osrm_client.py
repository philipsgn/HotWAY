"""
OSRM Client for Vietnam Road Network Routing.
Communicates with self-hosted OSRM Docker service or falls back to local precomputed matrices.
"""

from __future__ import annotations

import json
import math
import os
from typing import Any, Dict, List, Optional, Tuple
import urllib.request


class OSRMClient:
    """Client for querying OSRM (Open Source Routing Machine)."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("OSRM_URL", "http://localhost:5000")

    def get_distance_matrix(
        self,
        coordinates: List[Tuple[float, float]],  # List of (lat, lon)
        profile: str = "motorcycle"
    ) -> Optional[Dict[str, Any]]:
        """
        Request distance and duration matrix for coordinates: lon,lat;lon,lat.
        """
        try:
            coords_str = ";".join([f"{lon},{lat}" for lat, lon in coordinates])
            url = f"{self.base_url}/table/v1/{profile}/{coords_str}?annotations=distance,duration"
            req = urllib.request.Request(url, headers={"User-Agent": "HotWAY-RoutingEngine/7.0"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode())
                    return {
                        "distances_km": [[d / 1000.0 for d in row] for row in data["distances"]],
                        "durations_min": [[t / 60.0 for t in row] for row in data["durations"]],
                        "source": "OSRM_LOCAL"
                    }
        except Exception:
            pass
        return None

    def get_route(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        profile: str = "motorcycle"
    ) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.base_url}/route/v1/{profile}/{origin[1]},{origin[0]};{destination[1]},{destination[0]}?overview=full&geometries=geojson"
            req = urllib.request.Request(url, headers={"User-Agent": "HotWAY-RoutingEngine/7.0"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode())
                    route = data["routes"][0]
                    return {
                        "distance_km": route["distance"] / 1000.0,
                        "duration_min": route["duration"] / 60.0,
                        "geometry": route["geometry"],
                        "source": "OSRM_LOCAL"
                    }
        except Exception:
            pass
        return None

