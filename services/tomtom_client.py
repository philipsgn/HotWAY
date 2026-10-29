"""
TomTom Live Traffic API Client.
Manages TomTom Traffic Routing queries with quota throttling (2,500 req/day).
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional, Tuple
import urllib.request


class TomTomClient:
    """Client for TomTom Routing and Traffic API."""

    def __init__(self, api_key: Optional[str] = None, max_daily_requests: int = 2500):
        self.api_key = api_key or os.getenv("TOMTOM_API_KEY", "")
        self.max_daily_requests = max_daily_requests
        self.request_count = 0
        self.last_reset = time.time()

    def get_travel_time(
        self,
        origin: Tuple[float, float],       # (lat, lon)
        destination: Tuple[float, float],  # (lat, lon)
    ) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            return None

        # Reset daily quota tracker every 24h
        if time.time() - self.last_reset > 86400:
            self.request_count = 0
            self.last_reset = time.time()

        if self.request_count >= self.max_daily_requests:
            return None

        lat1, lon1 = origin
        lat2, lon2 = destination
        url = (
            f"https://api.tomtom.com/routing/1/calculateRoute/{lat1},{lon1}:{lat2},{lon2}/json"
            f"?key={self.api_key}&traffic=true&travelMode=motorcycle"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "HotWAY/7.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status == 200:
                    self.request_count += 1
                    data = json.loads(resp.read().decode())
                    summary = data["routes"][0]["summary"]
                    return {
                        "duration_min": round(summary["travelTimeInSeconds"] / 60.0, 2),
                        "distance_km": round(summary["lengthInMeters"] / 1000.0, 2),
                        "traffic_delay_min": round(summary.get("trafficDelayInSeconds", 0) / 60.0, 2),
                        "source": "TOMTOM_LIVE"
                    }
        except Exception:
            pass
        return None

