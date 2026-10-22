"""Quantify distance-matrix triangle violations and excess over true shortest paths."""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import networkx as nx
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.benchmark.instance_generator import load_benchmark_instances  # noqa: E402
from src.services.road_matrix import snap_coordinate_to_node  # noqa: E402

OUT = ROOT / "audit" / "results" / "triangle_check.json"


def main() -> None:
    with open(ROOT / "data" / "hcmc_compact_graph.pickle", "rb") as f:
        graph = pickle.load(f)
    instances = load_benchmark_instances(ROOT / "data" / "benchmark_instances")
    by_id = {i.name: i for i in instances}

    records = []
    for name in [f"HCMC_VN_{i:02d}" for i in range(25, 31)]:
        inst = by_id[name]
        node_ids = [
            int(snap_coordinate_to_node(float(lat), float(lon), graph=graph)[0])
            for lat, lon in inst.coords
        ]
        cache = {}
        for src in node_ids:
            cache[src] = nx.single_source_dijkstra_path_length(graph, src, weight="length")
        n = len(node_ids)
        d = np.array(inst.dist_matrix, dtype=float)
        t = np.array(inst.time_matrix, dtype=float)
        tri = 0
        tri_max = 0.0
        for i in range(n):
            for j in range(n):
                for k in range(n):
                    if i == j or j == k or i == k:
                        continue
                    excess = d[i][k] - (d[i][j] + d[j][k])
                    if excess > 1e-6:
                        tri += 1
                        tri_max = max(tri_max, excess)
        extra = []
        for i, a in enumerate(node_ids):
            for j, b in enumerate(node_ids):
                if i == j:
                    continue
                true_d = cache[a].get(b, float("inf"))
                extra.append(d[i][j] - true_d)
        extra = np.array(extra)
        t_tri = 0
        t_max = 0.0
        for i in range(n):
            for j in range(n):
                for k in range(n):
                    if i == j or j == k or i == k:
                        continue
                    excess = t[i][k] - (t[i][j] + t[j][k])
                    if excess > 1e-6:
                        t_tri += 1
                        t_max = max(t_max, excess)
        records.append({
            "instance": name,
            "n_nodes": n,
            "triangle_violations": int(tri),
            "triangle_checks": int(n * (n - 1) * (n - 2)),
            "max_triangle_violation_m": round(float(tri_max), 1),
            "pairs_over_true_shortest": int((extra > 0.001).sum()),
            "pairs_checked": int(len(extra)),
            "max_excess_over_shortest_m": round(float(extra.max()), 1),
            "median_excess_over_shortest_m": round(float(np.median(extra)), 2),
            "time_triangle_violations": int(t_tri),
            "time_max_violation_sec": round(float(t_max), 3),
        })
        print(records[-1], flush=True)

    OUT.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
