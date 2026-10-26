"""
Subgraph Extractor for GĐ1 (Time-Dependent Stochastic Routing).
Extracts a strongly connected component (12-16 nodes) from the real HCMC OpenStreetMap graph
around Hang Gon Quan (Binh Thanh) with parallel streets and connecting alleys.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Tuple, List, Dict, Any

import networkx as nx
import numpy as np


def extract_binhthanh_subgraph(
    full_graph_path: str | Path = "data/hcmc_compact_graph.pickle",
    output_path: str | Path = "data/binhthanh_routing_subgraph.pickle",
    depot_lat: float = 10.8012,
    depot_lon: float = 106.7145,
    min_nodes: int = 12,
    max_nodes: int = 16,
) -> nx.MultiDiGraph:
    """Extracts a strongly connected subgraph around depot with 12-16 nodes."""
    full_path = Path(full_graph_path)
    if not full_path.exists():
        raise FileNotFoundError(f"Full graph not found at {full_path}")

    with open(full_path, "rb") as f:
        G = pickle.load(f)

    # Search radii to find an SCC with target node count
    target_comp = None
    for radius in np.arange(350, 800, 25):
        cands = []
        for n, d in G.nodes(data=True):
            lat = d.get("y", d.get("lat", 0.0))
            lon = d.get("x", d.get("lon", 0.0))
            dist = ((lat - depot_lat) ** 2 + (lon - depot_lon) ** 2) ** 0.5 * 111000.0
            if dist <= radius:
                cands.append(n)

        subG = G.subgraph(cands).copy()
        sccs = list(nx.strongly_connected_components(subG))
        for comp in sccs:
            if min_nodes <= len(comp) <= max_nodes:
                target_comp = comp
                break
        if target_comp is not None:
            break

    if target_comp is None:
        # Fallback to largest SCC in 500m
        cands = [
            n for n, d in G.nodes(data=True)
            if (((d.get("y", d.get("lat", 0.0)) - depot_lat) ** 2 +
                 (d.get("x", d.get("lon", 0.0)) - depot_lon) ** 2) ** 0.5 * 111000.0) <= 500.0
        ]
        subG = G.subgraph(cands).copy()
        target_comp = max(nx.strongly_connected_components(subG), key=len)

    extracted_subgraph = G.subgraph(target_comp).copy()
    
    # Ensure node IDs are mapped or preserved, compute lengths
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "wb") as f:
        pickle.dump(extracted_subgraph, f)

    return extracted_subgraph


if __name__ == "__main__":
    subg = extract_binhthanh_subgraph()
    print(f"Extracted subgraph successfully:")
    print(f"Nodes: {subg.number_of_nodes()}, Edges: {subg.number_of_edges()}")
    print(f"Is strongly connected: {nx.is_strongly_connected(subg)}")
