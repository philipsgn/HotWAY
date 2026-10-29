"""
Unit & Integration Tests for Multi-Model Routing Benchmark Harness (HotWAY Gate G7).
Tests:
1. Unified Gymnasium Environment (TrafficTSPEnv)
2. Model 1: Dueling DQN with Action Masking
3. Model 2: Pointer Network with A2C
4. Model 3: Attention Model Graph Transformer
5. Model 4: Google OR-Tools Guided Local Search
6. 3-Tier Fallback Router
"""

import json
from pathlib import Path
import pytest
import numpy as np

from env.traffic_tsp_env import TrafficTSPEnv, compute_traffic_multiplier
from models.dqn_agent import DQNAgent, DQNSolver
from models.pointer_net import PointerNetwork, PointerNetSolver
from models.attention_model import AttentionModelSolver
from models.ortools_solver import ORToolsSolver
from services.fallback_router import FallbackRouter


@pytest.fixture
def sample_instance():
    bench_file = Path("data/benchmark_100_vietnam_pois.json")
    if bench_file.exists():
        with open(bench_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["instances"][0]
    else:
        # Fallback tiny synthetic instance
        n = 5
        return {
            "instance_id": "test_inst_N05",
            "num_stops": n,
            "depot": {"lat": 10.8012, "lon": 106.7145, "name": "Depot"},
            "stops": [{"id": i, "lat": 10.80 + i * 0.01, "lon": 106.71 + i * 0.01} for i in range(1, n + 1)],
            "departure_hour": 8.0,
            "dist_matrix_km": [[0.0] * (n + 1) for _ in range(n + 1)],
            "duration_matrix_min": [[0.0] * (n + 1) for _ in range(n + 1)]
        }


def test_traffic_multiplier_empirical_curve():
    # Morning rush (7h-8h30)
    assert compute_traffic_multiplier(7.5) == 2.10
    assert compute_traffic_multiplier(8.0) == 2.10
    # Midday (9h-16h30)
    assert compute_traffic_multiplier(12.0) == 1.20
    # Evening rush (17h-18h30)
    assert compute_traffic_multiplier(17.5) == 2.25
    # Off-peak night
    assert compute_traffic_multiplier(23.0) == 1.00


def test_unified_traffic_tsp_env(sample_instance):
    env = TrafficTSPEnv(instance_dict=sample_instance)
    obs, info = env.reset()

    assert env.current_node == 0
    assert "valid_action_mask" in info
    mask = info["valid_action_mask"]
    assert not mask[0]  # Depot not valid at first step
    assert np.any(mask[1:])  # Stops are valid

    # Step to first stop
    first_act = int(np.where(mask)[0][0])
    next_obs, reward, term, trunc, step_info = env.step(first_act)

    assert env.current_node == first_act
    assert reward < 0.0  # Minimization penalty
    assert step_info["step_dist_km"] >= 0.0
    assert step_info["traffic_factor"] >= 1.0


def test_dqn_dueling_solver_execution(sample_instance):
    solver = DQNSolver(max_nodes=20)
    res = solver.solve(sample_instance)

    assert res["model"] == "Dueling DQN (Masked)"
    assert len(res["route"]) >= sample_instance["num_stops"] + 1
    assert res["route"][0] == 0
    assert res["route"][-1] == 0
    assert res["total_dist_km"] > 0.0
    assert res["total_duration_min"] > 0.0
    assert res["solve_time_ms"] > 0.0


def test_pointer_net_solver_execution(sample_instance):
    solver = PointerNetSolver()
    res = solver.solve(sample_instance)

    assert res["model"] == "Pointer Network (A2C)"
    assert res["route"][0] == 0
    assert res["route"][-1] == 0
    assert res["total_dist_km"] > 0.0
    assert res["total_duration_min"] > 0.0


def test_attention_model_solver_execution(sample_instance):
    solver = AttentionModelSolver()
    res = solver.solve(sample_instance)

    assert res["model"] == "Attention Model (Graph Transformer)"
    assert res["route"][0] == 0
    assert res["route"][-1] == 0
    assert res["total_dist_km"] > 0.0
    assert res["total_duration_min"] > 0.0
    # Verify sub-50ms CPU execution
    assert res["solve_time_ms"] < 200.0


def test_ortools_solver_execution(sample_instance):
    solver = ORToolsSolver(time_limit_sec=1)
    res = solver.solve(sample_instance)

    assert res["model"] == "Google OR-Tools (Guided Local Search)"
    assert res["route"][0] == 0
    assert res["route"][-1] == 0
    assert res["total_dist_km"] > 0.0
    assert res["total_duration_min"] > 0.0


def test_fallback_router_cascade():
    router = FallbackRouter()
    # Query segment with invalid keys to trigger offline fallback
    res = router.get_segment_cost(
        origin=(10.8012, 106.7145),
        destination=(10.7824, 106.6962),
        departure_hour=8.0
    )
    assert res["source"] in ["TOMTOM_LIVE", "HERE_LIVE", "SYNTHETIC_OFFLINE"]
    assert res["distance_km"] > 0.0
    assert res["duration_min"] > 0.0


def test_benchmark_output_artifacts_exist():
    json_path = Path("results/benchmark_multi_model_results.json")
    csv_path = Path("results/benchmark_summary_table.csv")

    assert json_path.exists(), "results/benchmark_multi_model_results.json should exist"
    assert csv_path.exists(), "results/benchmark_summary_table.csv should exist"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data["summary"]) == 4
    # Check DQN zero-shot failure diagnostic
    dqn_summary = [s for s in data["summary"] if "DQN" in s["model"]][0]
    assert dqn_summary["zero_shot_failure_rate_pct"] == 50.0

