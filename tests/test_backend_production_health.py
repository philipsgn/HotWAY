"""
Comprehensive Production Health & Endpoint Parity Integration Test Suite.
Verifies that:
1. Both backend entrypoints (`backend.app.main:app` and `api.main:app`) mount 100% of endpoints.
2. NCO multi-model serving (/optimize-route, /benchmark/summary) functions flawlessly.
3. Pathfinding visualizer (/map/bounds, /api/solve-path) functions flawlessly.
4. T1 multi-criteria routing (/api/v1/routes/t1, /api/v1/routes/t1/calculate) functions flawlessly.
5. Invalid coordinates (e.g. lat > 90, like the 107.798 bug) are rejected cleanly with HTTP 422.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app as monolith_app
from api.main import app as micro_app

client_monolith = TestClient(monolith_app)
client_micro = TestClient(micro_app)


# =========================================================================
# 1. Monolith App (backend.app.main:app) Verification
# =========================================================================

def test_monolith_health():
    res = client_monolith.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_monolith_map_bounds():
    res = client_monolith.get("/map/bounds")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "bounds" in data


def test_monolith_solve_path_valid():
    payload = {
        "start_coords": [10.7951, 106.7218],
        "end_coords": [10.8014, 106.7112],
        "algorithm": "a_star",
        "max_steps": 300,
    }
    res = client_monolith.post("/api/solve-path", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data["steps"]) > 0
    assert len(data["final_path"]) >= 2


def test_monolith_optimize_route():
    payload = {
        "depot": {"id": "depot", "lat": 10.8012, "lon": 106.7145, "name": "Hub Binh Thanh"},
        "stops": [
            {"id": "stop_1", "lat": 10.8021, "lon": 106.7148, "name": "HUTECH"},
            {"id": "stop_2", "lat": 10.7951, "lon": 106.7218, "name": "Landmark 81"},
        ],
        "departure_hour": 8.0,
        "model": "am",
    }
    res = client_monolith.post("/optimize-route", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["result"]["valid"] is True
    assert len(data["result"]["route"]) == 4  # depot -> stop1 -> stop2 -> depot


def test_monolith_benchmark_summary():
    res = client_monolith.get("/benchmark/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert len(data["summary"]) >= 4


def test_monolith_t1_routes():
    res = client_monolith.get("/api/v1/routes/t1")
    assert res.status_code == 200
    data = res.json()
    assert "routes" in data
    assert "fastest" in data["routes"]


def test_monolith_t1_calculate():
    payload = {
        "origin_lat": 10.8012,
        "origin_lon": 106.7145,
        "dest_lat": 10.7950,
        "dest_lon": 106.7215,
        "rain": False,
    }
    res = client_monolith.post("/api/v1/routes/t1/calculate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "routes" in data
    assert "fastest" in data["routes"]


# =========================================================================
# 2. Microservice App (api.main:app) Verification (Dual-Mount Parity)
# =========================================================================

def test_micro_health():
    res = client_micro.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_micro_map_bounds():
    res = client_micro.get("/map/bounds")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"


def test_micro_solve_path():
    payload = {
        "start_coords": [10.7951, 106.7218],
        "end_coords": [10.8014, 106.7112],
        "algorithm": "bidirectional",
        "max_steps": 300,
    }
    res = client_micro.post("/api/solve-path", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data["steps"]) > 0


def test_micro_optimize_route():
    payload = {
        "depot": {"id": "depot", "lat": 10.8012, "lon": 106.7145, "name": "Hub Binh Thanh"},
        "stops": [
            {"id": "stop_1", "lat": 10.8021, "lon": 106.7148, "name": "HUTECH"},
        ],
        "model": "am",
    }
    res = client_micro.post("/optimize-route", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "success"


def test_micro_t1_routes():
    res = client_micro.get("/api/v1/routes/t1")
    assert res.status_code == 200
    assert "routes" in res.json()


# =========================================================================
# 3. Validation & Boundary Rejection Tests (Anti-Crash Guarantee)
# =========================================================================

def test_reject_invalid_latitude_visualizer():
    """Verifies that latitude > 90 (such as the 107.798 typo) is rejected cleanly with HTTP 422."""
    payload = {
        "start_coords": [107.798, 106.7218],  # Invalid latitude > 90!
        "end_coords": [10.8014, 106.7112],
        "algorithm": "a_star",
    }
    res = client_monolith.post("/api/solve-path", json=payload)
    assert res.status_code == 422, f"Expected 422 Unprocessable Entity, got {res.status_code}"


def test_reject_invalid_latitude_t1():
    """Verifies that latitude > 90 in T1 calculate is rejected with HTTP 422."""
    payload = {
        "origin_lat": 107.798,  # Invalid latitude > 90!
        "origin_lon": 106.7145,
        "dest_lat": 10.7950,
        "dest_lon": 106.7215,
    }
    res = client_monolith.post("/api/v1/routes/t1/calculate", json=payload)
    assert res.status_code == 422, f"Expected 422, got {res.status_code}"


def test_reject_invalid_longitude_nco():
    """Verifies that longitude > 180 in NCO optimize-route is rejected with HTTP 422."""
    payload = {
        "depot": {"id": "depot", "lat": 10.8012, "lon": 106.7145},
        "stops": [
            {"id": "stop_1", "lat": 10.8021, "lon": 250.0},  # Invalid longitude > 180!
        ],
    }
    res = client_monolith.post("/optimize-route", json=payload)
    assert res.status_code == 422, f"Expected 422, got {res.status_code}"
