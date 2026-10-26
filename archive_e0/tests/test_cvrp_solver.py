"""
Test T2 & T5: CVRP Solver Feasibility, Validator Independence, and Performance.
- Confirms 100% feasibility across Clarke-Wright, Random, Cyclic, Greedy, DQN, and Double DQN.
- Every customer visited exactly once.
- All routes respect capacity <= Q and vehicles <= K.
- Performance check: Runtime <= 10s.
"""

import time
import pytest
from src.cvrp_solver.problem import CVRPInstance, CVRPStop
from src.cvrp_solver.search import solve_cvrp_strategy
from src.cvrp_solver.validator import validate_cvrp_solution
from src.services.road_matrix import compute_road_matrix


@pytest.fixture(scope="module")
def sample_cvrp_instance():
    # 20 customer stops around Bình Thạnh depot
    points = [
        {"id": "DEPOT", "lat": 10.8012, "lon": 106.7145, "demand": 0},
        {"id": "ORD_01", "lat": 10.8015, "lon": 106.7135, "demand": 4},
        {"id": "ORD_02", "lat": 10.8000, "lon": 106.7165, "demand": 3},
        {"id": "ORD_03", "lat": 10.7995, "lon": 106.7180, "demand": 5},
        {"id": "ORD_04", "lat": 10.7980, "lon": 106.7205, "demand": 2},
        {"id": "ORD_05", "lat": 10.7950, "lon": 106.7215, "demand": 6},
        {"id": "ORD_06", "lat": 10.7930, "lon": 106.7160, "demand": 4},
        {"id": "ORD_07", "lat": 10.8030, "lon": 106.7175, "demand": 3},
        {"id": "ORD_08", "lat": 10.8060, "lon": 106.7170, "demand": 5},
        {"id": "ORD_09", "lat": 10.8080, "lon": 106.7165, "demand": 2},
        {"id": "ORD_10", "lat": 10.8085, "lon": 106.7145, "demand": 4},
        {"id": "ORD_11", "lat": 10.8050, "lon": 106.7125, "demand": 3},
        {"id": "ORD_12", "lat": 10.8018, "lon": 106.7118, "demand": 5},
        {"id": "ORD_13", "lat": 10.8000, "lon": 106.7100, "demand": 4},
        {"id": "ORD_14", "lat": 10.7985, "lon": 106.7085, "demand": 3},
        {"id": "ORD_15", "lat": 10.7970, "lon": 106.7065, "demand": 2},
        {"id": "ORD_16", "lat": 10.8035, "lon": 106.7060, "demand": 4},
        {"id": "ORD_17", "lat": 10.8020, "lon": 106.7020, "demand": 5},
        {"id": "ORD_18", "lat": 10.8010, "lon": 106.6980, "demand": 3},
        {"id": "ORD_19", "lat": 10.8030, "lon": 106.6950, "demand": 2},
        {"id": "ORD_20", "lat": 10.8120, "lon": 106.7135, "demand": 4},
    ]

    matrix_res = compute_road_matrix(points)
    n = len(points) - 1
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

    return (
        CVRPInstance(
            name="TestInstance_20_BinhThanh",
            n_customers=n,
            capacity=40,
            max_vehicles=5,
            demands=demands,
            dist_matrix=matrix_res["dist_matrix"],
            time_matrix=matrix_res["time_matrix"],
            stops=stops,
            coords=coords,
        ),
        matrix_res["leg_geometries"],
    )


@pytest.mark.parametrize("strategy", ["clarke_wright", "random", "cyclic", "greedy", "dqn", "double_dqn"])
def test_strategy_solution_is_feasible(sample_cvrp_instance, strategy):
    instance, leg_geoms = sample_cvrp_instance
    t0 = time.time()
    solution = solve_cvrp_strategy(
        strategy=strategy,
        instance=instance,
        max_steps=30,
        max_candidates=64,
        seed=42,
        leg_geometries=leg_geoms,
    )
    elapsed = time.time() - t0

    # T5 Performance check: <= 10 seconds
    assert elapsed <= 10.0, f"Strategy {strategy} took {elapsed:.2f}s > 10s!"

    # T2 Feasibility check
    assert solution.is_feasible, f"Strategy {strategy} produced infeasible solution: {solution.rejection_reason}"
    assert solution.total_distance > 0.0

    # Independent validator verification
    is_valid, dist, msg = validate_cvrp_solution(solution.routes, instance)
    assert is_valid, f"Independent validator rejected {strategy}: {msg}"
    assert abs(dist - solution.total_distance) < 0.1

    # Verify every customer is visited exactly once
    visited = [node for r in solution.routes for node in r]
    assert sorted(visited) == list(range(1, instance.n_customers + 1))

    # Verify search trace has step entries
    assert len(solution.search_trace) >= 1
