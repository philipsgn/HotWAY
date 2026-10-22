"""
Empirical Stress Test & Verification Suite for HotWAY Benchmark Routing Service
Target: backend/app/services/routing_service.py and FastAPI spatial endpoints.

Checks:
1. Schema & FeatureCollection validity (keys, properties, GeoJSON structures).
2. Bình Thạnh GPS bounding box validity (all lat in [10.79, 10.81], lon in [106.71, 106.73]).
3. Newton cooling thermal physics (Dijkstra < 65.0°C, DQN > 75.0°C, monotone decay).
4. Route transit duration & bottleneck rush hour penalty (Dijkstra > DQN, delay=270s).
5. Dual prefix API routing (/api/spatial/benchmark-routes and /api/v1/spatial/benchmark-routes).

Can be run via:
    pytest backend/tests/test_benchmark_routing_empirical.py -v
or:
    python backend/tests/test_benchmark_routing_empirical.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List

# Ensure project root is on sys.path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.services.routing_service import (
    DEPOT_LAT,
    DEPOT_LON,
    DEPOT_NAME,
    LANDMARK_81_LAT,
    LANDMARK_81_LON,
    LANDMARK_81_NAME,
    HANG_XANH_NAME,
    DIJKSTRA_COORDINATES,
    DIJKSTRA_WAYPOINTS,
    DQN_COORDINATES,
    DQN_WAYPOINTS,
    routing_service,
)
from backend.app.main import app

# Target Bình Thạnh Bounding Box
LAT_MIN: float = 10.79
LAT_MAX: float = 10.81
LON_MIN: float = 106.71
LON_MAX: float = 106.73


class TestBenchmarkRoutingServiceEmpirical(unittest.TestCase):
    """Empirical unit and invariant tests for the routing service."""

    def setUp(self) -> None:
        self.data: Dict[str, Any] = routing_service.get_benchmark_routes()

    def test_01_top_level_schema_and_keys(self) -> None:
        """Verify top-level keys and FeatureCollection standard conformity."""
        required_keys = {"type", "name", "depot", "destination", "routes", "features", "metadata"}
        self.assertTrue(
            required_keys.issubset(self.data.keys()),
            f"Missing required keys in get_benchmark_routes(). Present: {list(self.data.keys())}",
        )
        self.assertEqual(self.data["type"], "FeatureCollection")
        self.assertEqual(self.data["name"], "binhthanh_benchmark_routes")
        self.assertIsInstance(self.data["features"], list)
        self.assertEqual(len(self.data["features"]), 2, "Expected exactly 2 route features (Dijkstra and DQN)")

    def test_02_feature_structure_and_properties(self) -> None:
        """Verify GeoJSON Feature structure, IDs, geometries, and property payloads."""
        feature_ids = [f.get("id") for f in self.data["features"]]
        self.assertIn("dijkstra_route", feature_ids)
        self.assertIn("dqn_route", feature_ids)

        expected_properties = {
            "id",
            "name",
            "algorithm",
            "color",
            "stroke_style",
            "distance_meters",
            "travel_time_seconds",
            "final_temperature_c",
            "delay_seconds",
            "summary",
        }

        for feature in self.data["features"]:
            self.assertEqual(feature.get("type"), "Feature")
            self.assertIn("geometry", feature)
            geometry = feature["geometry"]
            self.assertEqual(geometry.get("type"), "LineString")
            self.assertIsInstance(geometry.get("coordinates"), list)
            self.assertGreater(len(geometry["coordinates"]), 2)

            props = feature.get("properties", {})
            self.assertTrue(
                expected_properties.issubset(props.keys()),
                f"Feature {feature.get('id')} missing properties: {expected_properties - props.keys()}",
            )

    def test_03_coordinates_validity_in_binh_thanh_bbox(self) -> None:
        """Verify all coordinates (GeoJSON [lon, lat] and waypoints) fall strictly inside Bình Thạnh range."""
        # 1. Check Depot
        self.assertTrue(
            LAT_MIN <= DEPOT_LAT <= LAT_MAX,
            f"Depot LAT {DEPOT_LAT} outside [{LAT_MIN}, {LAT_MAX}]",
        )
        self.assertTrue(
            LON_MIN <= DEPOT_LON <= LON_MAX,
            f"Depot LON {DEPOT_LON} outside [{LON_MIN}, {LON_MAX}]",
        )

        # 2. Check Destination (Landmark 81)
        self.assertTrue(
            LAT_MIN <= LANDMARK_81_LAT <= LAT_MAX,
            f"Destination LAT {LANDMARK_81_LAT} outside [{LAT_MIN}, {LAT_MAX}]",
        )
        self.assertTrue(
            LON_MIN <= LANDMARK_81_LON <= LON_MAX,
            f"Destination LON {LANDMARK_81_LON} outside [{LON_MIN}, {LON_MAX}]",
        )

        # 3. Check GeoJSON LineString Coordinates [lon, lat]
        for route_name, coords in [("Dijkstra", DIJKSTRA_COORDINATES), ("DQN", DQN_COORDINATES)]:
            for idx, pt in enumerate(coords):
                self.assertEqual(len(pt), 2, f"{route_name} coord #{idx} must be [lon, lat]")
                lon, lat = pt[0], pt[1]
                self.assertGreaterEqual(
                    lat, LAT_MIN,
                    f"{route_name} coord #{idx} lat {lat} < {LAT_MIN}"
                )
                self.assertLessEqual(
                    lat, LAT_MAX,
                    f"{route_name} coord #{idx} lat {lat} > {LAT_MAX}"
                )
                self.assertGreaterEqual(
                    lon, LON_MIN,
                    f"{route_name} coord #{idx} lon {lon} < {LON_MIN}"
                )
                self.assertLessEqual(
                    lon, LON_MAX,
                    f"{route_name} coord #{idx} lon {lon} > {LON_MAX}"
                )

        # 4. Check Waypoint Coordinates
        for route_name, waypoints in [("Dijkstra", DIJKSTRA_WAYPOINTS), ("DQN", DQN_WAYPOINTS)]:
            for idx, wp in enumerate(waypoints):
                lat = wp["lat"]
                lon = wp["lon"]
                self.assertGreaterEqual(
                    lat, LAT_MIN,
                    f"{route_name} waypoint #{idx} lat {lat} < {LAT_MIN}"
                )
                self.assertLessEqual(
                    lat, LAT_MAX,
                    f"{route_name} waypoint #{idx} lat {lat} > {LAT_MAX}"
                )
                self.assertGreaterEqual(
                    lon, LON_MIN,
                    f"{route_name} waypoint #{idx} lon {lon} < {LON_MIN}"
                )
                self.assertLessEqual(
                    lon, LON_MAX,
                    f"{route_name} waypoint #{idx} lon {lon} > {LON_MAX}"
                )

    def test_04_temperature_physics_invariants(self) -> None:
        """
        Verify Newton Cooling constraints:
        - Dijkstra final temperature MUST be < 65.0°C (degraded quality).
        - DQN final temperature MUST be > 75.0°C (delicious soup quality).
        - Initial temperature starts at 88.0°C.
        - Monotonic cooling along the route waypoints.
        """
        dijkstra_route = self.data["routes"]["dijkstra"]
        dqn_route = self.data["routes"]["dqn_rl"]

        dijkstra_temp = dijkstra_route["final_temperature_c"]
        dqn_temp = dqn_route["final_temperature_c"]

        # Requirement 2 checks:
        self.assertLess(
            dijkstra_temp, 65.0,
            f"Dijkstra final temperature must be < 65.0°C, got {dijkstra_temp}°C",
        )
        self.assertGreater(
            dqn_temp, 75.0,
            f"DQN final temperature must be > 75.0°C, got {dqn_temp}°C",
        )

        # Ambient & initial temp boundary checks:
        ambient_temp = self.data["metadata"]["ambient_temp_c"]
        initial_temp = self.data["metadata"]["initial_temp_c"]
        self.assertEqual(ambient_temp, 30.0)
        self.assertEqual(initial_temp, 88.0)
        self.assertGreater(dijkstra_temp, ambient_temp, "Delivered temperature cannot drop below ambient")
        self.assertGreater(dqn_temp, ambient_temp, "Delivered temperature cannot drop below ambient")

        # Monotonic cooling check along waypoints
        for route_name, waypoints in [("Dijkstra", dijkstra_route["waypoints"]), ("DQN", dqn_route["waypoints"])]:
            self.assertEqual(waypoints[0]["temp_c"], 88.0, f"{route_name} must start at 88.0°C")
            self.assertEqual(
                waypoints[-1]["temp_c"],
                dijkstra_temp if route_name == "Dijkstra" else dqn_temp,
                f"{route_name} final waypoint temp must match final_temperature_c",
            )
            for i in range(len(waypoints) - 1):
                t_curr = waypoints[i]["temp_c"]
                t_next = waypoints[i + 1]["temp_c"]
                self.assertGreaterEqual(
                    t_curr, t_next,
                    f"{route_name} cooling violation at step {i}->{i+1}: {t_curr}°C to {t_next}°C",
                )

    def test_05_route_lengths_and_transit_times(self) -> None:
        """
        Verify route transit times and rush-hour bottleneck delay penalty:
        - Dijkstra must show longer duration due to bottleneck rush-hour penalty than DQN.
        - Dijkstra transit duration = 650.0s > DQN duration = 380.0s.
        - Dijkstra delay_seconds = 270.0s, bottleneck = Hàng Xanh.
        - DQN delay_seconds = 0.0s.
        """
        dijkstra_route = self.data["routes"]["dijkstra"]
        dqn_route = self.data["routes"]["dqn_rl"]

        dijkstra_duration = dijkstra_route["travel_time_seconds"]
        dqn_duration = dqn_route["travel_time_seconds"]

        self.assertGreater(
            dijkstra_duration, dqn_duration,
            f"Dijkstra duration ({dijkstra_duration}s) must exceed DQN duration ({dqn_duration}s)",
        )
        self.assertEqual(dijkstra_duration, 650.0)
        self.assertEqual(dqn_duration, 380.0)

        # Delay penalty check
        self.assertGreater(dijkstra_route["delay_seconds"], 0.0)
        self.assertEqual(dijkstra_route["delay_seconds"], 270.0)
        self.assertEqual(dqn_route["delay_seconds"], 0.0)

        # Bottleneck attribution check
        self.assertEqual(dijkstra_route["bottleneck_node"], "dbp_05")
        self.assertIn("Hàng Xanh", dijkstra_route["bottleneck_name"])
        self.assertIsNone(dqn_route["bottleneck_node"])

    def test_06_rush_hour_parameter_toggle(self) -> None:
        """Verify behavior when rush_hour parameter is toggled."""
        normal_data = routing_service.get_benchmark_routes(rush_hour=False)
        rush_data = routing_service.get_benchmark_routes(rush_hour=True)

        self.assertEqual(normal_data["routes"]["dijkstra"]["rush_hour_multiplier"], 1.0)
        self.assertEqual(rush_data["routes"]["dijkstra"]["rush_hour_multiplier"], 3.0)


class TestFastApiDualPrefixEndpointsEmpirical(unittest.TestCase):
    """Empirical verification of FastAPI routes, dual prefix registration and HTTP responses."""

    def test_07_dual_prefix_route_registration_in_app(self) -> None:
        """Verify both /api/spatial/benchmark-routes and /api/v1/spatial/benchmark-routes exist in app.routes."""
        registered_paths = [route.path for route in app.routes]

        prefix_1 = "/api/spatial/benchmark-routes"
        prefix_2 = "/api/v1/spatial/benchmark-routes"

        self.assertIn(
            prefix_1, registered_paths,
            f"Prefix {prefix_1} is not registered in FastAPI app routes. Routes: {registered_paths}",
        )
        self.assertIn(
            prefix_2, registered_paths,
            f"Prefix {prefix_2} is not registered in FastAPI app routes. Routes: {registered_paths}",
        )

    def test_08_dual_prefix_endpoint_execution_via_testclient(self) -> None:
        """Perform simulated HTTP requests to both endpoints and verify responses."""
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            # Test /api prefix
            resp1 = client.get("/api/spatial/benchmark-routes")
            self.assertEqual(resp1.status_code, 200, f"/api failed with {resp1.status_code}: {resp1.text}")
            payload1 = resp1.json()

            # Test /api/v1 prefix
            resp2 = client.get("/api/v1/spatial/benchmark-routes")
            self.assertEqual(resp2.status_code, 200, f"/api/v1 failed with {resp2.status_code}: {resp2.text}")
            payload2 = resp2.json()

            # Verify identical output across both dual prefixes
            self.assertEqual(payload1["type"], payload2["type"])
            self.assertEqual(
                payload1["routes"]["dijkstra"]["final_temperature_c"],
                payload2["routes"]["dijkstra"]["final_temperature_c"],
            )
            self.assertEqual(
                payload1["routes"]["dqn_rl"]["final_temperature_c"],
                payload2["routes"]["dqn_rl"]["final_temperature_c"],
            )
            self.assertEqual(payload1["features"], payload2["features"])

            # Verify query params on /api/v1
            resp_no_rush = client.get("/api/v1/spatial/benchmark-routes?rush_hour=false")
            self.assertEqual(resp_no_rush.status_code, 200)
            data_no_rush = resp_no_rush.json()
            self.assertEqual(
                data_no_rush["routes"]["dijkstra"]["rush_hour_multiplier"],
                1.0,
            )


if __name__ == "__main__":
    unittest.main()
