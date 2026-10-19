"""Dynamic Rush-Hour Traffic Congestion Simulator for HotWAY.

Simulates time-dependent congestion slowdowns on Hàng Gòn road network edges:
- Peak Hours:
  * Morning: 07:00 - 08:30 (Peak 07:45)
  * Evening: 17:00 - 18:30 (Peak 17:45)
  * Lunch: 11:30 - 13:00 (Peak 12:15)
- Road Hierarchy Sensitivity:
  * QL56 (primary): Congestion multiplier x2.0 to x3.0
  * Secondary (Suối Tre - Hàng Gòn): x1.4 to x1.6
  * Tertiary / Residential: x1.1 to x1.25
  * Rural Tracks: x1.0
- Traversal Time: Delta_t = (length / speed) * traffic_multiplier

Authoritative References:
- PRD.md §3.2, TECH_ARCHITECTURE.md §2
- survey_rl.md §2.4
- TEST_INFRA.md Feature 5
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx


@dataclass
class RushHourWindow:
    name: str
    start_minute: float  # e.g. 7:00 = 420.0
    end_minute: float    # e.g. 8:30 = 510.0
    peak_minute: float   # e.g. 7:45 = 465.0
    sigma_minutes: float = 22.0


# Authoritative Rush Hour Windows
RUSH_HOURS: List[RushHourWindow] = [
    RushHourWindow(
        name="Morning Rush (QL56 Commute)",
        start_minute=420.0,   # 07:00
        end_minute=510.0,     # 08:30
        peak_minute=465.0,    # 07:45
        sigma_minutes=22.0,
    ),
    RushHourWindow(
        name="Lunch Rush",
        start_minute=690.0,   # 11:30
        end_minute=780.0,     # 13:00
        peak_minute=735.0,    # 12:15
        sigma_minutes=25.0,
    ),
    RushHourWindow(
        name="Evening Rush (QL56 Freight & Commute)",
        start_minute=1020.0,  # 17:00
        end_minute=1110.0,    # 18:30
        peak_minute=1065.0,   # 17:45
        sigma_minutes=22.0,
    ),
]

# Peak Congestion Factors by Road Hierarchy
PEAK_MULTIPLIERS_BY_HIGHWAY: Dict[str, float] = {
    "primary": 2.50,        # QL56: up to x2.50 travel time during peak
    "primary_link": 2.20,
    "secondary": 1.50,      # Inter-commune: up to x1.50
    "secondary_link": 1.40,
    "tertiary": 1.25,       # Village main roads: up to x1.25
    "tertiary_link": 1.20,
    "residential": 1.15,    # Residential alleys: up to x1.15
    "unclassified": 1.15,
    "service": 1.05,        # Farm / rubber plantation tracks: minimal traffic
    "track": 1.00,
}
DEFAULT_PEAK_MULTIPLIER: float = 1.15


def time_to_minutes(hour: int, minute: int = 0) -> float:
    """Converts 24h clock time to minutes from midnight (0.0 to 1440.0)."""
    return float((hour * 60) + minute)


def get_traffic_multiplier(
    time_minutes: float,
    highway_type: str = "primary",
    is_raining: bool = False,
    include_lunch: bool = True,
) -> float:
    """Computes dynamic congestion multiplier gamma in [1.0, 5.0] for a road type.

    Args:
        time_minutes: Minute of the day in [0.0, 1440.0).
        highway_type: OSM highway classification string.
        is_raining: Boolean flag indicating active precipitation.
        include_lunch: Whether to include the 11:30-13:00 lunch rush window.

    Returns:
        float: Congestion multiplier gamma (1.0 = free-flow).
    """
    # Normalize minute into [0, 1440)
    tau = time_minutes % 1440.0

    max_peak_factor = PEAK_MULTIPLIERS_BY_HIGHWAY.get(highway_type, DEFAULT_PEAK_MULTIPLIER)
    # The excess multiplier above free-flow (e.g. 2.5 - 1.0 = 1.5)
    max_excess = max(0.0, max_peak_factor - 1.0)

    # Evaluate Gaussian bell curve across active rush windows
    current_excess = 0.0
    for window in RUSH_HOURS:
        if not include_lunch and "Lunch" in window.name:
            continue
        dist = abs(tau - window.peak_minute)
        # Avoid wrap-around error at midnight
        dist = min(dist, 1440.0 - dist)
        if dist < (window.sigma_minutes * 3.5):
            excess = max_excess * math.exp(-0.5 * ((dist / window.sigma_minutes) ** 2))
            if excess > current_excess:
                current_excess = excess

    multiplier = 1.0 + current_excess

    # Rain adds global friction
    if is_raining:
        multiplier += 0.35

    # Safe bound clamping
    return round(max(1.0, min(multiplier, 5.0)), 4)


def compute_edge_traversal(
    length_meters: float,
    speed_kph: float,
    time_minutes: float,
    highway_type: str = "primary",
    is_raining: bool = False,
) -> Tuple[float, float, float]:
    """Computes dynamic traversal time and effective speed on a road segment.

    Returns:
        Tuple[traversal_time_seconds, traversal_time_minutes, effective_speed_kph]
    """
    if length_meters < 0.0:
        raise ValueError(f"Edge length cannot be negative: {length_meters}")
    if speed_kph <= 0.0:
        raise ValueError(f"Speed limit must be strictly positive: {speed_kph}")

    gamma = get_traffic_multiplier(
        time_minutes=time_minutes,
        highway_type=highway_type,
        is_raining=is_raining,
    )

    effective_speed_kph = max(5.0, speed_kph / gamma)
    effective_speed_mps = (effective_speed_kph * 1000.0) / 3600.0

    traversal_seconds = length_meters / effective_speed_mps
    traversal_minutes = traversal_seconds / 60.0

    return round(traversal_seconds, 3), round(traversal_minutes, 4), round(effective_speed_kph, 2)


def get_dynamic_edge_weight(
    u: Any,
    v: Any,
    edge_data: Dict[str, Any],
    time_minutes: float,
    is_raining: bool = False,
) -> float:
    """Returns dynamic traversal duration in seconds for NetworkX shortest path algorithms."""
    length = float(edge_data.get("length", 100.0))
    speed = float(edge_data.get("speed_kph", 30.0))
    hw = str(edge_data.get("highway", "residential"))
    traversal_sec, _, _ = compute_edge_traversal(
        length_meters=length,
        speed_kph=speed,
        time_minutes=time_minutes,
        highway_type=hw,
        is_raining=is_raining,
    )
    return traversal_sec
