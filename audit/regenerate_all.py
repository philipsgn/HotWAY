"""Regenerate all 30 benchmark instances from source and compare byte-level content."""
from __future__ import annotations

import json
import pickle
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.benchmark.instance_generator import generate_single_instance  # noqa: E402
from src.data.build_graph import load_site_config  # noqa: E402
from src.services.road_matrix import get_road_graph  # noqa: E402

INST_DIR = ROOT / "data" / "benchmark_instances"


def main():
    cfg = load_site_config(ROOT / "config" / "site.yaml")
    bm = cfg["benchmark"]
    depot = (cfg["site"]["depot"]["lat"], cfg["site"]["depot"]["lon"])
    graph = get_road_graph(region=cfg.get("default_region", "hcmc_compact"), config_path=ROOT / "config/site.yaml")
    rng = random.Random(bm["base_seed"])

    results = []
    t0 = time.time()
    for i in range(1, bm["n_instances"] + 1):
        inst_id = f"HCMC_VN_{i:02d}"
        seed = bm["base_seed"] + i * 17
        n_cust = rng.randint(bm["customers_range"][0], bm["customers_range"][1])
        t = time.time()
        inst = generate_single_instance(
            instance_id=inst_id,
            n_customers=n_cust,
            graph=graph,
            depot_coord=depot,
            demand_range=tuple(bm["demand_range"]),
            vehicle_capacity=cfg["fleet"]["vehicle_capacity"],
            max_vehicles=cfg["fleet"]["default_vehicles"],
            max_radius_km=bm["customer_radius_km"],
            seed=seed,
        )
        with open(INST_DIR / f"{inst_id}.pickle", "rb") as f:
            orig = pickle.load(f)
        rec = {
            "instance": inst_id,
            "seed": seed,
            "n_customers": n_cust,
            "coords_match": inst.coords == orig.coords,
            "demands_match": inst.demands == orig.demands,
            "dist_matrix_match": inst.dist_matrix == orig.dist_matrix,
            "time_matrix_match": inst.time_matrix == orig.time_matrix,
            "stops_match": [(s.id, s.order_id, s.demand) for s in inst.stops]
            == [(s.id, s.order_id, s.demand) for s in orig.stops],
            "gen_seconds": round(time.time() - t, 2),
        }
        results.append(rec)
        print(f"[{i:02d}/30] {inst_id} n={n_cust} match coords={rec['coords_match']} demands={rec['demands_match']} D={rec['dist_matrix_match']} T={rec['time_matrix_match']} ({rec['gen_seconds']}s)", flush=True)

    summary = {
        "generated": len(results),
        "all_coords_match": all(r["coords_match"] for r in results),
        "all_demands_match": all(r["demands_match"] for r in results),
        "all_dist_match": all(r["dist_matrix_match"] for r in results),
        "all_time_match": all(r["time_matrix_match"] for r in results),
        "all_stops_match": all(r["stops_match"] for r in results),
        "total_seconds": round(time.time() - t0, 1),
        "records": results,
    }
    out = ROOT / "audit" / "results" / "regeneration_audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"DONE all_match={all(summary[k] for k in summary if k.startswith('all_'))} in {summary['total_seconds']}s -> {out}", flush=True)


if __name__ == "__main__":
    main()
