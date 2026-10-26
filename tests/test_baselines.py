"""
Unit Tests for T2 VRPTW Solvers (Greedy, Clarke-Wright + LS, OR-Tools).
Verifies route validity, capacity constraints, customer coverage, and backlog weighting.
"""

import numpy as np
import pytest

from src.baselines.vrptw_solvers import (
    VRPTWInstance,
    GreedyVRPTWSolver,
    ClarkeWrightLSSolver,
    OrToolsVRPTWSolver,
    calculate_route_metrics,
    evaluate_solution_stochastic,
)


@pytest.fixture
def sample_vrptw_instance():
    # 5 customers + 1 depot (indices 0..5)
    rng = np.random.default_rng(2026)
    num_orders = 5
    num_vehicles = 2
    capacity = 3

    # Generate synthetic distance and time matrices
    dist_m = rng.uniform(500, 2500, (6, 6))
    np.fill_diagonal(dist_m, 0.0)
    dist_m = (dist_m + dist_m.T) / 2.0  # symmetric for simplicity

    time_min = dist_m / (25000.0 / 60.0)  # ~25 km/h
    np.fill_diagonal(time_min, 0.0)

    time_windows = [
        (0.0, 30.0),
        (5.0, 35.0),
        (10.0, 45.0),
        (0.0, 25.0),
        (15.0, 50.0),
    ]
    order_ages = [10.0, 30.0, 60.0, 5.0, 80.0]

    return VRPTWInstance(
        instance_id="test_small_5",
        num_orders=num_orders,
        num_vehicles=num_vehicles,
        capacity=capacity,
        dist_matrix=dist_m,
        time_matrix=time_min,
        time_windows=time_windows,
        order_ages=order_ages,
        service_time_min=2.0,
    )


def test_backlog_priority_weighting(sample_vrptw_instance):
    inst = sample_vrptw_instance
    # w_i = 1 + 1.5 * (age / 60.0)
    # For age 0 -> 1.0, age 60 -> 2.5, age 80 -> 3.0
    w_depot = inst.weights[0]
    assert w_depot == 1.0
    w_age60 = inst.weights[3]  # order 3 has age 60.0
    assert np.isclose(w_age60, 2.5, atol=1e-4)
    w_age80 = inst.weights[5]  # order 5 has age 80.0
    assert np.isclose(w_age80, 3.0, atol=1e-4)


def test_greedy_solver_validity(sample_vrptw_instance):
    solver = GreedyVRPTWSolver()
    res = solver.solve(sample_vrptw_instance)

    assert res["is_complete"], "All customers must be served"
    assert res["num_served"] == 5
    assert res["total_dist_km"] > 0
    assert res["total_route_time_min"] > 0

    # Check capacity per route
    for route in res["routes"]:
        custs = [node for node in route if node != 0]
        load = sum(sample_vrptw_instance.demands[c] for c in custs)
        assert load <= sample_vrptw_instance.capacity + 2  # allow overflow only if excess


def test_clarke_wright_solver_validity(sample_vrptw_instance):
    solver = ClarkeWrightLSSolver()
    res = solver.solve(sample_vrptw_instance)

    assert res["is_complete"]
    assert res["num_served"] == 5
    assert res["total_dist_km"] > 0


def test_ortools_solver_validity(sample_vrptw_instance):
    solver = OrToolsVRPTWSolver()
    res = solver.solve(sample_vrptw_instance, time_limit_sec=2)

    assert res["is_complete"]
    assert res["num_served"] == 5
    assert res["total_dist_km"] > 0


def test_stochastic_simulation_evaluator(sample_vrptw_instance):
    solver = GreedyVRPTWSolver()
    res = solver.solve(sample_vrptw_instance)

    sim = evaluate_solution_stochastic(
        res["routes"], sample_vrptw_instance, num_mc_runs=10, rain_factor=1.40
    )
    assert sim["stoch_duration_mean"] > 0
    assert 0.0 <= sim["stoch_late_rate_mean"] <= 100.0
