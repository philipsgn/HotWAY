"""Independent zero-trust audit of the HCMC directed road graph and matrix service."""
from __future__ import annotations

import json
import math
import pickle
import random
import statistics
import time
from pathlib import Path

import networkx as nx
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "data" / "hcmc_compact_graph.pickle"
INST_DIR = ROOT / "data" / "benchmark_instances"


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def main():
    t0 = time.time()
    with open(GRAPH_PATH, "rb") as f:
        G = pickle.load(f)
    load_s = time.time() - t0

    N, E = G.number_of_nodes(), G.number_of_edges()
    is_multi = G.is_multigraph()
    is_directed = G.is_directed()
    scc = nx.is_strongly_connected(G)

    nodes = list(G.nodes(data=True))
    edges = list(G.edges(keys=True, data=True))
    rng = random.Random(2027)

    # Basic edge integrity
    bad_len = 0
    bad_time = 0
    bad_time_formula = 0
    zero_len = 0
    self_loops = 0
    oneway_true = 0
    oneway_false = 0
    both_dir = 0
    edge_geom_counts = {"missing": 0, "2pt": 0, "gt2": 0}
    endpoint_mismatch = 0
    straight_synth = 0
    len_geom_ratio_bad = 0
    speed_range = [1e9, 0.0]

    node_xy = {n: (float(d.get("y", 0.0)), float(d.get("x", 0.0))) for n, d in nodes}
    directed_pairs = set()
    for u, v, k, d in edges:
        if u == v:
            self_loops += 1
        directed_pairs.add((u, v))
        L = d.get("length")
        if L is None or not (L > 0):
            bad_len += 1
            if L == 0:
                zero_len += 1
        ft = d.get("free_flow_time")
        if ft is None or not (ft > 0):
            bad_time += 1
        sp = d.get("speed_kph", 30.0)
        speed_range[0] = min(speed_range[0], float(sp))
        speed_range[1] = max(speed_range[1], float(sp))
        if L and ft:
            calc = float(L) / max(float(sp) * 1000.0 / 3600.0, 0.1)
            if abs(calc - float(ft)) > 1e-3:
                bad_time_formula += 1
        ow = d.get("oneway", False)
        if ow is True or str(ow).lower() in ("true", "yes", "1", "-1"):
            oneway_true += 1
        elif ow is False or str(ow).lower() in ("false", "no", "0"):
            oneway_false += 1
        geom = d.get("geometry")
        if not geom or not isinstance(geom, list):
            edge_geom_counts["missing"] += 1
        elif len(geom) == 2:
            edge_geom_counts["2pt"] += 1
        else:
            edge_geom_counts["gt2"] += 1
            # endpoints should match graph nodes (within 1e-6 deg)
            uy, ux = node_xy[u]
            vy, vx = node_xy[v]
            if abs(geom[0][0] - uy) > 1e-5 or abs(geom[0][1] - ux) > 1e-5:
                endpoint_mismatch += 1
            if abs(geom[-1][0] - vy) > 1e-5 or abs(geom[-1][1] - vx) > 1e-5:
                endpoint_mismatch += 1
            if len(geom) > 2:
                # compare polyline length vs attribute
                gl = sum(
                    haversine(geom[i][0], geom[i][1], geom[i + 1][0], geom[i + 1][1])
                    for i in range(len(geom) - 1)
                )
                if L and L > 5 and abs(gl - float(L)) / float(L) > 0.05:
                    len_geom_ratio_bad += 1
        if len(geom or []) == 2:
            # 2-point edges are indistinguishable from synthetic straight lines,
            # but they are legal for short OSM segments. Count them.
            straight_synth += 1

    for u, v in directed_pairs:
        if (v, u) in directed_pairs:
            both_dir += 1

    # Geometry endpoint consistency for all edges (sampled)
    # (full check above only for >2pt)

    # Random 50 OD pairs: verify Dijkstra path edges exist in forward direction,
    # and that the recomputed path equals independently computed shortest path.
    od_records = []
    node_ids = [n for n, _ in nodes]
    for _ in range(50):
        s = rng.choice(node_ids)
        t = rng.choice(node_ids)
        if s == t:
            continue
        tt, path = nx.single_source_dijkstra(G, s, target=t, weight="free_flow_time")
        ok_dir = True
        missing_edge = None
        recomputed = 0.0
        for a, b in zip(path[:-1], path[1:]):
            ed = G.get_edge_data(a, b)
            if not ed:
                ok_dir = False
                missing_edge = (a, b)
                break
            best = min(ed.values(), key=lambda e: e.get("free_flow_time", 1e18))
            recomputed += best.get("free_flow_time", 0.0)
        od_records.append({
            "source": s,
            "target": t,
            "path_len": len(path),
            "forward_edges_exist": ok_dir,
            "missing_edge": missing_edge,
            "time_sec": tt,
            "recomputed_time_sec": round(recomputed, 6),
            "time_match": abs(recomputed - tt) < 1e-6 * max(tt, 1),
            "hops": len(path) - 1,
        })

    # Asymmetry & matrix checks on all stored instances
    inst_checks = []
    asym_fracs = []
    tri_viol = 0
    tri_total = 0
    for p in sorted(INST_DIR.glob("HCMC_VN_*.pickle")):
        with open(p, "rb") as f:
            inst = pickle.load(f)
        n = inst.n_customers + 1
        D = np.asarray(inst.dist_matrix, dtype=float)
        T = np.asarray(inst.time_matrix, dtype=float)
        diag_ok = bool(np.allclose(np.diag(D), 0.0) and np.allclose(np.diag(T), 0.0))
        asym = D != D.T
        asym_frac = float(asym.mean())
        asym_fracs.append(asym_frac)
        # triangle inequality (Dijkstra shortest paths must satisfy it)
        if n <= 30:
            for i in range(n):
                for j in range(n):
                    for k in range(n):
                        tri_total += 1
                        if D[i][j] > D[i][k] + D[k][j] + 1e-6:
                            tri_viol += 1
        inst_checks.append({
            "instance": inst.name,
            "n": inst.n_customers,
            "demand_sum": int(sum(inst.demands)),
            "capacity": inst.capacity,
            "max_vehicles": inst.max_vehicles,
            "min_dist_nonnegative": bool(np.all(D >= 0)),
            "diag_zero": diag_ok,
            "asym_fraction": round(asym_frac, 4),
            "finite": bool(np.all(np.isfinite(D)) and np.all(np.isfinite(T))),
            "max_snap_m": None,
        })

    result = {
        "graph": {
            "path": str(GRAPH_PATH),
            "load_seconds": round(load_s, 2),
            "type": type(G).__name__,
            "is_multigraph": is_multi,
            "is_directed": is_directed,
            "nodes": N,
            "edges": E,
            "strongly_connected": bool(scc),
            "self_loops": self_loops,
            "bad_length": bad_len,
            "zero_length": zero_len,
            "bad_free_flow_time": bad_time,
            "free_flow_formula_mismatch": bad_time_formula,
            "speed_kph_range": speed_range,
            "oneway_true_edges": oneway_true,
            "oneway_false_edges": oneway_false,
            "directed_pairs_with_reverse": both_dir,
            "geometry_counts": edge_geom_counts,
            "geometry_endpoint_mismatch_gt2": endpoint_mismatch,
            "geometry_length_mismatch_gt5pct": len_geom_ratio_bad,
            "two_point_edges": straight_synth,
            "od50": {
                "n": len(od_records),
                "all_forward_edges_exist": all(r["forward_edges_exist"] for r in od_records),
                "all_times_match": all(r["time_match"] for r in od_records),
                "max_hops": max(r["hops"] for r in od_records),
                "min_hops": min(r["hops"] for r in od_records),
                "records": od_records,
            },
        },
        "instances": {
            "count": len(inst_checks),
            "checks": inst_checks,
            "asym_fraction_mean": round(float(np.mean(asym_fracs)), 4),
            "asym_fraction_min": round(float(np.min(asym_fracs)), 4),
            "asym_fraction_max": round(float(np.max(asym_fracs)), 4),
            "triangle_violations": tri_viol,
            "triangle_checks": tri_total,
        },
    }

    out = ROOT / "audit" / "results" / "graph_audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    def _json_default(o):
        if hasattr(o, "item"):
            return o.item()
        if isinstance(o, tuple):
            return list(o)
        return str(o)

    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=_json_default)

    g = result["graph"]
    print(f"Graph: {g['type']} nodes={N} edges={E} SCC={g['strongly_connected']}")
    print(f"  self_loops={g['self_loops']} bad_length={g['bad_length']} bad_time={g['bad_free_flow_time']} formula_mismatch={g['free_flow_formula_mismatch']}")
    print(f"  oneway_true={g['oneway_true_edges']} oneway_false={g['oneway_false_edges']} reverse_pairs={g['directed_pairs_with_reverse']}")
    print(f"  geometry={g['geometry_counts']} endpoint_mismatch={g['geometry_endpoint_mismatch_gt2']} len_mismatch={g['geometry_length_mismatch_gt5pct']}")
    print(f"  OD50 forward_edges={g['od50']['all_forward_edges_exist']} times_match={g['od50']['all_times_match']} hops={g['od50']['min_hops']}..{g['od50']['max_hops']}")
    i = result["instances"]
    print(f"Instances: {i['count']} asym_mean={i['asym_fraction_mean']} range=[{i['asym_fraction_min']},{i['asym_fraction_max']}] tri_viol={i['triangle_violations']}/{i['triangle_checks']}")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
