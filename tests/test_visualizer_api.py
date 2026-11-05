"""
Unit and Integration Tests for Graph Step-by-Step Pathfinding Visualizer (Gate G6/G7).
Verifies:
1. GraphStepEngine loads and extracts real road network bounds.
2. Dijkstra, A*, Bidirectional, and Dynamic C(t) search algorithms generate valid step-by-step frames.
3. A* Search expands fewer or equal nodes compared to uninformed Dijkstra.
4. FastAPI endpoints GET /map/bounds and POST /api/solve-path return HTTP 200 with valid schema.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.graph_stepper import GraphStepEngine

client = TestClient(app)


@pytest.fixture(scope="module")
def engine():
    return GraphStepEngine.get_instance()


def test_visualizer_engine_bounds(engine):
    """Verifies that the graph engine has valid geographical bounds."""
    bounds = engine.bounds
    assert bounds["total_nodes"] > 1000, f"Expected > 1000 nodes, got {bounds['total_nodes']}"
    assert bounds["total_edges"] > 2000, f"Expected > 2000 edges, got {bounds['total_edges']}"
    assert 10.0 <= bounds["center"][0] <= 11.5, "Center latitude out of HCMC range"
    assert 106.0 <= bounds["center"][1] <= 107.5, "Center longitude out of HCMC range"


def test_visualizer_all_four_algorithms(engine):
    """Verifies that all 4 algorithms solve paths and return non-empty steps and paths."""
    start_lat, start_lon = 10.795, 106.710
    end_lat, end_lon = 10.805, 106.720

    algos = ["a_star", "dijkstra", "bidirectional", "dynamic_c_t"]
    results = {}

    for algo in algos:
        res = engine.solve(start_lat, start_lon, end_lat, end_lon, algorithm=algo, max_steps=600)
        assert len(res["steps"]) > 0, f"No steps recorded for {algo}"
        assert len(res["final_path"]) >= 2, f"Final path too short for {algo}"
        assert res["metrics"]["distance_km"] > 0.5, f"Path distance too short for {algo}"
        assert res["metrics"]["compute_time_ms"] >= 0.0, f"Invalid compute time for {algo}"
        results[algo] = res

    # Algorithmic property: A* should expand significantly fewer nodes than standard Dijkstra
    astar_steps = results["a_star"]["metrics"]["total_steps_recorded"]
    dijkstra_steps = results["dijkstra"]["metrics"]["total_steps_recorded"]
    assert astar_steps < dijkstra_steps, (
        f"A* ({astar_steps} steps) must expand fewer nodes than Dijkstra ({dijkstra_steps} steps) on direct path!"
    )


def test_api_map_bounds_endpoint():
    """Verifies that GET /map/bounds returns HTTP 200 and required fields."""
    response = client.get("/map/bounds")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "bounds" in data
    assert len(data["sample_landmarks"]) >= 3
    assert len(data["supported_algorithms"]) == 4


def test_api_solve_path_endpoint():
    """Verifies that POST /api/solve-path returns HTTP 200 with chronological steps."""
    payload = {
        "start_coords": [10.7951, 106.7218],  # Landmark 81
        "end_coords": [10.8014, 106.7112],    # Hang Xanh
        "algorithm": "a_star",
        "max_steps": 500,
    }
    response = client.post("/api/solve-path", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "success"
    data = res["data"]
    assert "steps" in data
    assert len(data["steps"]) > 0
    assert "final_path" in data
    assert len(data["final_path"]) >= 2
    assert "metrics" in data
    assert data["metrics"]["distance_km"] > 0.0
