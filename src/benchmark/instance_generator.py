"""
HotWAY CVRP Benchmark Instance Generator v5.0
Generates reproducible, real-world CVRP test instances on Ho Chi Minh City road network.

Properties:
- Customers sampled from nodes of the Strongly Connected Component (SCC).
- Random demands sampled uniformly in [min_demand, max_demand].
- Vehicle capacity Q=40, max_vehicles=5.
- Distance & time matrices computed via single-source Dijkstra on real directed graph.
- Base seed + instance index ensures 100% reproducibility.
"""

from __future__ import annotations

import json
import logging
import math
import os
import pickle
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx
import numpy as np

from src.cvrp_solver.problem import CVRPInstance, CVRPStop
from src.data.build_graph import haversine, load_site_config
from src.services.road_matrix import compute_road_matrix, get_road_graph

logger = logging.getLogger("instance_generator")


def generate_single_instance(
    instance_id: str,
    n_customers: int,
    graph: nx.MultiDiGraph,
    depot_coord: Tuple[float, float],
    demand_range: Tuple[int, int] = (1, 8),
    vehicle_capacity: int = 40,
    max_vehicles: int = 5,
    max_radius_km: float = 8.0,
    seed: int = 2026,
) -> CVRPInstance:
    """
    Generates a single CVRPInstance with N customers sampled within max_radius_km of depot.
    Uses exact road network topology and Dijkstra travel times.
    """
    rng = random.Random(seed)
    depot_lat, depot_lon = depot_coord

    # Filter candidate nodes in graph within max_radius_km of depot
    candidates: List[Tuple[Any, float, float]] = []
    for nid, data in graph.nodes(data=True):
        lat = data.get("y", data.get("lat"))
        lon = data.get("x", data.get("lon"))
        if lat is None or lon is None:
            continue
        d_km = haversine(depot_lat, depot_lon, lat, lon) / 1000.0
        # Exclude nodes too close to depot (< 300m) or too far (> max_radius_km)
        if 0.3 <= d_km <= max_radius_km:
            candidates.append((nid, lat, lon))

    if len(candidates) < n_customers:
        # Fallback to all candidate nodes
        candidates = [
            (nid, data.get("y", data.get("lat")), data.get("x", data.get("lon")))
            for nid, data in graph.nodes(data=True)
            if data.get("y") is not None
        ]

    # Sample n_customers nodes without replacement
    sampled = rng.sample(candidates, n_customers)

    # Build points list: points[0] is depot, points[1..n] are customers
    points = [
        {"id": "DEPOT", "lat": depot_lat, "lon": depot_lon, "demand": 0}
    ]
    for idx, (nid, lat, lon) in enumerate(sampled, start=1):
        dem = rng.randint(demand_range[0], demand_range[1])
        points.append({
            "id": f"ORD_{instance_id}_{idx:02d}",
            "lat": lat,
            "lon": lon,
            "demand": dem,
            "node_id": str(nid),
        })

    # Compute asymmetric distance and travel time matrix
    matrix_res = compute_road_matrix(points, graph=graph)
    
    demands = [p["demand"] for p in points]
    coords = [[p["lat"], p["lon"]] for p in points]
    stops = [
        CVRPStop(
            id=p["id"],
            order_id=p["id"],
            lat=p["lat"],
            lon=p["lon"],
            demand=p["demand"],
        )
        for p in points
    ]

    return CVRPInstance(
        name=instance_id,
        n_customers=n_customers,
        capacity=vehicle_capacity,
        max_vehicles=max_vehicles,
        demands=demands,
        dist_matrix=matrix_res["dist_matrix"],
        time_matrix=matrix_res["time_matrix"],
        stops=stops,
        coords=coords,
    )


def generate_benchmark_suite(
    output_dir: Path | str = "data/benchmark_instances",
    region: str = "hcmc_compact",
    config_path: Path | str = "config/site.yaml",
) -> List[CVRPInstance]:
    """
    Generates and saves the standard 30 benchmark instances as specified in config/site.yaml.
    """
    config = load_site_config(config_path)
    bm_cfg = config.get("benchmark", {})
    n_instances = bm_cfg.get("n_instances", 30)
    cust_range = bm_cfg.get("customers_range", [15, 25])
    demand_range = tuple(bm_cfg.get("demand_range", [1, 8]))
    base_seed = bm_cfg.get("base_seed", 2026)
    radius_km = bm_cfg.get("customer_radius_km", 8.0)

    site_depot = config["site"]["depot"]
    depot_coord = (site_depot["lat"], site_depot["lon"])

    capacity = config["fleet"]["vehicle_capacity"]
    max_vehicles = config["fleet"]["default_vehicles"]

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading road graph for region '{region}'...")
    graph = get_road_graph(region=region, config_path=config_path)
    logger.info(f"Graph loaded: {graph.number_of_nodes()} nodes.")

    instances: List[CVRPInstance] = []
    meta: List[Dict[str, Any]] = []

    rng = random.Random(base_seed)

    for i in range(1, n_instances + 1):
        inst_id = f"HCMC_VN_{i:02d}"
        seed = base_seed + i * 17
        n_cust = rng.randint(cust_range[0], cust_range[1])
        
        logger.info(f"Generating instance {inst_id} ({i}/{n_instances}): {n_cust} customers (seed={seed})...")
        inst = generate_single_instance(
            instance_id=inst_id,
            n_customers=n_cust,
            graph=graph,
            depot_coord=depot_coord,
            demand_range=demand_range,
            vehicle_capacity=capacity,
            max_vehicles=max_vehicles,
            max_radius_km=radius_km,
            seed=seed,
        )
        instances.append(inst)

        # Save individual instance as pickle
        inst_path = out / f"{inst_id}.pickle"
        with open(inst_path, "wb") as f:
            pickle.dump(inst, f)

        meta.append({
            "instance_id": inst_id,
            "num_customers": n_cust,
            "total_demand": sum(inst.demands),
            "vehicle_capacity": capacity,
            "max_vehicles": max_vehicles,
            "seed": seed,
            "depot": depot_coord,
        })

    # Save metadata summary
    summary_path = out / "instances_index.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    logger.info(f"Generated {len(instances)} benchmark instances in {output_dir}")
    return instances


def load_benchmark_instances(
    instances_dir: Path | str = "data/benchmark_instances"
) -> List[CVRPInstance]:
    """Loads all pre-generated benchmark instances from directory."""
    p = Path(instances_dir)
    instances = []
    idx_file = p / "instances_index.json"
    if idx_file.exists():
        with open(idx_file, "r", encoding="utf-8") as f:
            meta = json.load(f)
        for item in meta:
            inst_file = p / f"{item['instance_id']}.pickle"
            if inst_file.exists():
                with open(inst_file, "rb") as f:
                    instances.append(pickle.load(f))
    return instances


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate CVRP Benchmark Instances")
    parser.add_argument("--region", type=str, default="hcmc_compact", help="Road graph region")
    parser.add_argument("--out", type=str, default="data/benchmark_instances", help="Output directory")
    args = parser.parse_args()

    generate_benchmark_suite(output_dir=args.out, region=args.region)
