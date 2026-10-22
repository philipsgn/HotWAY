"""
Road Matrix Service (Asymmetric Distance/Time & Route Geometry)
v5.0 — Multi-Region & KDTree Accelerated Edition

Follows Section 4.2 & 4.3 rules:
- Snaps GPS points to nearest graph nodes with <= 60m threshold using cKDTree in O(log N).
- Computes asymmetric cost matrix from directed shortest paths (single-source Dijkstra).
- Stores detailed leg geometries (list of [lat, lon]) along real road edges.
- Caches results by hash of snapped node IDs.
- Supports multi-region graphs (e.g. binhthanh, hcmc, hcmc_compact).
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx
import numpy as np
from scipy.spatial import cKDTree

from src.data.build_graph import haversine, load_site_config

logger = logging.getLogger("road_matrix")

# Multi-region graph and spatial index caches
_GRAPHS: Dict[str, nx.MultiDiGraph] = {}
_KDTREES: Dict[str, Tuple[cKDTree, List[Any], np.ndarray]] = {}
_MATRIX_CACHE: Dict[str, Dict[str, Any]] = {}


def get_road_graph(
    region: Optional[str] = None,
    graph_pickle_path: Optional[Path | str] = None,
    config_path: Path | str = "config/site.yaml",
) -> nx.MultiDiGraph:
    """
    Retrieves or loads the graph for a specified region or file path.
    If neither is given, loads default_region from site.yaml.
    """
    global _GRAPHS
    
    if graph_pickle_path is not None:
        key = str(graph_pickle_path)
        if key not in _GRAPHS:
            p = Path(graph_pickle_path)
            if not p.exists():
                raise FileNotFoundError(f"Graph cache not found at {p}. Run build_graph first.")
            with open(p, "rb") as f:
                _GRAPHS[key] = pickle.load(f)
        return _GRAPHS[key]

    config = load_site_config(config_path)
    if region is None:
        region = config.get("default_region", "hcmc_compact")

    if region in _GRAPHS:
        return _GRAPHS[region]

    regions_cfg = config.get("regions", {})
    if region not in regions_cfg:
        # Fallback to binhthanh if specified region not found
        region = "binhthanh"
    
    reg_cfg = regions_cfg.get(region, {})
    pickle_path = Path(reg_cfg.get("graph_file", f"data/{region}_graph.pickle"))
    
    if not pickle_path.exists():
        # Try legacy fallback
        legacy_path = Path("data/binhthanh_graph.pickle")
        if legacy_path.exists():
            logger.warning(f"Region graph {pickle_path} not found. Falling back to {legacy_path}")
            pickle_path = legacy_path
        else:
            raise FileNotFoundError(
                f"Graph file not found at {pickle_path}. Please run: python -m src.data.build_graph --region {region}"
            )

    logger.info(f"Loading road graph for region '{region}' from {pickle_path}...")
    with open(pickle_path, "rb") as f:
        graph = pickle.load(f)
    _GRAPHS[region] = graph
    return graph


def _get_or_build_kdtree(graph: nx.MultiDiGraph) -> Tuple[cKDTree, List[Any], np.ndarray]:
    """
    Builds or retrieves a cKDTree spatial index for fast nearest-neighbor snapping.
    Coordinates are in radians for spherical distance or Euclidean on projected/scaled lat-lon.
    For small/medium urban regions, equirectangular projection centered on depot gives mm precision:
        x = (lon - lon0) * cos(lat0) * R
        y = (lat - lat0) * R
    """
    graph_id = id(graph)
    key = str(graph_id)
    if key in _KDTREES:
        return _KDTREES[key]

    node_ids: List[Any] = []
    coords: List[Tuple[float, float]] = []

    for nid, data in graph.nodes(data=True):
        lat = data.get("y", data.get("lat", 0.0))
        lon = data.get("x", data.get("lon", 0.0))
        node_ids.append(nid)
        coords.append((lat, lon))

    coords_arr = np.array(coords, dtype=np.float64)  # [N, 2] with (lat, lon)
    
    # Use center latitude for equirectangular scaling
    lat0 = np.mean(coords_arr[:, 0]) if len(coords_arr) > 0 else 10.8
    cos_lat0 = math.cos(math.radians(lat0))
    r_earth = 6371000.0  # meters

    # Metric coordinates in meters
    metric_coords = np.zeros_like(coords_arr)
    metric_coords[:, 0] = coords_arr[:, 0] * (math.pi / 180.0) * r_earth
    metric_coords[:, 1] = coords_arr[:, 1] * (math.pi / 180.0) * r_earth * cos_lat0

    tree = cKDTree(metric_coords)
    _KDTREES[key] = (tree, node_ids, coords_arr)
    return _KDTREES[key]


def snap_coordinate_to_node(
    lat: float,
    lon: float,
    graph: Optional[nx.MultiDiGraph] = None,
    max_snap_meters: float = 60.0,
) -> Tuple[str, float, bool]:
    """
    Snaps a GPS point to the nearest drivable graph node in O(log N) using cKDTree.
    Returns (node_id, distance_meters, exceeds_threshold).
    """
    if graph is None:
        graph = get_road_graph()

    tree, node_ids, coords_arr = _get_or_build_kdtree(graph)
    
    # Query metric distance
    lat0 = np.mean(coords_arr[:, 0]) if len(coords_arr) > 0 else 10.8
    cos_lat0 = math.cos(math.radians(lat0))
    r_earth = 6371000.0

    qy = lat * (math.pi / 180.0) * r_earth
    qx = lon * (math.pi / 180.0) * r_earth * cos_lat0

    dist_meters, nearest_idx = tree.query([qy, qx])
    closest_node = node_ids[int(nearest_idx)]
    
    # Exact Haversine check
    node_lat, node_lon = coords_arr[nearest_idx]
    exact_dist = haversine(lat, lon, node_lat, node_lon)

    exceeds = exact_dist > max_snap_meters
    if exceeds:
        logger.warning(
            f"Point ({lat:.5f}, {lon:.5f}) snapped to {closest_node} with distance {exact_dist:.1f}m > threshold {max_snap_meters}m"
        )

    return str(closest_node), exact_dist, exceeds


def _extract_leg_geometry(
    graph: nx.MultiDiGraph,
    path: List[Any],
    src_pt: Dict[str, Any],
    dst_pt: Dict[str, Any],
) -> List[List[float]]:
    """Extracts continuous [lat, lon] coordinates along graph edges."""
    if len(path) <= 1:
        return [[src_pt["lat"], src_pt["lon"]]]

    full_geom: List[List[float]] = []

    for k in range(len(path) - 1):
        u, v = path[k], path[k + 1]
        edges = graph.get_edge_data(u, v)
        if not edges:
            continue
        # Pick best edge (lowest free_flow_time)
        edge_data = min(edges.values(), key=lambda e: e.get("free_flow_time", 999999.0))
        
        edge_geom = edge_data.get("geometry")
        if edge_geom and isinstance(edge_geom, list) and len(edge_geom) > 0:
            pts = edge_geom
        else:
            u_node = graph.nodes[u]
            v_node = graph.nodes[v]
            pts = [
                [float(u_node.get("y", u_node.get("lat", 0.0))), float(u_node.get("x", u_node.get("lon", 0.0)))],
                [float(v_node.get("y", v_node.get("lat", 0.0))), float(v_node.get("x", v_node.get("lon", 0.0)))],
            ]

        if not full_geom:
            full_geom.extend(pts)
        else:
            full_geom.extend(pts[1:])

    return full_geom


def compute_road_matrix(
    points: List[Dict[str, Any]],
    graph: Optional[nx.MultiDiGraph] = None,
    max_snap_meters: float = 60.0,
    region: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Computes asymmetric distance, duration, and leg geometry matrices for a list of points.
    points[0] must be the depot.
    points[1..n] are customer order stops.
    
    Uses single_source_dijkstra per point for O(n * (E + V log V)) complexity instead of O(n^2 * ...).
    """
    if graph is None:
        graph = get_road_graph(region=region)

    n = len(points)
    snapped_nodes: List[str] = []
    snap_warnings: List[Dict[str, Any]] = []

    # Fast KDTree snapping
    for idx, pt in enumerate(points):
        nid, snap_dist, exceeds = snap_coordinate_to_node(
            pt["lat"], pt["lon"], graph, max_snap_meters=max_snap_meters
        )
        snapped_nodes.append(nid)
        if exceeds:
            snap_warnings.append({
                "point_index": idx,
                "point_id": pt.get("id", f"p_{idx}"),
                "lat": pt["lat"],
                "lon": pt["lon"],
                "snapped_node": nid,
                "snap_dist_meters": round(snap_dist, 1),
            })

    # Cache key from ordered tuple of snapped nodes
    cache_key = hashlib.sha256(",".join(str(s) for s in snapped_nodes).encode("utf-8")).hexdigest()
    if cache_key in _MATRIX_CACHE:
        cached = _MATRIX_CACHE[cache_key]
        return {**cached, "snap_warnings": snap_warnings}

    dist_matrix = [[0.0] * n for _ in range(n)]
    time_matrix = [[0.0] * n for _ in range(n)]
    leg_geometries: List[List[List[List[float]]]] = [[[] for _ in range(n)] for _ in range(n)]

    # Cast to correct type in graph if nodes are ints or strings
    sample_node = next(iter(graph.nodes()))
    is_int_node = isinstance(sample_node, int)

    target_nodes = [int(s) if is_int_node else s for s in snapped_nodes]

    # Pre-calculate Dijkstra from each point i to all destinations in 1 pass
    for i in range(n):
        src_node = target_nodes[i]
        
        # Single-source Dijkstra for travel time
        try:
            times, paths = nx.single_source_dijkstra(
                graph, source=src_node, weight="free_flow_time"
            )
        except (nx.NodeNotFound, KeyError):
            times, paths = {}, {}

        for j in range(n):
            if i == j:
                dist_matrix[i][j] = 0.0
                time_matrix[i][j] = 0.0
                leg_geometries[i][j] = [[points[i]["lat"], points[i]["lon"]]]
                continue

            dst_node = target_nodes[j]
            if dst_node in paths:
                path = paths[dst_node]
                t_val = times[dst_node]
                
                # Compute total road distance along path
                path_dist = 0.0
                for k in range(len(path) - 1):
                    edges = graph.get_edge_data(path[k], path[k + 1])
                    if edges:
                        best_e = min(edges.values(), key=lambda e: e.get("free_flow_time", 999999.0))
                        path_dist += best_e.get("length", 0.0)

                dist_matrix[i][j] = round(path_dist, 1)
                time_matrix[i][j] = round(t_val, 1)
                leg_geometries[i][j] = _extract_leg_geometry(graph, path, points[i], points[j])
            else:
                # Disconnected or penalty fallback
                dist_matrix[i][j] = 999999.0
                time_matrix[i][j] = 999999.0
                leg_geometries[i][j] = [
                    [points[i]["lat"], points[i]["lon"]],
                    [points[j]["lat"], points[j]["lon"]],
                ]

    result = {
        "cache_key": cache_key,
        "n_points": n,
        "snapped_nodes": snapped_nodes,
        "dist_matrix": dist_matrix,
        "time_matrix": time_matrix,
        "leg_geometries": leg_geometries,
        "snap_warnings": snap_warnings,
    }

    _MATRIX_CACHE[cache_key] = result
    return result
