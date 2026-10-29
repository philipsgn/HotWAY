"""
FastAPI Microservice serving the winning Attention Model (Graph Transformer)
and 4-Model Comparative Benchmark Suite for HotWAY.
Port: 8000 (Local serving, CPU inference < 20ms).
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from models.attention_model import AttentionModelSolver
from models.dqn_agent import DQNSolver
from models.ortools_solver import ORToolsSolver
from models.pointer_net import PointerNetSolver
from services.fallback_router import FallbackRouter

app = FastAPI(
    title="HotWAY Dynamic Traffic-Aware Neural Routing API",
    version="7.1.0",
    description="Serving Graph Transformer (Kool et al., 2019) with 3-Layer Traffic Fallback and Multi-Model Benchmark."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize solvers
print("Initializing Serving Solvers on CPU...")
am_solver = AttentionModelSolver()
ortools_solver = ORToolsSolver(time_limit_sec=1)
ptr_solver = PointerNetSolver()
dqn_solver = DQNSolver(max_nodes=20)
fallback_router = FallbackRouter()


class StopItem(BaseModel):
    id: str
    lat: float
    lon: float
    name: Optional[str] = None


class RouteRequest(BaseModel):
    depot: StopItem = Field(default_factory=lambda: StopItem(id="depot", lat=10.8012, lon=106.7145, name="Depot"))
    stops: List[StopItem]
    departure_hour: float = 8.0
    model: str = "am"  # "am", "ortools", "ptr", "dqn", "all"


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "champion_model": "Attention Model (Graph Transformer Kool et al., 2019)",
        "traffic_fallback": "3-Tier (TomTom -> HERE -> Offline C(t))",
        "inference_engine": "PyTorch CPU Native / Sub-20ms",
        "supported_models": ["am", "ortools", "ptr", "dqn"]
    }


@app.post("/optimize-route")
def optimize_route(req: RouteRequest):
    if len(req.stops) == 0:
        raise HTTPException(status_code=400, detail="At least one stop is required.")

    # Prepare instance dictionary
    all_points = [{"lat": req.depot.lat, "lon": req.depot.lon}] + [{"lat": s.lat, "lon": s.lon} for s in req.stops]
    n = len(all_points)

    # Approximate distance matrix via Haversine
    dist_mat = [[0.0] * n for _ in range(n)]
    dur_mat = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                d = math_haversine(all_points[i]["lat"], all_points[i]["lon"], all_points[j]["lat"], all_points[j]["lon"])
                dist_mat[i][j] = round(d, 3)
                dur_mat[i][j] = round(d / (22.0 / 60.0), 3)  # 22 km/h base speed

    inst = {
        "instance_id": "api_request",
        "num_stops": len(req.stops),
        "depot": req.depot.model_dump(),
        "stops": [s.model_dump() for s in req.stops],
        "departure_hour": req.departure_hour,
        "dist_matrix_km": dist_mat,
        "duration_matrix_min": dur_mat
    }

    if req.model == "am":
        result = am_solver.solve(inst)
    elif req.model == "ortools":
        result = ortools_solver.solve(inst)
    elif req.model == "ptr":
        result = ptr_solver.solve(inst)
    elif req.model == "dqn":
        result = dqn_solver.solve(inst)
    elif req.model == "all":
        result = {
            "am": am_solver.solve(inst),
            "ortools": ortools_solver.solve(inst),
            "ptr": ptr_solver.solve(inst),
            "dqn": dqn_solver.solve(inst)
        }
    else:
        result = am_solver.solve(inst)

    return {
        "status": "success",
        "departure_hour": req.departure_hour,
        "num_stops": len(req.stops),
        "result": result
    }


@app.get("/benchmark/summary")
def get_benchmark_summary():
    csv_path = Path("results/benchmark_summary_table.csv")
    json_path = Path("results/benchmark_multi_model_results.json")

    if not csv_path.exists() or not json_path.exists():
        raise HTTPException(status_code=404, detail="Benchmark results not found. Run evaluate_benchmark.py first.")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {
        "summary": data["summary"],
        "dqn_fatal_flaws": data["dqn_fatal_flaws_diagnostic"],
        "metadata": data["metadata"]
    }


def math_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = (lat2 - lat1) * 3.141592653589793 / 180.0
    dlon = (lon2 - lon1) * 3.141592653589793 / 180.0
    a = (math_sin(dlat / 2) ** 2 +
         math_cos(lat1 * 3.141592653589793 / 180.0) * math_cos(lat2 * 3.141592653589793 / 180.0) * math_sin(dlon / 2) ** 2)
    c = 2 * math_atan2(math_sqrt(a), math_sqrt(1 - a))
    return R * c * 1.35  # 1.35 urban road winding factor


def math_sin(x): return (x - (x**3)/6.0 + (x**5)/120.0) if abs(x) < 0.5 else torch.sin(torch.tensor(x)).item()
def math_cos(x): return (1.0 - (x**2)/2.0 + (x**4)/24.0) if abs(x) < 0.5 else torch.cos(torch.tensor(x)).item()
def math_sqrt(x): return x**0.5
def math_atan2(y, x): return torch.atan2(torch.tensor(y), torch.tensor(x)).item()


if __name__ == "__main__":
    import uvicorn
    # Enforce port discipline: Backend 8000, never 3000
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)

