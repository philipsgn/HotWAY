"""
Address Generator and Distance Matrix Precomputer for HotWAY GĐ2.
Generates 400 fixed standard snapped addresses and 150 OOD addresses around Hang Gon Quan,
and precomputes asymmetric distance and travel time matrices using cKDTree and Dijkstra.
"""

from __future__ import annotations

import json
import math
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Any

import networkx as nx
import numpy as np
from scipy.spatial import cKDTree


def generate_address_pools(
    graph_pickle_path: str | Path = "data/hcmc_compact_graph.pickle",
    output_dir: str | Path = "data",
    depot_lat: float = 10.8012,
    depot_lon: float = 106.7145,
    n_standard: int = 400,
    n_ood: int = 150,
    standard_radius_km: float = 4.5,
    ood_min_radius_km: float = 5.0,
    ood_max_radius_km: float = 8.5,
    seed: int = 2026,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Generates standard and OOD address pools with precomputed distance/time matrices.
    """
    rng = np.random.default_rng(seed)
    with open(graph_pickle_path, "rb") as f:
        G: nx.MultiDiGraph = pickle.load(f)

    # Collect nodes with coordinates
    node_ids = []
    coords = []
    for n, d in G.nodes(data=True):
        lat = d.get("y", d.get("lat", 0.0))
        lon = d.get("x", d.get("lon", 0.0))
        node_ids.append(n)
        coords.append((lat, lon))

    coords_arr = np.array(coords, dtype=np.float64)
    # Distance in km from depot
    dists_km = np.sqrt(
        (coords_arr[:, 0] - depot_lat) ** 2 +
        ((coords_arr[:, 1] - depot_lon) * math.cos(math.radians(depot_lat))) ** 2
    ) * 111.0

    # Depot node index (closest node to depot coordinates)
    depot_idx = int(np.argmin(dists_km))
    depot_node = node_ids[depot_idx]

    # Find nodes with outgoing edges
    valid_mask = np.array([G.out_degree(n) > 0 and G.in_degree(n) > 0 for n in node_ids], dtype=bool)

    # Standard candidate indices
    std_cand_indices = np.where(valid_mask & (dists_km <= standard_radius_km) & (dists_km > 0.1))[0]
    # OOD candidate indices
    ood_cand_indices = np.where(valid_mask & (dists_km >= ood_min_radius_km) & (dists_km <= ood_max_radius_km))[0]

    chosen_std_indices = rng.choice(std_cand_indices, size=min(n_standard, len(std_cand_indices)), replace=False)
    chosen_ood_indices = rng.choice(ood_cand_indices, size=min(n_ood, len(ood_cand_indices)), replace=False)

    # Pool 1: Standard (Index 0 is depot, followed by customer addresses)
    std_node_ids = [depot_node] + [node_ids[i] for i in chosen_std_indices]
    std_coords = [{"id": 0, "node_id": depot_node, "lat": depot_lat, "lon": depot_lon, "name": "Hang Gon Quan - Depot"}]
    for idx, i in enumerate(chosen_std_indices, start=1):
        std_coords.append({
            "id": idx,
            "node_id": node_ids[i],
            "lat": float(coords_arr[i, 0]),
            "lon": float(coords_arr[i, 1]),
            "dist_depot_km": float(dists_km[i]),
        })

    # Pool 2: OOD (Index 0 is depot, followed by OOD customer addresses)
    ood_node_ids = [depot_node] + [node_ids[i] for i in chosen_ood_indices]
    ood_coords = [{"id": 0, "node_id": depot_node, "lat": depot_lat, "lon": depot_lon, "name": "Hang Gon Quan - Depot"}]
    for idx, i in enumerate(chosen_ood_indices, start=1):
        ood_coords.append({
            "id": idx,
            "node_id": node_ids[i],
            "lat": float(coords_arr[i, 0]),
            "lon": float(coords_arr[i, 1]),
            "dist_depot_km": float(dists_km[i]),
        })

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "address_pool_standard.json", "w", encoding="utf-8") as f:
        json.dump(std_coords, f, indent=2, ensure_ascii=False)

    with open(out_dir / "address_pool_ood.json", "w", encoding="utf-8") as f:
        json.dump(ood_coords, f, indent=2, ensure_ascii=False)

    print(f"Generated {len(std_coords)} standard addresses and {len(ood_coords)} OOD addresses.")

    # Precompute pairwise distance and time matrices on the road graph
    _precompute_matrix(G, std_node_ids, out_dir / "matrix_standard.npz")
    _precompute_matrix(G, ood_node_ids, out_dir / "matrix_ood.npz")

    return {"count": len(std_coords), "file": str(out_dir / "address_pool_standard.json")}, {
        "count": len(ood_coords),
        "file": str(out_dir / "address_pool_ood.json"),
    }


def _precompute_matrix(
    G: nx.MultiDiGraph,
    selected_nodes: List[Any],
    output_path: Path,
    speed_kmh: float = 25.0,
) -> None:
    """Computes pairwise shortest path distance (m) and travel time (min)."""
    n = len(selected_nodes)
    node_set = set(selected_nodes)
    node_to_idx = {node: i for i, node in enumerate(selected_nodes)}

    dist_matrix = np.full((n, n), 1e6, dtype=np.float64)
    np.fill_diagonal(dist_matrix, 0.0)

    # Edge weight: length
    for i, src in enumerate(selected_nodes):
        lengths = nx.single_source_dijkstra_path_length(G, src, weight="length")
        for target, d in lengths.items():
            if target in node_to_idx:
                j = node_to_idx[target]
                dist_matrix[i, j] = float(d)

    # If disconnected paths exist, fallback to Haversine * 1.4 detour
    coords = {nid: (G.nodes[nid].get("y", 10.8), G.nodes[nid].get("x", 106.7)) for nid in selected_nodes}
    for i in range(n):
        for j in range(n):
            if i != j and dist_matrix[i, j] >= 1e5:
                lat1, lon1 = coords[selected_nodes[i]]
                lat2, lon2 = coords[selected_nodes[j]]
                h_dist = math.sqrt((lat1 - lat2) ** 2 + ((lon1 - lon2) * 0.98) ** 2) * 111000.0 * 1.4
                dist_matrix[i, j] = float(h_dist)

    # Time matrix in minutes: (dist / 1000) / (speed / 60)
    time_matrix = (dist_matrix / 1000.0) / (speed_kmh / 60.0)

    np.savez_compressed(
        output_path,
        dist_matrix=dist_matrix,
        time_matrix=time_matrix,
        node_ids=np.array(selected_nodes),
    )
    print(f"Saved precomputed matrix to {output_path} (shape: {dist_matrix.shape})")


if __name__ == "__main__":
    generate_address_pools()
