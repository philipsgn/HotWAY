"""
Integration Test for Backend Stream & Route Optimization API (Gate G6).
Verifies health probe, T1 multi-criteria routes, T2 VRPTW benchmark,
T3 adaptive routing benchmark, and Server-Sent Events (SSE) telemetry stream.
"""

import json
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_backend_health():
    """Verifies operational liveness and system health metadata."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] is not None


def test_t1_routes_endpoint():
    """Verifies retrieval of certified 4 Pareto-optimal routes (T1)."""
    response = client.get("/api/v1/routes/t1")
    assert response.status_code == 200
    data = response.json()
    assert "routes" in data
    assert "metadata" in data
    assert data.get("attribution") == "MÔ PHỎNG" or data["metadata"].get("attribution") == "MÔ PHỎNG"

    routes = data["routes"]
    for arche in ["fastest", "shortest", "stable", "easiest"]:
        assert arche in routes
        r_info = routes[arche]
        assert "distance_m" in r_info
        assert "expected_time_min" in r_info
        assert "p90_time_min" in r_info
        assert "num_turns" in r_info
        assert "num_left_turns" in r_info
        assert "alley_ratio_pct" in r_info
        assert "coordinates" in r_info
        assert len(r_info["coordinates"]) >= 2


def test_t1_calculate_endpoint():
    """Verifies on-the-fly multi-criteria route calculation via GPS coordinates."""
    payload = {
        "origin_lat": 10.8016,
        "origin_lon": 106.7118,
        "dest_lat": 10.8035,
        "dest_lon": 106.7170,
        "rain": False,
    }
    response = client.post("/api/v1/routes/t1/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "routes" in data
    assert "fastest" in data["routes"]
    assert data["metadata"]["attribution"] == "MÔ PHỎNG"


def test_t2_vrptw_benchmark_endpoint():
    """Verifies T2 VRPTW comparative benchmark across solvers."""
    response = client.get("/api/v1/vrptw/benchmark")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "instances" in data
    assert data["attribution"] == "MÔ PHỎNG"

    summary = data["summary"]
    assert "Google OR-Tools" in summary
    assert "Clarke-Wright + LS" in summary
    assert "Greedy Urgency" in summary

    # Verify Google OR-Tools achieves lowest late rate and backlog penalty
    or_tools = summary["Google OR-Tools"]
    cw = summary["Clarke-Wright + LS"]
    greedy = summary["Greedy Urgency"]

    assert or_tools["mean_late_rate_pct"] < cw["mean_late_rate_pct"]
    assert cw["mean_late_rate_pct"] < greedy["mean_late_rate_pct"]
    assert or_tools["mean_backlog_penalty"] < cw["mean_backlog_penalty"]


def test_t3_benchmark_endpoint():
    """Verifies T3 Adaptive Routing policy benchmark and Wilcoxon tests."""
    response = client.get("/api/v1/routing/t3/benchmark")
    assert response.status_code == 200
    data = response.json()
    assert "scenarios" in data
    assert data["attribution"] == "MÔ PHỎNG"

    scenarios = data["scenarios"]
    assert "Scenario A: Normal Hours (Dry)" in scenarios
    assert "Scenario B: Morning Peak (Dry)" in scenarios
    assert "Scenario C: Evening Peak (Rain & Incidents)" in scenarios

    # In all scenarios, Dynamic Dijkstra outperforms Edge-Scoring DQN
    for sc_name, sc_data in scenarios.items():
        assert "Dynamic Dijkstra" in sc_data
        assert "Edge-Scoring DQN" in sc_data
        assert "wilcoxon_tests" in sc_data

        dijk_time = sc_data["Dynamic Dijkstra"]["mean_time_min"]
        dqn_time = sc_data["Edge-Scoring DQN"]["mean_time_min"]
        assert dijk_time < dqn_time

        # Statistically significant advantage (p < 0.01)
        p_val = sc_data["wilcoxon_tests"]["dqn_vs_dynamic"]["p_value"]
        assert p_val < 0.01


def test_stream_simulation_first_events():
    """Verifies Server-Sent Events (SSE) telemetry stream on Port 8000."""
    with client.stream(
        "GET", "/api/v1/sim/stream?policy=dynamic_dijkstra&speed_mult=100.0"
    ) as response:
        assert response.status_code == 200
        events = []
        for line in response.iter_lines():
            if line.startswith("data: "):
                payload = json.loads(line[6:])
                events.append(payload)
                if len(events) >= 4:
                    break

        assert len(events) >= 4
        # First event is INIT
        assert events[0]["event_type"] == "INIT"
        assert events[0]["policy"] == "dynamic_dijkstra"
        assert events[0]["attribution"] == "MÔ PHỎNG"
        assert "planned_path" in events[0]

        # Subsequent events are PROGRESS or REROUTE
        for ev in events[1:]:
            assert ev["event_type"] in ["PROGRESS", "REROUTE"]
            assert "current_node" in ev
            assert "coordinates" in ev
            assert len(ev["coordinates"]) == 2
            assert "congestion_state" in ev
