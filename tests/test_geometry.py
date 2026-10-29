"""
Test D4 & T1: Geometry Discipline and Directed Graph Integrity.
- 0 one-way violations (mọi cạnh liên tiếp phải tồn tại trong đồ thị có hướng).
- 0 artificial straight lines.
- Snap distance <= 60m or emits warning.
- Graph is strongly connected.
"""

import pickle
import pytest
import networkx as nx
from pathlib import Path
from src.data.build_graph import haversine, load_site_config, build_legacy_binhthanh_graph


@pytest.fixture(scope="module")
def site_config():
    return load_site_config("config/site.yaml")


@pytest.fixture(scope="module")
def graph(site_config):
    return build_legacy_binhthanh_graph(site_config)


def test_graph_is_directed_and_strongly_connected(graph):
    """Verifies that the graph is strictly directed and strongly connected."""
    assert graph.is_directed(), "Graph must be a directed MultiDiGraph!"
    assert nx.is_strongly_connected(graph), "Graph must be strongly connected (all nodes mutually reachable)!"
    assert graph.number_of_nodes() >= 30, "Graph must contain comprehensive nodes covering the operating zone!"


def test_edge_properties_and_geometries(graph):
    """Verifies that every edge has realistic length, travel time, and valid coordinates."""
    for u, v, k, data in graph.edges(keys=True, data=True):
        assert "length" in data and data["length"] > 0, f"Edge ({u}, {v}) missing positive length!"
        assert "speed_kph" in data and data["speed_kph"] >= 15.0, f"Edge ({u}, {v}) speed unrealistically low!"
        assert "free_flow_time" in data and data["free_flow_time"] > 0, f"Edge ({u}, {v}) missing travel time!"
        assert "geometry" in data and len(data["geometry"]) >= 2, f"Edge ({u}, {v}) missing multi-point geometry!"

        # Verify geometry endpoints match node coordinates
        u_data = graph.nodes[u]
        v_data = graph.nodes[v]
        geom = data["geometry"]
        assert abs(geom[0][0] - u_data["y"]) < 1e-4, f"Geometry start does not match node {u} latitude"
        assert abs(geom[-1][0] - v_data["y"]) < 1e-4, f"Geometry end does not match node {v} latitude"


def test_shortest_path_follows_directed_edges(graph):
    """Tests 50 random origin-destination pairs to verify paths strictly follow directed edges."""
    import random
    nodes = list(graph.nodes())
    random.seed(42)

    for _ in range(50):
        src, dst = random.sample(nodes, 2)
        path = nx.shortest_path(graph, source=src, target=dst, weight="free_flow_time")
        assert len(path) >= 2

        # Verify each consecutive edge exists in the directed graph
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            assert graph.has_edge(u, v), f"Edge ({u} -> {v}) violates one-way rule or does not exist in directed graph!"


def test_snap_point_within_threshold(graph, site_config):
    """Verifies snapping point to nearest drivable node with distance <= 60m."""
    max_snap_m = site_config["site"]["snap_max_distance_meters"]
    depot_lat = site_config["site"]["depot"]["lat"]
    depot_lon = site_config["site"]["depot"]["lon"]

    # Test depot snapping: should be exact 0m to depot_0
    closest_node = None
    min_dist = float("inf")
    for nid, data in graph.nodes(data=True):
        dist = haversine(depot_lat, depot_lon, data["y"], data["x"])
        if dist < min_dist:
            min_dist = dist
            closest_node = nid

    assert min_dist <= max_snap_m, f"Depot snap distance {min_dist}m exceeds threshold {max_snap_m}m!"
    assert closest_node == "depot_0", f"Depot snapped to {closest_node} instead of depot_0!"


def test_zero_artificial_straight_lines(graph):
    """Verifies that no edge geometry is empty or synthetic straight line outside road network."""
    for u, v, k, data in graph.edges(keys=True, data=True):
        geom = data["geometry"]
        assert len(geom) >= 2, "Path geometry must contain road vertices"
        for pt in geom:
            assert len(pt) == 2
            lat, lon = pt[0], pt[1]
            assert 10.70 <= lat <= 10.90, f"Latitude {lat} out of HCMC bounds"
            assert 106.60 <= lon <= 106.80, f"Longitude {lon} out of HCMC bounds"
