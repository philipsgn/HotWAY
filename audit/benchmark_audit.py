"""Independent CVRP benchmark with honest evaluation of time budgets, evals, and thermal feasibility.

This module deliberately reuses the public solver entry point but instruments it:
  * Q-network weights can be swapped (audit checkpoints vs the shipped checkpoints),
  * candidate evaluations are counted (not inferred as steps*candidates),
  * protocol time limits are optionally enforced (the shipped runner ignores them),
  * thermal feasibility is separated from capacity/fleet feasibility.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import src.cvrp_solver.search as search_mod  # noqa: E402
from src.benchmark.instance_generator import load_benchmark_instances  # noqa: E402
from src.cvrp_solver.constructive import clarke_wright_savings  # noqa: E402
from src.cvrp_solver.validator import calculate_route_distance, validate_cvrp_solution  # noqa: E402

STRATEGY_MAP = {
    "random": "Random",
    "cyclic": "Cyclic",
    "greedy": "Greedy",
    "dqn": "DQN",
    "double_dqn": "Double DQN",
}
STRATEGIES = list(STRATEGY_MAP)

PROTOCOLS = {
    "A2": {"max_steps": 100, "max_candidates": 256, "time_limit": None},
    "A": {"max_steps": 100, "max_candidates": 128, "time_limit": None},
    "A3": {"max_steps": 100, "max_candidates": 128, "time_limit": None},
    "B": {"max_steps": 200, "max_candidates": 64, "time_limit": 0.05},
    "B2": {"max_steps": 400, "max_candidates": 128, "time_limit": 0.10},
}

_BASE_INFERENCE = search_mod.QNetworkInference
_BASE_BEST_MOVE = search_mod.best_move


def install_weight_map(weight_map: Optional[Dict[str, str]]):
    class MappedInference(_BASE_INFERENCE):
        def __init__(self, weights_path=None, seed=42):
            mapped = weight_map.get(weights_path, weights_path) if weight_map else weights_path
            super().__init__(weights_path=mapped, seed=seed)

    search_mod.QNetworkInference = MappedInference


def make_timed_best_move(deadline: Optional[float], counter: Dict[str, Any]):
    def timed_best_move(action, routes, instance, max_candidates=128, rng=None):
        if deadline is not None and time.perf_counter() > deadline:
            counter["deadline_hit"] = True
            return False, 0.0, routes, 0
        applied, delta, new_routes, evals = _BASE_BEST_MOVE(
            action, routes, instance, max_candidates=max_candidates, rng=rng
        )
        counter["evals"] += evals
        counter["calls"] += 1
        counter["applied"] += int(bool(applied))
        return applied, delta, new_routes, evals

    return timed_best_move


def bootstrap_ci(diff: np.ndarray, n_resamples: int = 5000, seed: int = 2027) -> Tuple[float, float]:
    rng = np.random.RandomState(seed)
    if len(diff) == 0:
        return 0.0, 0.0
    means = np.array([np.mean(rng.choice(diff, size=len(diff), replace=True)) for _ in range(n_resamples)])
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def run_one(strategy: str, inst, cfg: Dict[str, Any], seed: int, enforce_time: bool):
    cw_routes = clarke_wright_savings(inst)
    cw_cost = sum(calculate_route_distance(r, inst.dist_matrix) for r in cw_routes)

    counter = {"evals": 0, "calls": 0, "applied": 0, "deadline_hit": False}
    deadline = None
    if enforce_time and cfg["time_limit"] is not None:
        deadline = time.perf_counter() + cfg["time_limit"]
    search_mod.best_move = make_timed_best_move(deadline, counter)

    t0 = time.perf_counter()
    sol = search_mod.solve_cvrp_strategy(
        strategy=strategy,
        instance=inst,
        max_steps=cfg["max_steps"],
        max_candidates=cfg["max_candidates"],
        seed=seed,
    )
    elapsed = time.perf_counter() - t0

    ok, val_cost, msg = validate_cvrp_solution(sol.routes, inst)
    temps = [s.estimated_temp_c for r in sol.detailed_routes for s in r.stops]
    times_min = [s.elapsed_time_min for r in sol.detailed_routes for s in r.stops]
    thermal_viol = int(sum(r.thermal_violations_count for r in sol.detailed_routes))
    min_temp = float(min(temps)) if temps else 85.0
    max_time = float(max(times_min)) if times_min else 0.0
    improvement = (cw_cost - sol.total_distance) / max(cw_cost, 1.0) * 100.0

    trace = sol.search_trace
    applied_steps = sum(1 for t in trace[1:] if t.get("applied"))
    action_hist = [0, 0, 0, 0]
    for t in trace[1:]:
        a = t.get("action", -1)
        if 0 <= a < 4:
            action_hist[a] += 1

    return {
        "instance_id": inst.name,
        "strategy": STRATEGY_MAP[strategy],
        "raw_strategy": strategy,
        "protocol": None,
        "seed": seed,
        "cw_cost_km": round(cw_cost / 1000.0, 4),
        "cost_km": round(sol.total_distance / 1000.0, 4),
        "cost_meters": round(sol.total_distance, 2),
        "improvement_pct": round(improvement, 6),
        "feasible_cvrp": bool(ok),
        "error_msg": "" if ok else msg,
        "thermal_violations": thermal_viol,
        "thermal_feasible": thermal_viol == 0,
        "min_delivery_temp_c": round(min_temp, 1),
        "max_delivery_time_min": round(max_time, 1),
        "num_vehicles": len(sol.routes),
        "runtime_ms": round(elapsed * 1000.0, 2),
        "runtime_sec": round(elapsed, 6),
        "decisions_traced": len(trace),
        "applied_steps": applied_steps,
        "evals_actual": counter["evals"],
        "best_move_calls": counter["calls"],
        "deadline_hit": counter["deadline_hit"],
        "action_0": action_hist[0],
        "action_1": action_hist[1],
        "action_2": action_hist[2],
        "action_3": action_hist[3],
        "candidates_budget": cfg["max_candidates"],
        "steps_budget": cfg["max_steps"],
        "time_limit": cfg["time_limit"],
        "enforce_time": enforce_time,
    }


def summarize(df: pd.DataFrame, protocols: List[str]) -> pd.DataFrame:
    rows = []
    for proto in protocols:
        sub = df[df["protocol"] == proto]
        for strat in [STRATEGY_MAP[s] for s in STRATEGIES]:
            s = sub[sub["strategy"] == strat]
            if s.empty:
                continue
            costs = s["cost_km"].values
            impr = s["improvement_pct"].values
            lo, hi = bootstrap_ci(impr)
            rows.append({
                "protocol": proto,
                "method": strat,
                "n_runs": len(s),
                "mean_distance_km": round(float(np.mean(costs)), 4),
                "median_distance_km": round(float(np.median(costs)), 4),
                "std_distance_km": round(float(np.std(costs, ddof=1)) if len(costs) > 1 else 0.0, 4),
                "mean_improvement_pct": round(float(np.mean(impr)), 4),
                "median_improvement_pct": round(float(np.median(impr)), 4),
                "improvement_ci_lower": round(lo, 4),
                "improvement_ci_upper": round(hi, 4),
                "feasible_cvrp_rate": round(float(s["feasible_cvrp"].mean()), 4),
                "thermal_feasible_rate": round(float(s["thermal_feasible"].mean()), 4),
                "mean_thermal_violations": round(float(s["thermal_violations"].mean()), 2),
                "mean_runtime_sec": round(float(s["runtime_sec"].mean()), 4),
                "max_runtime_sec": round(float(s["runtime_sec"].max()), 4),
                "deadline_hit_rate": round(float(s["deadline_hit"].mean()), 4),
                "mean_evals_actual": round(float(s["evals_actual"].mean()), 1),
                "mean_applied_steps": round(float(s["applied_steps"].mean()), 2),
                "mean_decisions_traced": round(float(s["decisions_traced"].mean()), 2),
            })
    return pd.DataFrame(rows)


def paired_stats(df: pd.DataFrame, protocols: List[str]) -> pd.DataFrame:
    pairs = [
        ("DQN", "Random"), ("DQN", "Cyclic"), ("DQN", "Greedy"),
        ("Double DQN", "Random"), ("Double DQN", "Cyclic"), ("Double DQN", "Greedy"),
        ("DQN", "Double DQN"),
    ]
    rows = []
    for proto in protocols:
        sub = df[df["protocol"] == proto]
        pivot = sub.pivot_table(index=["instance_id", "seed"], columns="strategy", values="cost_km")
        for a, b in pairs:
            if a not in pivot.columns or b not in pivot.columns:
                continue
            av = pivot[a].values
            bv = pivot[b].values
            mask = ~(np.isnan(av) | np.isnan(bv))
            av, bv = av[mask], bv[mask]
            if len(av) < 2:
                continue
            diff = av - bv
            lo, hi = bootstrap_ci(diff)
            try:
                stat, p = stats.wilcoxon(av, bv, alternative="two-sided", zero_method="wilcox")
            except Exception:
                p = 1.0
            # W/T/L on cost: lower is better for A
            tol = 0.001  # 1 metre
            w = int(np.sum(diff < -tol))
            t = int(np.sum(np.abs(diff) <= tol))
            l = int(np.sum(diff > tol))
            dz_denom = np.std(diff, ddof=1)
            dz = float(np.mean(diff) / dz_denom) if dz_denom > 0 else 0.0
            rows.append({
                "protocol": proto,
                "comparison": f"{a} - {b}",
                "n_pairs": len(diff),
                "mean_delta_cost_km": round(float(np.mean(diff)), 5),
                "ci_lower_km": round(lo, 5),
                "ci_upper_km": round(hi, 5),
                "w_t_l_lower_better": f"{w}/{t}/{l}",
                "cohen_dz": round(dz, 3),
                "p_wilcoxon_raw": p,
            })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["p_holm"] = np.nan
    for proto, idx in out.groupby("protocol").groups.items():
        sub = out.loc[idx]
        m = len(sub)
        order = np.argsort(sub["p_wilcoxon_raw"].values)
        adj = np.empty(m)
        cum = 0.0
        for rank, pos in enumerate(order):
            k = m - rank
            corr = min(1.0, float(sub["p_wilcoxon_raw"].values[pos]) * k)
            corr = max(corr, cum)
            cum = corr
            adj[pos] = corr
        out.loc[idx, "p_holm"] = adj
    out["p_wilcoxon_raw"] = out["p_wilcoxon_raw"].map(lambda x: float(f"{x:.6g}"))
    out["p_holm"] = out["p_holm"].map(lambda x: float(f"{x:.6g}"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", type=str, default="fair", help="weights tag: fair/repro/stock")
    ap.add_argument("--weights-dir", type=str, default="audit/weights")
    ap.add_argument("--weights-suffix", type=str, default="best", choices=["best", "final"])
    ap.add_argument("--instances", type=str, default="test", choices=["test", "all"])
    ap.add_argument("--protocols", type=str, default="A2,A,A3,B,B2")
    ap.add_argument("--seeds", type=str, default="2027")
    ap.add_argument("--enforce-time", action="store_true")
    ap.add_argument("--out-prefix", type=str, default=None)
    args = ap.parse_args()

    instances = load_benchmark_instances(ROOT / "data" / "benchmark_instances")
    if args.instances == "test":
        instances = [i for i in instances if int(i.name[-2:]) >= 25]
    protocols = [p.strip() for p in args.protocols.split(",") if p.strip()]
    seeds = [int(s.strip()) for s in args.seeds.split(",") if s.strip()]

    if args.tag == "stock":
        install_weight_map(None)
    else:
        wdir = ROOT / args.weights_dir
        sfx = args.weights_suffix
        install_weight_map({
            "src/cvrp_solver/weights/dqn_model.pt": str(wdir / f"{args.tag}_dqn_{sfx}.pt"),
            "src/cvrp_solver/weights/double_dqn_model.pt": str(wdir / f"{args.tag}_double_dqn_{sfx}.pt"),
        })

    rows = []
    total = len(protocols) * len(instances) * len(STRATEGIES) * len(seeds)
    n = 0
    t_start = time.time()
    for proto in protocols:
        cfg = PROTOCOLS[proto]
        for inst in instances:
            for strat in STRATEGIES:
                for seed in seeds:
                    rec = run_one(strat, inst, cfg, seed, args.enforce_time)
                    rec["protocol"] = proto
                    rows.append(rec)
                    n += 1
                    if n % 25 == 0 or n == total:
                        print(f"[{n}/{total}] {proto} {inst.name} {STRATEGY_MAP[strat]} seed={seed} "
                              f"cost={rec['cost_km']:.3f} evals={rec['evals_actual']} "
                              f"t={rec['runtime_sec']:.3f}s", flush=True)

    df = pd.DataFrame(rows)
    prefix = args.out_prefix or f"{args.tag}_{args.instances}_{'enforced' if args.enforce_time else 'stockmode'}_{'_'.join(str(s) for s in seeds)}"
    raw_path = ROOT / "audit" / "results" / f"raw_runs_{prefix}.csv"
    df.to_csv(raw_path, index=False)
    summary = summarize(df, protocols)
    summary_path = ROOT / "audit" / "results" / f"summary_{prefix}.csv"
    summary.to_csv(summary_path, index=False)
    paired = paired_stats(df, protocols)
    paired_path = ROOT / "audit" / "results" / f"paired_{prefix}.csv"
    paired.to_csv(paired_path, index=False)

    print("\n=== SUMMARY (independent) ===")
    print(summary.to_string(index=False))
    print("\n=== PAIRED (negative delta = first method has lower distance) ===")
    print(paired.to_string(index=False))
    print(f"\nRuns: {len(df)} in {time.time()-t_start:.1f}s")
    print(f"wrote {raw_path}\nwrote {summary_path}\nwrote {paired_path}")


if __name__ == "__main__":
    main()
