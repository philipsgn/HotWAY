"""
HotWAY Directed Road Network Builder v5.0 — Multi-Region OSMnx Edition.

Supports two modes:
1. "legacy"  — Hand-crafted Bình Thạnh graph (38 nodes, backward compat)
2. "osmnx"   — Real road network from OpenStreetMap via OSMnx

Follows D4 discipline:
- Strictly directed graph (MultiDiGraph) preserving oneway directions
- Checks Strongly Connected Component (SCC) and preserves the largest SCC
- Calculates accurate edge lengths and travel times
- Saves to GraphML, pickle cache, and GeoJSON for MapLibre rendering
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import pickle
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx
import yaml

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("build_graph")

EARTH_RADIUS_METERS: float = 6371000.0


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance in meters between two WGS84 GPS coordinates."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    return EARTH_RADIUS_METERS * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def load_site_config(config_path: Path | str = "config/site.yaml") -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ===========================================================================
#  MODE 1: OSMnx — Real Road Network from OpenStreetMap
# ===========================================================================

def build_osmnx_graph(region_config: Dict[str, Any]) -> nx.MultiDiGraph:
    """
    Downloads and builds a real directed road graph using OSMnx.
    
    Supports two download modes:
    - place_name: Downloads by city/district name
    - radius_km: Downloads by point + radius
    """
    try:
        import osmnx as ox
    except ImportError:
        logger.error("OSMnx is not installed. Run: pip install osmnx")
        raise

    network_type = region_config.get("network_type", "drive")
    
    if "place_name" in region_config:
        place = region_config["place_name"]
        logger.info(f"Downloading OSMnx graph for place: {place} (type: {network_type})")
        G = ox.graph_from_place(place, network_type=network_type)
    elif "radius_km" in region_config:
        depot = region_config["depot"]
        radius_m = region_config["radius_km"] * 1000
        logger.info(f"Downloading OSMnx graph from ({depot[0]}, {depot[1]}), radius={radius_m}m")
        G = ox.graph_from_point(tuple(depot), dist=radius_m, network_type=network_type)
    else:
        raise ValueError("Region config must have either 'place_name' or 'radius_km'")

    logger.info(f"Downloaded raw graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    # Ensure edge lengths exist (some OSMnx versions don't always have them)
    if not all("length" in d for _, _, d in G.edges(data=True)):
        logger.info("Adding missing edge lengths...")
        G = ox.distance.add_edge_lengths(G)

    # Standardize edge geometries to list of [lat, lon]
    logger.info("Normalizing edge geometries to list of [lat, lon]...")
    for u, v, k, data in G.edges(keys=True, data=True):
        geom = data.get("geometry")
        if hasattr(geom, "coords"):
            # OSMnx shapely LineString coords are (lon, lat) -> convert to [lat, lon]
            data["geometry"] = [[float(pt[1]), float(pt[0])] for pt in geom.coords]
        elif isinstance(geom, list) and geom:
            pass
        else:
            u_node = G.nodes[u]
            v_node = G.nodes[v]
            data["geometry"] = [
                [float(u_node.get("y", 0.0)), float(u_node.get("x", 0.0))],
                [float(v_node.get("y", 0.0)), float(v_node.get("x", 0.0))],
            ]

    # Add travel time based on speed limits or defaults
    _add_travel_times(G)

    return G


def _add_travel_times(G: nx.MultiDiGraph, default_speed_kph: float = 30.0):
    """
    Adds 'free_flow_time' (seconds) to each edge based on speed limit or default.
    Speed hierarchy: maxspeed tag > highway type default > global default.
    """
    highway_speeds = {
        "motorway": 80.0,
        "motorway_link": 60.0,
        "trunk": 60.0,
        "trunk_link": 50.0,
        "primary": 50.0,
        "primary_link": 40.0,
        "secondary": 40.0,
        "secondary_link": 35.0,
        "tertiary": 35.0,
        "tertiary_link": 30.0,
        "residential": 25.0,
        "living_street": 20.0,
        "service": 20.0,
        "unclassified": 30.0,
    }

    for u, v, k, data in G.edges(keys=True, data=True):
        length_m = data.get("length", 0.0)
        
        # Try maxspeed tag first
        speed_kph = default_speed_kph
        maxspeed = data.get("maxspeed")
        if maxspeed:
            if isinstance(maxspeed, list):
                maxspeed = maxspeed[0]
            try:
                speed_kph = float(str(maxspeed).replace("km/h", "").strip())
            except (ValueError, TypeError):
                pass
        else:
            # Fallback to highway type
            highway = data.get("highway", "unclassified")
            if isinstance(highway, list):
                highway = highway[0]
            speed_kph = highway_speeds.get(highway, default_speed_kph)

        data["speed_kph"] = speed_kph
        speed_mps = (speed_kph * 1000.0) / 3600.0
        data["free_flow_time"] = length_m / max(speed_mps, 0.1)


# ===========================================================================
#  MODE 2: Legacy — Hand-crafted Bình Thạnh graph (backward compatibility)
# ===========================================================================

def build_legacy_binhthanh_graph(config: Dict[str, Any]) -> nx.MultiDiGraph:
    """
    Original hand-crafted Bình Thạnh graph with 38 nodes.
    Kept for backward compatibility and demo purposes.
    """
    site = config["site"]
    depot_lat = site["depot"]["lat"]
    depot_lon = site["depot"]["lon"]
    depot_name = site["depot"]["name"]
    depot_id = "depot_0"

    G = nx.MultiDiGraph()
    G.graph["name"] = site["name"]
    G.graph["crs"] = "EPSG:4326"
    G.graph["depot_id"] = depot_id

    nodes: Dict[str, Dict[str, Any]] = {
        depot_id: {
            "y": depot_lat,
            "x": depot_lon,
            "name": depot_name,
            "is_depot": True,
        }
    }

    road_intersections = [
        ("dbp_00", 10.7930, 106.7020, "Ngã tư Điện Biên Phủ - Đinh Tiên Hoàng"),
        ("dbp_01", 10.7950, 106.7040, "Cầu Điện Biên Phủ / Kênh Nhiêu Lộc"),
        ("dbp_02", 10.7970, 106.7065, "Điện Biên Phủ - Nguyễn Cửu Vân"),
        ("dbp_03", 10.7985, 106.7085, "Cầu Văn Thánh Tây"),
        ("dbp_04", 10.8000, 106.7100, "Điện Biên Phủ - Phan Chu Trinh"),
        ("dbp_05", 10.8018, 106.7118, "Vòng Xoay Hàng Xanh"),
        ("dbp_06", 10.8015, 106.7135, "Điện Biên Phủ - Cổng ĐH HUTECH"),
        ("dbp_07", 10.8010, 106.7150, "Mặt tiền 490 Điện Biên Phủ"),
        ("dbp_08", 10.8000, 106.7165, "Giao lộ D1"),
        ("dbp_09", 10.7995, 106.7180, "Pearl Plaza / Giao lộ D2"),
        ("dbp_10", 10.7980, 106.7205, "Cầu Văn Thánh Đông"),
        ("dbp_11", 10.7965, 106.7230, "Chân Cầu Sài Gòn"),
        ("xvnt_00", 10.7900, 106.7040, "Cầu Thị Nghè 1"),
        ("xvnt_01", 10.7940, 106.7065, "Chợ Thị Nghè"),
        ("xvnt_02", 10.7980, 106.7090, "Xô Viết Nghệ Tĩnh - Huỳnh Mẫn Đạt"),
        ("xvnt_03", 10.8050, 106.7125, "Xô Viết Nghệ Tĩnh - Bạch Đằng"),
        ("xvnt_04", 10.8080, 106.7130, "Ngã Ba Đài Liệt Sĩ"),
        ("xvnt_05", 10.8120, 106.7135, "Bến Xe Miền Đông Cũ"),
        ("xvnt_06", 10.8160, 106.7140, "Chân Cầu Bình Triệu 1"),
        ("bd_01", 10.8035, 106.7060, "Bạch Đằng - Huỳnh Đình Hai"),
        ("bd_02", 10.8020, 106.7020, "Bạch Đằng - Phan Chu Trinh"),
        ("bd_03", 10.8010, 106.6980, "Chợ Bà Chiểu"),
        ("pdl_01", 10.8030, 106.6950, "Bệnh Viện Nhân Dân Gia Định"),
        ("pdl_02", 10.8050, 106.6920, "Phan Đăng Lưu - Nơ Trang Long"),
        ("d1_01", 10.8020, 106.7170, "Nguyễn Văn Thương (D1)"),
        ("d2_01", 10.8030, 106.7175, "Nguyễn Gia Trí (D2) - ĐH GTVT"),
        ("d2_02", 10.8060, 106.7170, "Nguyễn Gia Trí (D2) - Khu Ẩm Thực"),
        ("uvk_01", 10.8080, 106.7165, "Ngã Ba D2 - Ung Văn Khiêm"),
        ("uvk_02", 10.8085, 106.7145, "Ung Văn Khiêm - XVNT"),
        ("uvk_03", 10.8070, 106.7210, "Ung Văn Khiêm - Cầu Sài Gòn"),
        ("nhc_01", 10.7930, 106.7160, "Nguyễn Hữu Cảnh - Cầu Thủ Thiêm 1"),
        ("nhc_02", 10.7950, 106.7190, "Nguyễn Hữu Cảnh - Vinhomes Tây"),
        ("vh_01", 10.7955, 106.7208, "Đại Lộ Vinhomes Central Park"),
        ("vh_02", 10.7950, 106.7215, "Landmark 81"),
        ("vh_03", 10.7935, 106.7225, "Công Viên Vinhomes Ven Sông"),
        ("link_01", 10.7960, 106.7120, "Nguyễn Cửu Vân - Nguyễn Hữu Cảnh"),
        ("link_02", 10.8005, 106.7195, "Đường Ven Sông Sài Gòn"),
    ]

    for nid, lat, lon, name in road_intersections:
        nodes[nid] = {"y": lat, "x": lon, "name": name, "is_depot": False}

    for nid, data in nodes.items():
        G.add_node(nid, **data)

    raw_edges: List[Tuple[str, str, str, float, bool]] = [
        (depot_id, "dbp_07", "Lối vào Hàng Gòn Quán", 30.0, False),
        ("dbp_00", "dbp_01", "Đường Điện Biên Phủ", 60.0, False),
        ("dbp_01", "dbp_02", "Đường Điện Biên Phủ", 60.0, False),
        ("dbp_02", "dbp_03", "Đường Điện Biên Phủ", 60.0, False),
        ("dbp_03", "dbp_04", "Đường Điện Biên Phủ", 60.0, False),
        ("dbp_04", "dbp_05", "Đường Điện Biên Phủ", 50.0, False),
        ("dbp_05", "dbp_06", "Đường Điện Biên Phủ", 50.0, False),
        ("dbp_06", "dbp_07", "Đường Điện Biên Phủ", 60.0, False),
        ("dbp_07", "dbp_08", "Đường Điện Biên Phủ", 60.0, False),
        ("dbp_08", "dbp_09", "Đường Điện Biên Phủ", 60.0, False),
        ("dbp_09", "dbp_10", "Đường Điện Biên Phủ", 60.0, False),
        ("dbp_10", "dbp_11", "Đường Điện Biên Phủ", 60.0, False),
        ("xvnt_00", "xvnt_01", "Đường Xô Viết Nghệ Tĩnh", 40.0, False),
        ("xvnt_01", "xvnt_02", "Đường Xô Viết Nghệ Tĩnh", 40.0, False),
        ("xvnt_02", "dbp_05", "Đường Xô Viết Nghệ Tĩnh", 35.0, False),
        ("dbp_05", "xvnt_03", "Đường Xô Viết Nghệ Tĩnh", 35.0, False),
        ("xvnt_03", "xvnt_04", "Đường Xô Viết Nghệ Tĩnh", 40.0, False),
        ("xvnt_04", "xvnt_05", "Đường Xô Viết Nghệ Tĩnh", 40.0, False),
        ("xvnt_05", "xvnt_06", "Đường Xô Viết Nghệ Tĩnh", 50.0, False),
        ("xvnt_03", "bd_01", "Đường Bạch Đằng", 40.0, False),
        ("bd_01", "bd_02", "Đường Bạch Đằng", 40.0, False),
        ("bd_02", "bd_03", "Đường Bạch Đằng", 40.0, False),
        ("bd_03", "pdl_01", "Đường Phan Đăng Lưu", 45.0, False),
        ("pdl_01", "pdl_02", "Đường Phan Đăng Lưu", 45.0, False),
        ("dbp_08", "d1_01", "Đường D1", 35.0, False),
        ("d1_01", "d2_01", "Đường Nội Khu D1-D2", 30.0, False),
        ("dbp_09", "d2_01", "Đường D2", 35.0, False),
        ("d2_01", "d2_02", "Đường D2", 35.0, False),
        ("d2_02", "uvk_01", "Đường D2", 35.0, False),
        ("uvk_01", "uvk_02", "Đường Ung Văn Khiêm", 40.0, False),
        ("uvk_02", "xvnt_04", "Đường Ung Văn Khiêm", 40.0, False),
        ("uvk_01", "uvk_03", "Đường Ung Văn Khiêm", 40.0, False),
        ("uvk_03", "dbp_11", "Đường Nhánh Cầu Sài Gòn", 35.0, False),
        ("dbp_10", "vh_01", "Lối vào Vinhomes", 30.0, False),
        ("vh_01", "vh_02", "Đại Lộ Vinhomes", 25.0, False),
        ("vh_02", "vh_03", "Đường Ven Công Viên Sông", 25.0, False),
        ("vh_01", "nhc_02", "Đường Kết Nối NHC", 35.0, False),
        ("nhc_02", "nhc_01", "Đường Nguyễn Hữu Cảnh", 50.0, False),
        ("nhc_01", "link_01", "Đường Nhánh Cầu Thủ Thiêm", 40.0, False),
        ("link_01", "dbp_02", "Đường Nguyễn Cửu Vân", 35.0, False),
        ("dbp_10", "link_02", "Đường Ven Kênh", 30.0, False),
        ("link_02", "vh_01", "Đường Nối Kênh Văn Thánh", 30.0, False),
    ]

    for u, v, name, speed, oneway in raw_edges:
        u_data = nodes[u]
        v_data = nodes[v]
        length_m = haversine(u_data["y"], u_data["x"], v_data["y"], v_data["x"])
        speed_mps = (speed * 1000.0) / 3600.0
        free_flow_sec = length_m / max(speed_mps, 0.1)
        geom = [[u_data["y"], u_data["x"]], [v_data["y"], v_data["x"]]]

        G.add_edge(u, v, name=name, length=length_m, speed_kph=speed,
                   free_flow_time=free_flow_sec, oneway=oneway, geometry=geom)
        if not oneway:
            G.add_edge(v, u, name=name, length=length_m, speed_kph=speed,
                       free_flow_time=free_flow_sec, oneway=oneway,
                       geometry=[[v_data["y"], v_data["x"]], [u_data["y"], u_data["x"]]])

    return G


# ===========================================================================
#  Shared Utilities
# ===========================================================================

def enforce_strongly_connected(G: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """Verifies and extracts the largest Strongly Connected Component (SCC)."""
    total_nodes = G.number_of_nodes()
    
    if nx.is_strongly_connected(G):
        logger.info(f"Graph is already strongly connected (SCC): {total_nodes} nodes, {G.number_of_edges()} edges.")
        return G

    sccs = list(nx.strongly_connected_components(G))
    largest_scc = max(sccs, key=len)
    scc_coverage = len(largest_scc) / total_nodes * 100 if total_nodes > 0 else 0
    
    logger.warning(f"Graph is NOT strongly connected. Found {len(sccs)} SCCs.")
    logger.info(f"Largest SCC: {len(largest_scc)} / {total_nodes} nodes ({scc_coverage:.1f}% coverage)")
    
    subG = G.subgraph(largest_scc).copy()
    
    # Verify SCC is truly strongly connected
    assert nx.is_strongly_connected(subG), "Extracted SCC is not strongly connected!"
    
    return subG


def export_graph_artifacts(
    G: nx.MultiDiGraph,
    output_dir: Path | str = "data",
    prefix: str = "binhthanh",
    export_graphml: bool = True,
):
    """Exports graph to pickle, GeoJSON, and optionally GraphML."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # 1. Export Fast Pickle Cache
    pickle_path = out / f"{prefix}_graph.pickle"
    with open(pickle_path, "wb") as f:
        pickle.dump(G, f)
    logger.info(f"Exported Pickle Cache: {pickle_path} ({pickle_path.stat().st_size / 1024:.1f} KB)")

    # 2. Export GraphML (optional — can be very large for city graphs)
    if export_graphml:
        graphml_path = out / f"{prefix}_graph.graphml"
        G_export = G.copy()
        for _, _, _, data in G_export.edges(keys=True, data=True):
            # Convert list attributes to JSON strings for XML compliance
            for key, val in list(data.items()):
                if isinstance(val, (list, dict)):
                    data[key] = json.dumps(val)
        try:
            nx.write_graphml(G_export, graphml_path)
            logger.info(f"Exported GraphML: {graphml_path}")
        except Exception as e:
            logger.warning(f"GraphML export failed (graph too large?): {e}")

    # 3. Export GeoJSON Roads for MapLibre
    geojson_features = []
    for u, v, k, data in G.edges(keys=True, data=True):
        u_node = G.nodes[u]
        v_node = G.nodes[v]
        
        # Get geometry: data["geometry"] is already normalized to list of [lat, lon]
        geom_latlon = data.get("geometry")
        if geom_latlon and isinstance(geom_latlon, list) and len(geom_latlon) > 0:
            # Convert [lat, lon] -> GeoJSON standard [lon, lat]
            coords = [[float(pt[1]), float(pt[0])] for pt in geom_latlon]
        else:
            coords = [
                [float(u_node.get("x", 0.0)), float(u_node.get("y", 0.0))],
                [float(v_node.get("x", 0.0)), float(v_node.get("y", 0.0))],
            ]

        highway_type = data.get("highway", "unclassified")
        if isinstance(highway_type, list):
            highway_type = highway_type[0]

        geojson_features.append({
            "type": "Feature",
            "properties": {
                "id": f"{u}_{v}_{k}",
                "name": data.get("name", "Đường đô thị"),
                "highway": highway_type,
                "speed_kph": data.get("speed_kph", 30.0),
                "length_m": round(data.get("length", 0.0), 1),
                "oneway": data.get("oneway", False),
            },
            "geometry": {
                "type": "LineString",
                "coordinates": coords,
            },
        })

    geojson_path = out / f"{prefix}_roads.geojson"
    with open(geojson_path, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": geojson_features}, f, ensure_ascii=False)
    logger.info(f"Exported Roads GeoJSON: {geojson_path} ({len(geojson_features)} features)")

    # 4. Export Buildings/Points of Interest GeoJSON (nodes with special attributes)
    poi_features = []
    for node_id, data in G.nodes(data=True):
        if data.get("is_depot"):
            poi_features.append({
                "type": "Feature",
                "properties": {
                    "id": str(node_id),
                    "name": data.get("name", ""),
                    "type": "depot",
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [data.get("x", 0), data.get("y", 0)],
                },
            })
    
    if poi_features:
        buildings_path = out / f"{prefix}_buildings.geojson"
        with open(buildings_path, "w", encoding="utf-8") as f:
            json.dump({"type": "FeatureCollection", "features": poi_features}, f, ensure_ascii=False)
        logger.info(f"Exported POI GeoJSON: {buildings_path}")


def print_graph_stats(G: nx.MultiDiGraph, region_name: str):
    """Prints comprehensive graph statistics."""
    print(f"\n{'='*60}")
    print(f"  [STATS] Graph Statistics: {region_name}")
    print(f"{'='*60}")
    print(f"  Nodes:          {G.number_of_nodes():,}")
    print(f"  Edges:          {G.number_of_edges():,}")
    
    # Edge length stats
    lengths = [d.get("length", 0) for _, _, d in G.edges(data=True)]
    if lengths:
        print(f"  Total road km:  {sum(lengths)/1000:.1f}")
        print(f"  Avg edge len:   {sum(lengths)/len(lengths):.1f} m")
        print(f"  Max edge len:   {max(lengths):.1f} m")
        print(f"  Min edge len:   {min(lengths):.1f} m")
    
    # SCC check
    is_scc = nx.is_strongly_connected(G)
    print(f"  Strongly Conn:  {'YES' if is_scc else 'NO'}")
    
    if not is_scc:
        sccs = list(nx.strongly_connected_components(G))
        largest = max(len(s) for s in sccs)
        print(f"  Num SCCs:       {len(sccs)}")
        print(f"  Largest SCC:    {largest} nodes ({largest/G.number_of_nodes()*100:.1f}%)")
    
    print(f"{'='*60}\n")


# ===========================================================================
#  Main Entry Point
# ===========================================================================

def build_region(region_name: str, config: Dict[str, Any]) -> nx.MultiDiGraph:
    """Builds a graph for the specified region."""
    regions = config.get("regions", {})
    
    if region_name not in regions:
        available = list(regions.keys())
        raise ValueError(f"Region '{region_name}' not found. Available: {available}")
    
    region_cfg = regions[region_name]
    mode = region_cfg.get("mode", "legacy")
    
    if mode == "osmnx":
        G = build_osmnx_graph(region_cfg)
    elif mode == "legacy":
        G = build_legacy_binhthanh_graph(config)
    else:
        raise ValueError(f"Unknown graph mode: {mode}")
    
    # Enforce SCC
    G = enforce_strongly_connected(G)
    print_graph_stats(G, region_name)
    
    # Determine prefix from graph_file or region name
    graph_file = region_cfg.get("graph_file", f"data/{region_name}_graph.pickle")
    prefix = Path(graph_file).stem.replace("_graph", "")
    output_dir = str(Path(graph_file).parent)
    
    # Export artifacts
    export_graphml = region_cfg.get("graphml_file") is not None
    export_graph_artifacts(G, output_dir, prefix, export_graphml)
    
    return G


def main():
    parser = argparse.ArgumentParser(description="HotWAY Road Network Builder v5.0")
    parser.add_argument(
        "--region", type=str, default=None,
        help="Region to build (e.g., 'binhthanh', 'hcmc', 'hcmc_compact'). "
             "If not specified, uses default_region from config."
    )
    parser.add_argument(
        "--config", type=str, default="config/site.yaml",
        help="Path to site config YAML"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Build all regions defined in config"
    )
    args = parser.parse_args()

    config = load_site_config(args.config)
    logger.info(f"Loaded site config: {config['site']['name']}")

    if args.all:
        regions = list(config.get("regions", {}).keys())
        logger.info(f"Building all regions: {regions}")
        for r in regions:
            try:
                build_region(r, config)
                print(f"[SUCCESS] Built region '{r}'")
            except Exception as e:
                print(f"[FAILED] Region '{r}' - {e}")
    else:
        region = args.region or config.get("default_region", "binhthanh")
        G = build_region(region, config)
        print(f"[SUCCESS] Built '{region}' with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")


if __name__ == "__main__":
    main()
