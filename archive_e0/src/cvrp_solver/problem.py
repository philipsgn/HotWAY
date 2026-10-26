"""
CVRP Problem Definition and Solution Data Structures.
Supports asymmetric cost matrices from road networks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CVRPStop:
    id: str
    order_id: str
    lat: float
    lon: float
    demand: int
    window_start: Optional[str] = None
    window_end: Optional[str] = None


@dataclass
class CVRPInstance:
    name: str
    n_customers: int
    capacity: int
    max_vehicles: int
    demands: List[int]            # index 0 is depot (demand 0), 1..n customers
    dist_matrix: List[List[float]] # asymmetric distance (meters)
    time_matrix: List[List[float]] # asymmetric duration (seconds)
    stops: List[CVRPStop]         # index 0 is depot, 1..n customers
    coords: List[List[float]]     # [[lat, lon], ...]


@dataclass
class RouteStopInfo:
    node_idx: int
    order_id: str
    lat: float
    lon: float
    arrival_time_sec: float
    elapsed_time_min: float
    demand: int
    remaining_load: int
    estimated_temp_c: float
    thermal_violation: bool


@dataclass
class VehicleRoute:
    vehicle_id: int
    customer_indices: List[int] # customer node indices (excluding depot)
    stops: List[RouteStopInfo]
    leg_geometries: List[List[List[float]]]
    distance_km: float
    duration_min: float
    total_load: int
    thermal_violations_count: int


@dataclass
class CVRPSolution:
    routes: List[List[int]]       # List of customer index sequences, e.g. [[1, 3], [2, 4]]
    total_distance: float
    total_duration_sec: float
    is_feasible: bool
    rejection_reason: Optional[str] = None
    detailed_routes: List[VehicleRoute] = field(default_factory=list)
    search_trace: List[Dict[str, Any]] = field(default_factory=list)
