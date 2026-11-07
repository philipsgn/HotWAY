"""
HotWAY Neural Combinatorial Optimization (NCO) Benchmark & Multi-Model Serving Router.
Exposes:
- POST /optimize-route: Real-time route optimization using Attention Model (Kool et al., 2019),
  OR-Tools, PointerNet, or Dueling DQN.
- GET /benchmark/summary: Serves authoritative 100 POI benchmark summary table and metrics.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from models.attention_model import AttentionModelSolver
from models.dqn_agent import DQNSolver
from models.ortools_solver import ORToolsSolver
from models.pointer_net import PointerNetSolver
from services.fallback_router import FallbackRouter

router = APIRouter(tags=["NCO Multi-Model Serving & Benchmark"])

# Lazy-initialized solvers cache for fast CPU startup
_AM_SOLVER: Optional[AttentionModelSolver] = None
_ORTOOLS_SOLVER: Optional[ORToolsSolver] = None
_PTR_SOLVER: Optional[PointerNetSolver] = None
_DQN_SOLVER: Optional[DQNSolver] = None
_FALLBACK_ROUTER: Optional[FallbackRouter] = None


def get_solvers():
    global _AM_SOLVER, _ORTOOLS_SOLVER, _PTR_SOLVER, _DQN_SOLVER, _FALLBACK_ROUTER
    if _AM_SOLVER is None:
        _AM_SOLVER = AttentionModelSolver()
    if _ORTOOLS_SOLVER is None:
        _ORTOOLS_SOLVER = ORToolsSolver(time_limit_sec=1)
    if _PTR_SOLVER is None:
        _PTR_SOLVER = PointerNetSolver()
    if _DQN_SOLVER is None:
        _DQN_SOLVER = DQNSolver(max_nodes=20)
    if _FALLBACK_ROUTER is None:
        _FALLBACK_ROUTER = FallbackRouter()
    return _AM_SOLVER, _ORTOOLS_SOLVER, _PTR_SOLVER, _DQN_SOLVER, _FALLBACK_ROUTER


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance in km with 1.35 urban winding factor."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return R * c * 1.35


class StopItem(BaseModel):
    id: str
    lat: float = Field(..., ge=-90.0, le=90.0, description="WGS84 latitude")
    lon: float = Field(..., ge=-180.0, le=180.0, description="WGS84 longitude")
    name: Optional[str] = None


class RouteRequest(BaseModel):
    depot: StopItem = Field(default_factory=lambda: StopItem(id="depot", lat=10.8012, lon=106.7145, name="Depot"))
    stops: List[StopItem] = Field(..., min_length=1, description="List of delivery stops")
    departure_hour: float = Field(default=8.0, ge=0.0, le=24.0, description="Departure hour of day (0-24)")
    model: str = Field(default="am", description="'am', 'ortools', 'ptr', 'dqn', or 'all'")


@router.post("/optimize-route", summary="Optimize multi-stop delivery tour with selected NCO or OR model")
def optimize_route(req: RouteRequest) -> Dict[str, Any]:
    if len(req.stops) == 0:
        raise HTTPException(status_code=400, detail="At least one stop is required.")

    am_solver, ortools_solver, ptr_solver, dqn_solver, _ = get_solvers()

    all_points = [{"lat": req.depot.lat, "lon": req.depot.lon}] + [{"lat": s.lat, "lon": s.lon} for s in req.stops]
    n = len(all_points)

    dist_mat = [[0.0] * n for _ in range(n)]
    dur_mat = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                d = haversine_km(all_points[i]["lat"], all_points[i]["lon"], all_points[j]["lat"], all_points[j]["lon"])
                dist_mat[i][j] = round(d, 3)
                dur_mat[i][j] = round(d / (22.0 / 60.0), 3)  # 22 km/h base speed

    inst = {
        "instance_id": "api_request",
        "num_stops": len(req.stops),
        "depot": req.depot.model_dump(),
        "stops": [s.model_dump() for s in req.stops],
        "departure_hour": req.departure_hour,
        "dist_matrix_km": dist_mat,
        "duration_matrix_min": dur_mat,
    }

    m = req.model.lower()
    if m == "am":
        result = am_solver.solve(inst)
    elif m == "ortools":
        result = ortools_solver.solve(inst)
    elif m == "ptr":
        result = ptr_solver.solve(inst)
    elif m == "dqn":
        result = dqn_solver.solve(inst)
    elif m == "all":
        result = {
            "am": am_solver.solve(inst),
            "ortools": ortools_solver.solve(inst),
            "ptr": ptr_solver.solve(inst),
            "dqn": dqn_solver.solve(inst),
        }
    else:
        result = am_solver.solve(inst)

    return {
        "status": "success",
        "departure_hour": req.departure_hour,
        "num_stops": len(req.stops),
        "model_used": req.model,
        "result": result,
    }


@router.get("/benchmark/summary", summary="Get multi-model benchmark summary on 100 nationwide POIs")
def get_benchmark_summary() -> Dict[str, Any]:
    json_path = Path("results/benchmark_multi_model_results.json")
    if not json_path.exists():
        fallback_path = Path("results/benchmark_summary_table.csv")
        if not fallback_path.exists():
            raise HTTPException(status_code=404, detail="Benchmark results not found. Run evaluate_benchmark.py first.")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {
        "status": "success",
        "summary": data.get("summary", []),
        "dqn_fatal_flaws": data.get("dqn_fatal_flaws_diagnostic", {}),
        "metadata": data.get("metadata", {}),
    }
