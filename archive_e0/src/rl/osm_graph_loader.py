"""HotWAY OpenStreetMap Road Network Loader and Synthetic Graph Generator.

Provides road network extraction for Hàng Gòn (Long Khánh, Đồng Nai) with:
1. Loading/saving GraphML networks (data/hanggon_graph.graphml).
2. Online download via OSMnx when requested and internet is accessible.
3. Deterministic synthetic fallback graph with 64 realistic nodes and edges
   modeling the QL56 corridor, commune branch roads, and alleys for air-gapped
   and offline test environments.
4. Proper attribute typing: length (m), speed_kph (km/h), free_flow_time (s).
5. GeoJSON export for road segments and 3D building footprints.

Authoritative References:
- PRD.md §4.1, TECH_ARCHITECTURE.md §2
- survey_rl.md §2.1 - §2.3
- TEST_INFRA.md Features 1 & 2
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx

logger = logging.getLogger(__name__)

# Authoritative Depot Coordinates
DEPOT_LAT: float = 10.9212
DEPOT_LON: float = 107.2401
DEPOT_NODE_ID: str = "depot_0"
DEPOT_NAME: str = "Quán Bánh Canh Gà Hàng Gòn"

# Default Speed Limits (Vietnamese Traffic Regulation Standards)
SPEED_LIMITS_KPH: Dict[str, float] = {
    "motorway": 80.0,
    "trunk": 70.0,
    "primary": 60.0,
    "primary_link": 50.0,
    "secondary": 40.0,
    "secondary_link": 35.0,
    "tertiary": 35.0,
    "tertiary_link": 30.0,
    "residential": 30.0,
    "unclassified": 30.0,
    "living_street": 20.0,
    "service": 20.0,
    "track": 20.0,
}
DEFAULT_SPEED_KPH: float = 30.0

EARTH_RADIUS_METERS: float = 6371000.0


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance between two GPS coordinates in meters."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_METERS * c


def generate_deterministic_hanggon_graph() -> nx.MultiDiGraph:
    """Constructs a deterministic synthetic road graph of Hàng Gòn (64 nodes).

    Includes:
    - Depot: Quán Bánh Canh Gà Hàng Gòn at (10.9212, 107.2401)
    - QL56 Corridor (15 nodes North-South, primary 60 km/h)
    - Eastern Branch Network (24 nodes, secondary/tertiary/residential)
    - Western Branch Network (24 nodes, secondary/tertiary/residential)
    - Cross-connecting bypasses allowing congestion circumvention
    Total nodes: 1 + 15 + 24 + 24 = 64 nodes.
    """
    G = nx.MultiDiGraph()
    G.graph["name"] = "HangGon_Synthetic_Realistic_64"
    G.graph["crs"] = "EPSG:4326"

    nodes_data: Dict[str, Dict[str, Any]] = {}
    edges_data: List[Tuple[str, str, Dict[str, Any]]] = []

    # 1. Depot Node
    nodes_data[DEPOT_NODE_ID] = {
        "y": DEPOT_LAT,
        "x": DEPOT_LON,
        "name": DEPOT_NAME,
        "is_depot": True,
    }

    # 2. QL56 Spinal Corridor (15 nodes spanning South to North: 10.9000 to 10.9420)
    ql56_nodes: List[str] = []
    base_lat = 10.9000
    base_lon = 107.2370
    for i in range(15):
        node_id = f"ql56_{i:02d}"
        ql56_nodes.append(node_id)
        # Curvature along QL56
        lat = round(base_lat + i * 0.0030, 4)
        lon = round(base_lon + (i * 0.0005) + (0.0002 if i % 2 == 0 else -0.0002), 4)
        nodes_data[node_id] = {
            "y": lat,
            "x": lon,
            "name": f"QL56 Km{i+1} Hàng Gòn",
            "is_depot": False,
        }

    # Connect QL56 nodes sequentially (bi-directional)
    for i in range(len(ql56_nodes) - 1):
        u, v = ql56_nodes[i], ql56_nodes[i + 1]
        edges_data.append((u, v, {"highway": "primary", "name": "Quốc Lộ 56"}))
        edges_data.append((v, u, {"highway": "primary", "name": "Quốc Lộ 56"}))

    # Connect Depot to QL56 at node ql56_07 (lat ~ 10.9210)
    depot_anchor = "ql56_07"
    edges_data.append((DEPOT_NODE_ID, depot_anchor, {"highway": "residential", "name": "Đường vào Quán"}))
    edges_data.append((depot_anchor, DEPOT_NODE_ID, {"highway": "residential", "name": "Đường vào Quán"}))

    # 3. Eastern Sector (4 branches x 6 nodes each = 24 nodes)
    east_branches = [
        ("E1", "ql56_12", "Đường Suối Tre - Hàng Gòn", "secondary", 0.0008, 0.0025),
        ("E2", "ql56_09", "Đường Di Tích Cự Thạch", "tertiary", 0.0003, 0.0022),
        ("E3", "ql56_06", "Đường Ấp Hàng Gòn 1", "residential", -0.0002, 0.0020),
        ("E4", "ql56_02", "Đường Nông Trường Cao Su", "service", -0.0005, 0.0024),
    ]

    east_branch_nodes: Dict[str, List[str]] = {}
    for b_code, anchor, street_name, hw_type, lat_slope, lon_step in east_branches:
        branch_list: List[str] = []
        anchor_lat = nodes_data[anchor]["y"]
        anchor_lon = nodes_data[anchor]["x"]
        prev_node = anchor
        for j in range(6):
            node_id = f"{b_code}_{j:02d}"
            branch_list.append(node_id)
            n_lat = round(anchor_lat + (j + 1) * lat_slope, 4)
            n_lon = round(anchor_lon + (j + 1) * lon_step, 4)
            nodes_data[node_id] = {
                "y": n_lat,
                "x": n_lon,
                "name": f"{street_name} #{j+1}",
                "is_depot": False,
            }
            edges_data.append((prev_node, node_id, {"highway": hw_type, "name": street_name}))
            edges_data.append((node_id, prev_node, {"highway": hw_type, "name": street_name}))
            prev_node = node_id
        east_branch_nodes[b_code] = branch_list

    # North-South East Lateral Connectors (Creating Eastern Bypass around QL56)
    for col_idx in (2, 4):
        e_pairs = [("E1", "E2"), ("E2", "E3"), ("E3", "E4")]
        for b_up, b_down in e_pairs:
            u_node = east_branch_nodes[b_up][col_idx]
            v_node = east_branch_nodes[b_down][col_idx]
            edges_data.append((u_node, v_node, {"highway": "tertiary", "name": "Đường Liên Ấp Đông"}))
            edges_data.append((v_node, u_node, {"highway": "tertiary", "name": "Đường Liên Ấp Đông"}))

    # 4. Western Sector (3 branches x 8 nodes each = 24 nodes)
    west_branches = [
        ("W1", "ql56_11", "Đường UBND Xã & Trường Học", "tertiary", 0.0006, -0.0020),
        ("W2", "ql56_07", "Đường Ấp Đồi Rìu", "residential", 0.0001, -0.0022),
        ("W3", "ql56_03", "Đường Canh Tác Suối Râm", "service", -0.0004, -0.0021),
    ]

    west_branch_nodes: Dict[str, List[str]] = {}
    for b_code, anchor, street_name, hw_type, lat_slope, lon_step in west_branches:
        branch_list: List[str] = []
        anchor_lat = nodes_data[anchor]["y"]
        anchor_lon = nodes_data[anchor]["x"]
        prev_node = anchor
        for j in range(8):
            node_id = f"{b_code}_{j:02d}"
            branch_list.append(node_id)
            n_lat = round(anchor_lat + (j + 1) * lat_slope, 4)
            n_lon = round(anchor_lon + (j + 1) * lon_step, 4)
            nodes_data[node_id] = {
                "y": n_lat,
                "x": n_lon,
                "name": f"{street_name} #{j+1}",
                "is_depot": False,
            }
            edges_data.append((prev_node, node_id, {"highway": hw_type, "name": street_name}))
            edges_data.append((node_id, prev_node, {"highway": hw_type, "name": street_name}))
            prev_node = node_id
        west_branch_nodes[b_code] = branch_list

    # North-South West Lateral Connectors (Creating Western Bypass around QL56)
    for col_idx in (3, 6):
        w_pairs = [("W1", "W2"), ("W2", "W3")]
        for b_up, b_down in w_pairs:
            u_node = west_branch_nodes[b_up][col_idx]
            v_node = west_branch_nodes[b_down][col_idx]
            edges_data.append((u_node, v_node, {"highway": "tertiary", "name": "Đường Liên Ấp Tây"}))
            edges_data.append((v_node, u_node, {"highway": "tertiary", "name": "Đường Liên Ấp Tây"}))

    # Add all nodes to Graph
    for node_id, attrs in nodes_data.items():
        G.add_node(node_id, **attrs)

    # Add all edges to Graph with physical metric lengths and free flow times
    for u, v, attr in edges_data:
        lat1, lon1 = G.nodes[u]["y"], G.nodes[u]["x"]
        lat2, lon2 = G.nodes[v]["y"], G.nodes[v]["x"]
        length = round(haversine_distance_meters(lat1, lon1, lat2, lon2), 2)
        length = max(length, 10.0)

        hw_type = attr.get("highway", "residential")
        speed_kph = SPEED_LIMITS_KPH.get(hw_type, DEFAULT_SPEED_KPH)
        speed_mps = (speed_kph * 1000.0) / 3600.0
        free_flow_time = round(length / speed_mps, 2)

        edge_attrs = {
            "length": float(length),
            "speed_kph": float(speed_kph),
            "free_flow_time": float(free_flow_time),
            "highway": hw_type,
            "name": attr.get("name", "Đường giao thông"),
            "oneway": False,
        }
        G.add_edge(u, v, **edge_attrs)

    return G


def _sanitize_graph_attributes(G: nx.MultiDiGraph) -> None:
    """Ensures length, speed_kph, free_flow_time, and coordinates are typed as floats."""
    for n, data in G.nodes(data=True):
        if "y" in data:
            data["y"] = float(data["y"])
        if "x" in data:
            data["x"] = float(data["x"])
        if "lat" in data and "y" not in data:
            data["y"] = float(data["lat"])
        if "lon" in data and "x" not in data:
            data["x"] = float(data["lon"])

    for u, v, k, data in G.edges(keys=True, data=True):
        data["length"] = float(data.get("length", 100.0))
        hw = data.get("highway", "residential")
        if isinstance(hw, list):
            hw = hw[0]
        data["speed_kph"] = float(data.get("speed_kph", SPEED_LIMITS_KPH.get(hw, DEFAULT_SPEED_KPH)))
        speed_mps = (data["speed_kph"] * 1000.0) / 3600.0
        data["free_flow_time"] = float(data.get("free_flow_time", data["length"] / speed_mps))


def _annotate_osm_graph_attributes(G: nx.MultiDiGraph) -> None:
    """Annotates an OSMnx-extracted graph with speed limits and baseline travel times."""
    for u, v, k, data in G.edges(keys=True, data=True):
        hw = data.get("highway", "residential")
        if isinstance(hw, list):
            hw = hw[0]
        speed = SPEED_LIMITS_KPH.get(str(hw), DEFAULT_SPEED_KPH)
        data["speed_kph"] = float(speed)
        length = float(data.get("length", 50.0))
        speed_mps = (speed * 1000.0) / 3600.0
        data["free_flow_time"] = float(length / speed_mps)


def load_or_generate_hanggon_graph(
    graph_path: str = "data/hanggon_graph.graphml",
    force_download: bool = False,
    force_synthetic: bool = False,
) -> nx.MultiDiGraph:
    """Loads Hàng Gòn graph from disk, downloads via OSMnx, or generates synthetic fallback."""
    target_file = Path(graph_path)

    if force_synthetic:
        logger.info("Generating deterministic synthetic fallback graph (64 nodes)...")
        G = generate_deterministic_hanggon_graph()
        target_file.parent.mkdir(parents=True, exist_ok=True)
        nx.write_graphml(G, str(target_file))
        return G

    # Try loading existing file
    if target_file.is_file() and not force_download:
        try:
            G_raw = nx.read_graphml(str(target_file))
            if not isinstance(G_raw, nx.MultiDiGraph):
                G = nx.MultiDiGraph(G_raw)
            else:
                G = G_raw

            if G.number_of_nodes() < 10:
                logger.warning(
                    "Loaded graphml contains only %d nodes (<10). Regenerating realistic 64-node graph...",
                    G.number_of_nodes(),
                )
                G = generate_deterministic_hanggon_graph()
                nx.write_graphml(G, str(target_file))
            else:
                _sanitize_graph_attributes(G)
            return G
        except Exception as e:
            logger.warning("Failed to parse existing graphml file (%s): %s. Regenerating...", graph_path, e)

    # Attempt online download via OSMnx if requested
    if force_download:
        try:
            import osmnx as ox  # type: ignore
            logger.info("Attempting OSMnx road download for Hàng Gòn bbox...")
            G_ox = ox.graph_from_bbox(
                north=10.95, south=10.90, east=107.27, west=107.21,
                network_type="drive", simplify=True
            )
            G_ox = ox.utils_graph.get_largest_component(G_ox, strongly=True)
            _annotate_osm_graph_attributes(G_ox)
            target_file.parent.mkdir(parents=True, exist_ok=True)
            ox.save_graphml(G_ox, str(target_file))
            return G_ox
        except Exception as e:
            logger.warning("OSMnx download failed or offline (%s). Falling back to synthetic graph.", e)

    # Deterministic fallback
    G = generate_deterministic_hanggon_graph()
    target_file.parent.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(G, str(target_file))
    return G


def export_geojson_files(
    G: nx.MultiDiGraph,
    roads_path: str = "data/hanggon_center_roads.geojson",
    buildings_path: str = "data/hanggon_buildings.geojson",
) -> Tuple[str, str]:
    """Exports road geometries and synthetic building footprints to GeoJSON format."""
    # 1. Road GeoJSON
    features = []
    seen_edges = set()

    for u, v, k, data in G.edges(keys=True, data=True):
        edge_key = tuple(sorted([str(u), str(v)]))
        if edge_key in seen_edges:
            continue
        seen_edges.add(edge_key)

        u_lat = float(G.nodes[u]["y"])
        u_lon = float(G.nodes[u]["x"])
        v_lat = float(G.nodes[v]["y"])
        v_lon = float(G.nodes[v]["x"])

        feature = {
            "type": "Feature",
            "properties": {
                "id": f"way_{u}_{v}",
                "name": data.get("name", "Đường giao thông"),
                "highway": data.get("highway", "residential"),
                "speed_kph": float(data.get("speed_kph", 30.0)),
                "length_m": float(data.get("length", 100.0)),
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [u_lon, u_lat],
                    [v_lon, v_lat],
                ],
            },
        }
        features.append(feature)

    roads_fc = {
        "type": "FeatureCollection",
        "name": "hanggon_center_roads",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": features,
    }

    r_path = Path(roads_path)
    r_path.parent.mkdir(parents=True, exist_ok=True)
    with open(r_path, "w", encoding="utf-8") as f:
        json.dump(roads_fc, f, indent=2, ensure_ascii=False)

    # 2. Buildings GeoJSON
    building_features = []
    # Depot Building
    depot_bldg = {
        "type": "Feature",
        "properties": {
            "id": "bldg_depot",
            "name": DEPOT_NAME,
            "building": "commercial",
            "height": 6.5,
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [DEPOT_LON - 0.0001, DEPOT_LAT - 0.0001],
                    [DEPOT_LON + 0.0001, DEPOT_LAT - 0.0001],
                    [DEPOT_LON + 0.0001, DEPOT_LAT + 0.0001],
                    [DEPOT_LON - 0.0001, DEPOT_LAT + 0.0001],
                    [DEPOT_LON - 0.0001, DEPOT_LAT - 0.0001],
                ]
            ],
        },
    }
    building_features.append(depot_bldg)

    # Key landmark buildings at significant nodes
    landmarks = [
        ("ql56_07", "UBND Xã Hàng Gòn", "civic", 9.0, 0.00015),
        ("ql56_11", "Trường THCS Hàng Gòn", "school", 8.0, 0.0002),
        ("E2_02", "Khu Di Tích Mộ Cự Thạch", "historic", 4.5, 0.00025),
        ("E3_02", "Chợ Hàng Gòn", "commercial", 7.0, 0.0002),
        ("E4_03", "Trạm Y Tế Xã Hàng Gòn", "hospital", 6.0, 0.00015),
        ("W1_04", "Bưu Điện Văn Hóa Xã", "civic", 5.5, 0.00015),
        ("W2_04", "Nhà Văn Hóa Ấp Đồi Rìu", "civic", 5.0, 0.00015),
        ("ql56_03", "Cây Xăng QL56 Hàng Gòn", "commercial", 5.5, 0.0002),
    ]

    for node_id, b_name, b_type, b_height, size in landmarks:
        if node_id in G.nodes:
            n_lat = float(G.nodes[node_id]["y"])
            n_lon = float(G.nodes[node_id]["x"])
            b_feat = {
                "type": "Feature",
                "properties": {
                    "id": f"bldg_{node_id}",
                    "name": b_name,
                    "building": b_type,
                    "height": float(b_height),
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [round(n_lon - size, 6), round(n_lat - size, 6)],
                            [round(n_lon + size, 6), round(n_lat - size, 6)],
                            [round(n_lon + size, 6), round(n_lat + size, 6)],
                            [round(n_lon - size, 6), round(n_lat + size, 6)],
                            [round(n_lon - size, 6), round(n_lat - size, 6)],
                        ]
                    ],
                },
            }
            building_features.append(b_feat)

    buildings_fc = {
        "type": "FeatureCollection",
        "name": "hanggon_buildings",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": building_features,
    }

    b_path = Path(buildings_path)
    b_path.parent.mkdir(parents=True, exist_ok=True)
    with open(b_path, "w", encoding="utf-8") as f:
        json.dump(buildings_fc, f, indent=2, ensure_ascii=False)

    return str(r_path), str(b_path)


def get_nearest_node(G: nx.Graph, lat: float, lon: float) -> Any:
    """Finds the closest node in G to the given latitude and longitude."""
    best_node = None
    min_dist = float("inf")
    for n, data in G.nodes(data=True):
        n_lat = float(data.get("y", data.get("lat", 0.0)))
        n_lon = float(data.get("x", data.get("lon", 0.0)))
        d = haversine_distance_meters(lat, lon, n_lat, n_lon)
        if d < min_dist:
            min_dist = d
            best_node = n
    return best_node
