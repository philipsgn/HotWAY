"""Tier 1: Road Network Graph and Traffic Congestion Features Verification.

Verifies:
- 64-node planar graph extraction and strong connectivity
- Depot coordinate accuracy (10.9212, 107.2401)
- Positive edge metric lengths and free flow times
- Dynamic traffic congestion model calculations on primary vs residential roads

Authoritative References:
- PRD.md §3.2, §4.1
- survey_rl.md §2.1 - §2.4
- TEST_INFRA.md Features 1, 2, 5
"""

from __future__ import annotations

import unittest
import networkx as nx

from src.rl.osm_graph_loader import (
    DEPOT_LAT,
    DEPOT_LON,
    DEPOT_NAME,
    DEPOT_NODE_ID,
    generate_deterministic_hanggon_graph,
    get_nearest_node,
    haversine_distance_meters,
    load_or_generate_hanggon_graph,
)
from src.rl.traffic_model import (
    compute_edge_traversal,
    get_dynamic_edge_weight,
    get_traffic_multiplier,
)


class TestRoadGraphAndTrafficFeatures(unittest.TestCase):
    """Tier 1 tests for OSMnx graph loading, synthetic graph, and traffic physics."""

    def setUp(self):
        self.graph = load_or_generate_hanggon_graph()

    def test_graph_has_64_nodes_and_is_strongly_connected(self):
        """Verifies 64 nodes and 100% reachability across the graph."""
        self.assertGreaterEqual(self.graph.number_of_nodes(), 64)
        is_strongly_conn = nx.is_strongly_connected(self.graph)
        self.assertTrue(is_strongly_conn, "Road network must be strongly connected")

    def test_depot_node_exists_with_accurate_coordinates(self):
        """Verifies depot node identity, coordinates, and tag."""
        self.assertIn(DEPOT_NODE_ID, self.graph.nodes)
        depot_data = self.graph.nodes[DEPOT_NODE_ID]
        lat = float(depot_data.get("y", depot_data.get("lat", 0.0)))
        lon = float(depot_data.get("x", depot_data.get("lon", 0.0)))
        self.assertAlmostEqual(lat, DEPOT_LAT, places=3)
        self.assertAlmostEqual(lon, DEPOT_LON, places=3)
        self.assertTrue(depot_data.get("is_depot", False))

    def test_edge_attributes_validity(self):
        """Verifies all edges possess strictly positive length, speed limit, and free flow time."""
        for u, v, k, data in self.graph.edges(keys=True, data=True):
            self.assertIn("length", data)
            self.assertGreater(float(data["length"]), 0.0)
            self.assertIn("speed_kph", data)
            self.assertGreater(float(data["speed_kph"]), 0.0)
            self.assertIn("free_flow_time", data)
            self.assertGreater(float(data["free_flow_time"]), 0.0)

    def test_rush_hour_congestion_peak_on_ql56(self):
        """Verifies traffic multiplier peaks at ~2.5x during morning rush (07:45 = min 465)."""
        morning_peak_min = 465.0  # 07:45 AM
        midnight_min = 120.0       # 02:00 AM

        gamma_peak = get_traffic_multiplier(morning_peak_min, highway_type="primary", is_raining=False)
        gamma_night = get_traffic_multiplier(midnight_min, highway_type="primary", is_raining=False)

        self.assertGreaterEqual(gamma_peak, 2.2, "QL56 morning peak traffic should be >= 2.2x")
        self.assertEqual(gamma_night, 1.0, "Midnight traffic should be 1.0x free-flow")

        # Residential roads should have much lower peak congestion
        gamma_residential = get_traffic_multiplier(morning_peak_min, highway_type="residential", is_raining=False)
        self.assertLess(gamma_residential, gamma_peak)

    def test_dynamic_edge_traversal_duration(self):
        """Verifies dynamic edge traversal calculation correctly increases with congestion."""
        length = 1000.0  # 1 km
        speed = 60.0    # 60 km/h

        # Free flow: 1 km at 60 km/h = 60 seconds
        t_sec_free, _, _ = compute_edge_traversal(length, speed, time_minutes=120.0, highway_type="primary")
        self.assertAlmostEqual(t_sec_free, 60.0, delta=1.0)

        # Rush hour peak: ~2.5x slower -> ~150 seconds
        t_sec_rush, _, _ = compute_edge_traversal(length, speed, time_minutes=465.0, highway_type="primary")
        self.assertGreaterEqual(t_sec_rush, 130.0)


if __name__ == "__main__":
    unittest.main()
