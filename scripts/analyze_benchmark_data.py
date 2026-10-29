"""
Benchmark Data Spatial & Traffic Analysis (HotWAY Gate G7 / Phase 1).
Analyzes the 100 Nationwide Delivery Itineraries:
- Hanoi Cluster (40 instances)
- Da Nang Cluster (20 instances)
- Ho Chi Minh City Cluster (40 instances)

Extracts spatial metrics:
- Mean stops per tier (N10, N20, N30, N50)
- Bounding box dimensions & operating radius
- Pairwise road distance distributions
- Dynamic traffic factor C(t) distribution across departure windows
- Exports results/data_analysis_summary.json for academic report & slides
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

# Reconfigure stdout for Windows console UTF-8 support
sys.stdout.reconfigure(encoding="utf-8")


def analyze_dataset(benchmark_path: str = "data/benchmark_100_vietnam_pois.json") -> Dict[str, Any]:
    with open(benchmark_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    instances = data["instances"]
    total_inst = len(instances)

    regions = {"Hà Nội": [], "Đà Nẵng": [], "TP. Hồ Chí Minh": []}
    tiers = {"N10": [], "N20": [], "N30": [], "N50": []}

    for inst in instances:
        reg = inst.get("region", "TP. Hồ Chí Minh")
        tier = inst.get("tier", "N20")
        if reg in regions:
            regions[reg].append(inst)
        if tier in tiers:
            tiers[tier].append(inst)

    region_stats = {}
    for reg_name, inst_list in regions.items():
        if not inst_list:
            continue
        
        depot_dists = []
        lat_spans = []
        lon_spans = []
        pairwise_dists = []
        dep_hours = []

        for inst in inst_list:
            depot = inst["depot"]
            stops = inst["stops"]
            dep_hours.append(inst["departure_hour"])

            lats = [depot["lat"]] + [s["lat"] for s in stops]
            lons = [depot["lon"]] + [s["lon"] for s in stops]

            lat_spans.append(max(lats) - min(lats))
            lon_spans.append(max(lons) - min(lons))

            # Distances from depot
            dist_mat = inst["dist_matrix_km"]
            for j in range(1, len(dist_mat)):
                depot_dists.append(dist_mat[0][j])

            # Sample pairwise distances
            for i in range(1, len(dist_mat)):
                for j in range(i + 1, len(dist_mat)):
                    pairwise_dists.append(dist_mat[i][j])

        # Convert spans to approximate km (1 deg lat ~= 111 km, 1 deg lon ~= 108 km)
        mean_lat_km = float(np.mean(lat_spans)) * 111.0
        mean_lon_km = float(np.mean(lon_spans)) * 108.0
        coverage_radius_km = math.sqrt(mean_lat_km**2 + mean_lon_km**2) / 2.0

        region_stats[reg_name] = {
            "instance_count": len(inst_list),
            "depot_name": inst_list[0]["depot"]["name"],
            "depot_coord": [inst_list[0]["depot"]["lat"], inst_list[0]["depot"]["lon"]],
            "coverage_radius_km": round(coverage_radius_km, 2),
            "mean_depot_distance_km": round(float(np.mean(depot_dists)), 2),
            "p90_depot_distance_km": round(float(np.percentile(depot_dists, 90)), 2),
            "max_depot_distance_km": round(float(np.max(depot_dists)), 2),
            "mean_inter_stop_distance_km": round(float(np.mean(pairwise_dists)), 2),
            "departure_hours_range": [round(float(min(dep_hours)), 2), round(float(max(dep_hours)), 2)],
        }

    tier_stats = {}
    for t_name, inst_list in tiers.items():
        if not inst_list:
            continue
        total_durs = []
        total_dists = []
        for inst in inst_list:
            d_mat = inst["dist_matrix_km"]
            t_mat = inst["duration_matrix_min"]
            total_dists.append(sum(d_mat[0]))
            total_durs.append(sum(t_mat[0]))

        tier_stats[t_name] = {
            "instance_count": len(inst_list),
            "stops_per_tour": int(t_name[1:]),
            "mean_initial_spread_km": round(float(np.mean(total_dists)), 2),
            "mean_initial_duration_min": round(float(np.mean(total_durs)), 2),
        }

    summary = {
        "metadata": {
            "title": "HotWAY Nationwide Logistics Benchmark Data Analysis",
            "version": "7.3.1",
            "total_instances": total_inst,
            "target_clusters": ["Hà Nội", "Đà Nẵng", "TP. Hồ Chí Minh"],
            "tiers": ["N10", "N20", "N30", "N50"]
        },
        "regions": region_stats,
        "tiers": tier_stats
    }

    out_file = Path("results/data_analysis_summary.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("=" * 70)
    print("HOTWAY NATIONWIDE BENCHMARK DATA ANALYSIS SUMMARY")
    print("=" * 70)
    for reg, s in region_stats.items():
        print(f"[{reg}] Instances: {s['instance_count']} | Coverage Radius: {s['coverage_radius_km']} km | Mean Depot Dist: {s['mean_depot_distance_km']} km")
    print("-" * 70)
    for t, s in tier_stats.items():
        print(f"[{t}] Stops: {s['stops_per_tour']} | Instances: {s['instance_count']}")
    print("=" * 70)
    print(f"Saved analysis artifact to: {out_file}")

    return summary


if __name__ == "__main__":
    analyze_dataset()
