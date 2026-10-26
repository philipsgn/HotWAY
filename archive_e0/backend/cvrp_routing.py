"""
HotWAY CVRP Scheduling & Routing API (/api/v1)
OptimoRoute-style Dispatcher Endpoints:
1. POST /api/v1/scenarios & GET /api/v1/scenarios/{id} & POST /api/v1/scenarios/sample
2. POST /api/v1/plans (Clarke-Wright, Random, Cyclic, Greedy, DQN, Double DQN, OR-Tools, or Best)
3. GET /api/v1/strategies/benchmark (Reads directly from rel_result/ CSVs)
4. GET /api/v1/sim/{plan_id} (Interpolated live simulation coordinates along road geometry)
"""

from __future__ import annotations

import csv
import logging
import math
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.cvrp_solver.problem import CVRPInstance, CVRPStop
from src.cvrp_solver.search import solve_cvrp_strategy
from src.data.build_graph import load_site_config
from src.services.road_matrix import compute_road_matrix, snap_coordinate_to_node

logger = logging.getLogger("cvrp_routing_api")
router = APIRouter(prefix="/api/v1", tags=["CVRP Scheduling & Dispatch"])

# In-memory storage for scenarios and plans (SQLite / dict cache)
_SCENARIOS_STORE: Dict[str, Dict[str, Any]] = {}
_PLANS_STORE: Dict[str, Dict[str, Any]] = {}


class OrderItem(BaseModel):
    id: str
    address: str
    lat: float
    lon: float
    demand: int = Field(default=3, ge=1, le=20)
    window_start: Optional[str] = "11:00"
    window_end: Optional[str] = "12:00"


class FleetConfig(BaseModel):
    num_vehicles: int = 5
    capacity: int = 40
    avg_speed_kmh: float = 30.0


class ScenarioCreateRequest(BaseModel):
    name: str = "Kịch bản giao hàng Bình Thạnh"
    orders: List[OrderItem]
    fleet: FleetConfig = Field(default_factory=FleetConfig)


class ThermalConfig(BaseModel):
    t0_c: float = 85.0
    tenv_c: float = 30.0
    k_rate: float = 0.020
    min_temp: float = 60.0


class PlanRequest(BaseModel):
    scenario_id: str
    strategy: str = Field(
        default="best",
        description="clarke_wright | random | cyclic | greedy | dqn | double_dqn | ortools | best",
    )
    max_steps: int = 100
    max_candidates: int = 128
    thermal: ThermalConfig = Field(default_factory=ThermalConfig)


# ==============================================================================
# 1. SCENARIOS ENDPOINTS
# ==============================================================================

@router.post("/scenarios")
async def create_scenario(req: ScenarioCreateRequest):
    site_cfg = load_site_config("config/site.yaml")
    depot = site_cfg["site"]["depot"]

    # Construct points: depot is index 0
    points = [{"id": "DEPOT", "lat": depot["lat"], "lon": depot["lon"], "demand": 0}]
    for o in req.orders:
        points.append({"id": o.id, "lat": o.lat, "lon": o.lon, "demand": o.demand})

    # Compute road matrix & snapping
    matrix_res = compute_road_matrix(points)
    scenario_id = f"scen_{uuid.uuid4().hex[:8]}"

    scenario_data = {
        "id": scenario_id,
        "name": req.name,
        "created_at": time.time(),
        "depot": depot,
        "orders": [o.model_dump() for o in req.orders],
        "fleet": req.fleet.model_dump(),
        "points": points,
        "matrix_res": matrix_res,
        "snap_warnings": matrix_res.get("snap_warnings", []),
    }
    _SCENARIOS_STORE[scenario_id] = scenario_data

    return {
        "scenario_id": scenario_id,
        "name": req.name,
        "num_orders": len(req.orders),
        "num_vehicles": req.fleet.num_vehicles,
        "vehicle_capacity": req.fleet.capacity,
        "snap_warnings": matrix_res.get("snap_warnings", []),
    }


@router.get("/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str):
    if scenario_id not in _SCENARIOS_STORE:
        raise HTTPException(status_code=404, detail="Không tìm thấy kịch bản.")
    scen = _SCENARIOS_STORE[scenario_id]
    return {
        "id": scen["id"],
        "name": scen["name"],
        "created_at": scen["created_at"],
        "depot": scen["depot"],
        "orders": scen["orders"],
        "fleet": scen["fleet"],
        "snap_warnings": scen["snap_warnings"],
    }


@router.post("/scenarios/sample")
async def create_sample_scenario():
    """Generates an authentic sample scenario of 15-20 orders in Bình Thạnh."""
    sample_orders = [
        OrderItem(id="ORD-01", address="475A Điện Biên Phủ, HUTECH", lat=10.8015, lon=106.7135, demand=4),
        OrderItem(id="ORD-02", address="Nguyễn Văn Thương (D1), P.25", lat=10.8000, lon=106.7165, demand=3),
        OrderItem(id="ORD-03", address="Pearl Plaza, 561A Điện Biên Phủ", lat=10.7995, lon=106.7180, demand=5),
        OrderItem(id="ORD-04", address="Chung Cư Cầu Văn Thánh Đông", lat=10.7980, lon=106.7205, demand=2),
        OrderItem(id="ORD-05", address="Sảnh Landmark 81, Vinhomes", lat=10.7950, lon=106.7215, demand=6),
        OrderItem(id="ORD-06", address="Nguyễn Hữu Cảnh, P.22", lat=10.7930, lon=106.7160, demand=4),
        OrderItem(id="ORD-07", address="ĐH Giao Thông Vận Tải, D2", lat=10.8030, lon=106.7175, demand=3),
        OrderItem(id="ORD-08", address="Khu Ẩm Thực Nguyễn Gia Trí (D2)", lat=10.8060, lon=106.7170, demand=5),
        OrderItem(id="ORD-09", address="Ngã Ba Ung Văn Khiêm - D2", lat=10.8080, lon=106.7165, demand=2),
        OrderItem(id="ORD-10", address="Đài Liệt Sĩ, Ung Văn Khiêm", lat=10.8085, lon=106.7145, demand=4),
        OrderItem(id="ORD-11", address="Xô Viết Nghệ Tĩnh - Bạch Đằng", lat=10.8050, lon=106.7125, demand=3),
        OrderItem(id="ORD-12", address="Vòng Xoay Hàng Xanh", lat=10.8018, lon=106.7118, demand=5),
        OrderItem(id="ORD-13", address="Phan Chu Trinh, P.14", lat=10.8000, lon=106.7100, demand=4),
        OrderItem(id="ORD-14", address="Cầu Văn Thánh Tây", lat=10.7985, lon=106.7085, demand=3),
        OrderItem(id="ORD-15", address="Nguyễn Cửu Vân, P.17", lat=10.7970, lon=106.7065, demand=2),
        OrderItem(id="ORD-16", address="Huỳnh Đình Hai - Bạch Đằng", lat=10.8035, lon=106.7060, demand=4),
        OrderItem(id="ORD-17", address="Bạch Đằng Tây, P.14", lat=10.8020, lon=106.7020, demand=5),
        OrderItem(id="ORD-18", address="Chợ Bà Chiểu, Bạch Đằng", lat=10.8010, lon=106.6980, demand=3),
    ]

    req = ScenarioCreateRequest(
        name="Kịch bản mẫu: Giao trưa Bình Thạnh (18 đơn)",
        orders=sample_orders,
        fleet=FleetConfig(num_vehicles=5, capacity=40),
    )
    return await create_scenario(req)


# ==============================================================================
# 2. PLANS (SOLVER EXECUTION) ENDPOINTS
# ==============================================================================

@router.post("/plans")
async def create_plan(req: PlanRequest):
    if req.scenario_id not in _SCENARIOS_STORE:
        raise HTTPException(status_code=404, detail="Không tìm thấy kịch bản tương ứng.")

    scen = _SCENARIOS_STORE[req.scenario_id]
    matrix_res = scen["matrix_res"]
    points = scen["points"]
    orders = scen["orders"]
    fleet = scen["fleet"]

    n_cust = len(points) - 1
    demands = [p["demand"] for p in points]
    stops = [
        CVRPStop(
            id=p["id"],
            order_id=p["id"],
            lat=p["lat"],
            lon=p["lon"],
            demand=p["demand"],
        )
        for p in points
    ]
    coords = [[p["lat"], p["lon"]] for p in points]

    instance = CVRPInstance(
        name=scen["name"],
        n_customers=n_cust,
        capacity=fleet["capacity"],
        max_vehicles=fleet["num_vehicles"],
        demands=demands,
        dist_matrix=matrix_res["dist_matrix"],
        time_matrix=matrix_res["time_matrix"],
        stops=stops,
        coords=coords,
    )

    t_start = time.time()
    strategy_to_run = req.strategy.lower()
    fallback_used = False
    fallback_reason = None

    # Handle automatic "best" selection: evaluates baselines and picks highest improvement
    if strategy_to_run in ["best", "recommended"]:
        sol_cw = solve_cvrp_strategy("clarke_wright", instance, leg_geometries=matrix_res["leg_geometries"])
        sol_rand = solve_cvrp_strategy("random", instance, max_steps=50, leg_geometries=matrix_res["leg_geometries"])
        sol_cyclic = solve_cvrp_strategy("cyclic", instance, max_steps=50, leg_geometries=matrix_res["leg_geometries"])

        # Pick the minimum distance solution
        candidates = [("clarke_wright", sol_cw), ("random", sol_rand), ("cyclic", sol_cyclic)]
        candidates.sort(key=lambda x: x[1].total_distance)
        strategy_to_run, solution = candidates[0]

    else:
        try:
            solution = solve_cvrp_strategy(
                strategy=strategy_to_run,
                instance=instance,
                max_steps=req.max_steps,
                max_candidates=req.max_candidates,
                leg_geometries=matrix_res["leg_geometries"],
                t0_c=req.thermal.t0_c,
                tenv_c=req.thermal.tenv_c,
                k_rate=req.thermal.k_rate,
                min_temp=req.thermal.min_temp,
            )
        except Exception as exc:
            logger.error(f"Strategy {strategy_to_run} execution failed: {exc}. Falling back to Cyclic.")
            fallback_used = True
            fallback_reason = str(exc)
            strategy_to_run = "cyclic"
            solution = solve_cvrp_strategy(
                strategy="cyclic",
                instance=instance,
                max_steps=50,
                leg_geometries=matrix_res["leg_geometries"],
                t0_c=req.thermal.t0_c,
                tenv_c=req.thermal.tenv_c,
                k_rate=req.thermal.k_rate,
                min_temp=req.thermal.min_temp,
            )

    t_elapsed = time.time() - t_start

    # Compute CW initial baseline distance for improvement calculation
    cw_init_dist = solution.search_trace[0]["cost"] if solution.search_trace else solution.total_distance
    improvement_pct = 0.0
    if cw_init_dist > 0:
        improvement_pct = max(0.0, round(((cw_init_dist - solution.total_distance) / cw_init_dist) * 100.0, 3))

    plan_id = f"plan_{uuid.uuid4().hex[:8]}"

    plan_result = {
        "plan_id": plan_id,
        "scenario_id": req.scenario_id,
        "strategy_requested": req.strategy,
        "strategy_used": strategy_to_run,
        "fallback": fallback_used,
        "fallback_reason": fallback_reason,
        "runtime_sec": round(t_elapsed, 3),
        "metrics": {
            "total_distance_km": round(solution.total_distance / 1000.0, 2),
            "total_duration_min": round(solution.total_duration_sec / 60.0, 1),
            "cw_initial_distance_km": round(cw_init_dist / 1000.0, 2),
            "improvement_pct": improvement_pct,
            "vehicles_used": len([r for r in solution.routes if len(r) > 0]),
            "thermal_violations_count": sum(r.thermal_violations_count for r in solution.detailed_routes),
            "is_feasible": solution.is_feasible,
        },
        "routes": [
            {
                "vehicle_id": r.vehicle_id,
                "distance_km": r.distance_km,
                "duration_min": r.duration_min,
                "total_load": r.total_load,
                "thermal_violations_count": r.thermal_violations_count,
                "customer_indices": r.customer_indices,
                "stops": [
                    {
                        "node_idx": s.node_idx,
                        "order_id": s.order_id,
                        "lat": s.lat,
                        "lon": s.lon,
                        "arrival_time_sec": s.arrival_time_sec,
                        "elapsed_time_min": s.elapsed_time_min,
                        "demand": s.demand,
                        "remaining_load": s.remaining_load,
                        "estimated_temp_c": s.estimated_temp_c,
                        "thermal_violation": s.thermal_violation,
                    }
                    for s in r.stops
                ],
                "leg_geometries": r.leg_geometries,
            }
            for r in solution.detailed_routes
        ],
        "search_trace": solution.search_trace,
    }

    _PLANS_STORE[plan_id] = plan_result
    return plan_result


@router.get("/plans/{plan_id}")
async def get_plan(plan_id: str):
    if plan_id not in _PLANS_STORE:
        raise HTTPException(status_code=404, detail="Không tìm thấy kế hoạch.")
    return _PLANS_STORE[plan_id]


# ==============================================================================
# 3. STRATEGY LAB / BENCHMARK ENDPOINT (AUTHENTIC CSV DATA)
# ==============================================================================

@router.get("/strategies/benchmark")
async def get_strategy_benchmark():
    """
    Returns authentic experimental results strictly loaded from rel_result/ CSV files.
    Includes comprehensive statistical tests and explanations.
    """
    summary_path = Path("rel_result/summary_by_algorithm.csv")
    paired_path = Path("rel_result/paired_comparisons.csv")
    cost_path = Path("rel_result/per_decision_cost.csv")

    if not summary_path.exists() or not paired_path.exists():
        raise HTTPException(status_code=500, detail="Bộ kết quả rel_result CSV chưa sẵn sàng.")

    with open(summary_path, "r", encoding="utf-8") as f:
        summary_rows = list(csv.DictReader(f))

    with open(paired_path, "r", encoding="utf-8") as f:
        paired_rows = list(csv.DictReader(f))

    with open(cost_path, "r", encoding="utf-8") as f:
        cost_rows = list(csv.DictReader(f))

    return {
        "title": "Kết quả Nghiệm thu Thực nghiệm Thuật toán DQN-CVRP",
        "provenance": "rel_result_test_20261018_142948 (F28 feature set, 24 test instances)",
        "summary_by_algorithm": summary_rows,
        "paired_comparisons": paired_rows,
        "per_decision_cost": cost_rows,
        "academic_conclusions": {
            "dqn_wins": False,
            "best_heuristics": "OR-Tools (GLS, 5 s) đạt gap 0.000%, Random & Cyclic đạt cải thiện cao nhất trên local search.",
            "why_dqn_did_not_win": [
                {
                    "reason": "Dư địa cải thiện từ Clarke-Wright rất nhỏ",
                    "detail": "Trần cải thiện trung bình từ CW chỉ từ 0.56% đến 1.23% (nghiệm cuối vẫn cách OR-Tools 2.4 - 3.1%). Với luật chấp nhận giảm nghiêm ngặt, mọi chiến lược đều tiến về cùng local optimum chung.",
                },
                {
                    "reason": "Lệch miền đặc trưng (Distribution Shift)",
                    "detail": "Đặc trưng no_improve_streak khi validation/test bị lệch miền do patience thay đổi. Khi khôi phục feature_patience = 30 (A3, B2), khoảng cách giữa DQN và baseline thu hẹp nhưng vẫn không vượt được.",
                },
                {
                    "reason": "Chi phí suy luận mạng nơ-ron (Inference Overhead)",
                    "detail": "Trong cùng giới hạn thời gian (Giao thức B2: 0.1s), DQN tốn 0.270 ms/quyết định (so với Random 0.104 ms). Do đó, DQN chỉ đánh giá được 44,487 candidates (~39% so với 114,134 của Random), hạn chế khả năng khai phá không gian nghiệm.",
                },
            ],
        },
    }


# ==============================================================================
# 4. SIMULATION ENDPOINT (SIMULATED DRIVER MOVEMENT ALONG REAL LEGS)
# ==============================================================================

@router.get("/sim/{plan_id}")
async def get_simulation_stream(
    plan_id: str,
    time_offset_sec: float = Query(default=0.0, ge=0.0),
):
    """
    Returns interpolated driver positions along the real road geometries for a plan.
    Strictly labeled as 'MÔ PHỎNG'.
    """
    if plan_id not in _PLANS_STORE:
        raise HTTPException(status_code=404, detail="Không tìm thấy kế hoạch để mô phỏng.")

    plan = _PLANS_STORE[plan_id]
    site_cfg = load_site_config("config/site.yaml")
    thermal_cfg = site_cfg.get("thermal", {})
    t0_c = thermal_cfg.get("T0_celsius", 85.0)
    tenv_c = thermal_cfg.get("Tenv_celsius", 30.0)
    k_rate = thermal_cfg.get("k_cooling_rate", 0.020)
    min_temp = thermal_cfg.get("min_delivery_temp", 60.0)

    sim_vehicles = []

    for route in plan["routes"]:
        v_id = route["vehicle_id"]
        stops = route["stops"]
        geoms = route["leg_geometries"]

        if not stops or not geoms:
            continue

        # Flatten full coordinate trajectory for this vehicle
        flat_trajectory: List[List[float]] = []
        for leg in geoms:
            flat_trajectory.extend(leg)

        if not flat_trajectory:
            flat_trajectory = [[stops[0]["lat"], stops[0]["lon"]]]

        # Interpolate progress along trajectory based on time_offset_sec
        total_route_sec = route["duration_min"] * 60.0
        progress_ratio = min(1.0, time_offset_sec / max(total_route_sec, 1.0))
        target_idx = int(progress_ratio * (len(flat_trajectory) - 1))
        curr_coord = flat_trajectory[target_idx]

        # Calculate current simulated food temperature
        elapsed_min = time_offset_sec / 60.0
        curr_temp = tenv_c + (t0_c - tenv_c) * math.exp(-k_rate * elapsed_min)
        curr_temp = round(curr_temp, 1)

        sim_vehicles.append({
            "vehicle_id": v_id,
            "status": "COMPLETED" if progress_ratio >= 1.0 else "EN_ROUTE",
            "lat": curr_coord[0],
            "lon": curr_coord[1],
            "progress_percent": round(progress_ratio * 100.0, 1),
            "elapsed_time_sec": time_offset_sec,
            "estimated_temp_c": curr_temp,
            "is_thermal_warning": curr_temp < min_temp,
            "label": "MÔ PHỎNG",
        })

    return {
        "plan_id": plan_id,
        "time_offset_sec": time_offset_sec,
        "vehicles": sim_vehicles,
        "is_simulation": True,
        "label": "MÔ PHỎNG",
    }
