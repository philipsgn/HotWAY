"""Independent audit of the 30 CVRP benchmark instances and the train/val/test split."""
from __future__ import annotations

import json
import math
import pickle
import statistics
from pathlib import Path

import numpy as np

from src.cvrp_solver.constructive import clarke_wright_savings
from src.cvrp_solver.search import calculate_thermal_profile
from src.cvrp_solver.validator import validate_cvrp_solution
from src.services.road_matrix import get_road_graph, snap_coordinate_to_node

ROOT = Path(__file__).resolve().parents[1]
INST_DIR = ROOT / "data" / "benchmark_instances"


def haversine(a, b, c, d):
    R = 6371000.0
    p1, p2 = math.radians(a), math.radians(c)
    dp = math.radians(c - a)
    dl = math.radians(d - b)
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(x), math.sqrt(1 - x))


def main():
    with open(INST_DIR / "instances_index.json", encoding="utf-8") as f:
        index = {r["instance_id"]: r for r in json.load(f)}
    G = get_road_graph(region="hcmc_compact")
    depot = (10.8012, 106.7145)

    records = []
    for p in sorted(INST_DIR.glob("HCMC_VN_*.pickle")):
        with open(p, "rb") as f:
            inst = pickle.load(f)
        meta = index[inst.name]

        max_snap = 0.0
        snap_warn = 0
        for c in inst.coords:
            nid, d, exceeds = snap_coordinate_to_node(c[0], c[1], G, max_snap_meters=60.0)
            max_snap = max(max_snap, d)
            snap_warn += int(exceeds)

        demands = [int(x) for x in inst.demands]
        assert demands[0] == 0
        radius_km = max(haversine(depot[0], depot[1], c[0], c[1]) for c in inst.coords) / 1000.0

        cw = clarke_wright_savings(inst)
        ok, cw_dist, msg = validate_cvrp_solution(cw, inst)
        cw_thermal_viol = 0
        cw_min_temp = 999.0
        cw_max_time = 0.0
        for r in cw:
            stops, dur, viol = calculate_thermal_profile(r, inst)
            cw_thermal_viol += viol
            cw_max_time = max(cw_max_time, dur / 60.0)
            for s in stops:
                cw_min_temp = min(cw_min_temp, s.estimated_temp_c)

        records.append({
            "instance": inst.name,
            "split": "train" if int(inst.name[-2:]) <= 20 else ("val" if int(inst.name[-2:]) <= 24 else "test"),
            "n_customers": inst.n_customers,
            "demand_sum": int(sum(demands)),
            "demand_min": int(min(demands[1:])),
            "demand_max": int(max(demands[1:])),
            "capacity": inst.capacity,
            "max_vehicles": inst.max_vehicles,
            "requires_min_vehicles_ceil": int(math.ceil(sum(demands) / inst.capacity)),
            "metadata_matches": (
                meta["num_customers"] == inst.n_customers
                and meta["total_demand"] == sum(demands)
                and meta["vehicle_capacity"] == inst.capacity
                and meta["max_vehicles"] == inst.max_vehicles
            ),
            "coords_all_within_60m": snap_warn == 0,
            "max_snap_m": round(max_snap, 2),
            "radius_km": round(radius_km, 3),
            "cw_routes": len(cw),
            "cw_valid": bool(ok),
            "cw_cost_km": round(cw_dist / 1000.0, 3),
            "cw_thermal_violations": cw_thermal_viol,
            "cw_min_temp_c": round(cw_min_temp, 1),
            "cw_max_route_min": round(cw_max_time, 1),
            "thermal_feasible_cw": cw_thermal_viol == 0,
        })

    splits = {}
    for name in ("train", "val", "test"):
        sub = [r for r in records if r["split"] == name]
        splits[name] = {
            "n_instances": len(sub),
            "n_customers_mean": round(float(np.mean([r["n_customers"] for r in sub])), 2),
            "n_customers_range": [min(r["n_customers"] for r in sub), max(r["n_customers"] for r in sub)],
            "demand_mean": round(float(np.mean([r["demand_sum"] for r in sub])), 2),
            "radius_km_mean": round(float(np.mean([r["radius_km"] for r in sub])), 3),
            "cw_cost_km_mean": round(float(np.mean([r["cw_cost_km"] for r in sub])), 3),
            "cw_thermal_violations_mean": round(float(np.mean([r["cw_thermal_violations"] for r in sub])), 2),
            "thermal_feasible_cw_count": int(sum(r["thermal_feasible_cw"] for r in sub)),
        }

    all_meta_ok = all(r["metadata_matches"] for r in records)
    all_snap_ok = all(r["coords_all_within_60m"] for r in records)
    all_cw_valid = all(r["cw_valid"] for r in records)
    thermal_feasible = sum(r["thermal_feasible_cw"] for r in records)

    result = {
        "instance_count": len(records),
        "metadata_all_match_index": bool(all_meta_ok),
        "all_coords_snap_within_60m": bool(all_snap_ok),
        "all_clarke_wright_capacity_fleet_valid": bool(all_cw_valid),
        "thermal_feasible_instances_under_cw": int(thermal_feasible),
        "total_thermal_violations_under_cw": int(sum(r["cw_thermal_violations"] for r in records)),
        "splits": splits,
        "records": records,
    }
    out = ROOT / "audit" / "results" / "instance_audit.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Instances: {len(records)} | metadata_ok={all_meta_ok} | snap<=60m={all_snap_ok} | CW feasible={all_cw_valid}")
    print(f"Thermal-feasible under CW: {thermal_feasible}/{len(records)} (total violations {result['total_thermal_violations_under_cw']})")
    for name, s in splits.items():
        print(f"  {name:5s}: n={s['n_instances']:2d} customers~{s['n_customers_mean']:.1f} {s['n_customers_range']} demand~{s['demand_mean']:.1f} radius~{s['radius_km_mean']:.2f}km CW~{s['cw_cost_km_mean']:.1f}km therm_viol~{s['cw_thermal_violations_mean']:.1f}")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
