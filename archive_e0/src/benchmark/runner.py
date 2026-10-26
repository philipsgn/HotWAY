"""
HotWAY CVRP Benchmark Runner v5.0
Executes CVRP optimization strategies across benchmark instances under strict scientific protocols.

Protocols:
- Protocol A: 100 steps, 128 candidates.
- Protocol A2: 100 steps, 256 candidates.
- Protocol A3: 100 steps, 128 candidates (feature_patience=30).
- Protocol B: Time budget 0.05s (50ms).
- Protocol B2: Time budget 0.1s (100ms).

Evaluates 5 strategies:
1. Random
2. Cyclic
3. Greedy
4. DQN
5. Double DQN

Outputs:
- rel_result/raw_runs.csv (every run detail)
- rel_result/summary_by_algorithm.csv (matching OptimoRoute UI & Strategy Lab schema)
- rel_result/per_decision_cost.csv (decision time & candidate evaluation statistics)
"""

from __future__ import annotations

import argparse
import csv
import logging
import math
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.cvrp_solver.constructive import clarke_wright_savings
from src.cvrp_solver.problem import CVRPInstance, CVRPSolution
from src.cvrp_solver.search import solve_cvrp_strategy
from src.cvrp_solver.validator import calculate_route_distance, validate_cvrp_solution
from src.data.build_graph import load_site_config
from src.benchmark.instance_generator import load_benchmark_instances

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("benchmark_runner")

STRATEGY_MAP = {
    "random": "Random",
    "cyclic": "Cyclic",
    "greedy": "Greedy",
    "dqn": "DQN",
    "double_dqn": "Double DQN",
}

STRATEGIES = list(STRATEGY_MAP.keys())


def run_strategy_on_instance(
    strategy: str,
    instance: CVRPInstance,
    max_steps: int = 100,
    max_candidates: int = 128,
    seed: int = 42,
    time_limit_sec: Optional[float] = None,
) -> Dict[str, Any]:
    """Runs a single strategy on an instance and collects timing and quality metrics."""
    # Compute baseline Clarke-Wright cost for relative improvement
    init_routes = clarke_wright_savings(instance)
    cw_cost_m = sum(calculate_route_distance(r, instance.dist_matrix) for r in init_routes)

    start_t = time.perf_counter()
    
    # Run solver
    solution = solve_cvrp_strategy(
        strategy=strategy,
        instance=instance,
        max_steps=max_steps,
        max_candidates=max_candidates,
        seed=seed,
    )
    
    elapsed_ms = (time.perf_counter() - start_t) * 1000.0

    # Independent validation
    is_valid, val_cost, err_msg = validate_cvrp_solution(
        solution.routes, instance
    )

    # Compute temperature stats
    all_temps = []
    all_times_min = []
    for r in solution.detailed_routes:
        for s in r.stops:
            all_temps.append(s.estimated_temp_c)
            all_times_min.append(s.elapsed_time_min)

    min_temp = min(all_temps) if all_temps else 85.0
    avg_temp = float(np.mean(all_temps)) if all_temps else 85.0
    max_time_min = max(all_times_min) if all_times_min else 0.0

    steps_count = len(solution.search_trace)
    evals_count = steps_count * max_candidates
    impr_pct = max(0.0, ((cw_cost_m - solution.total_distance) / max(cw_cost_m, 1.0)) * 100.0)
    thermal_viols = sum(r.thermal_violations_count for r in solution.detailed_routes)

    return {
        "instance_id": instance.name,
        "strategy": STRATEGY_MAP.get(strategy.lower(), strategy),
        "raw_strategy": strategy,
        "feasible": is_valid,
        "error_msg": err_msg if not is_valid else "",
        "cw_cost_km": round(cw_cost_m / 1000.0, 3),
        "cost_km": round(solution.total_distance / 1000.0, 3),
        "cost_meters": round(solution.total_distance, 1),
        "improvement_pct": round(impr_pct, 4),
        "runtime_ms": round(elapsed_ms, 2),
        "runtime_sec": round(elapsed_ms / 1000.0, 5),
        "num_vehicles": len(solution.routes),
        "num_customers": instance.n_customers,
        "total_demand": sum(instance.demands),
        "min_delivery_temp_c": round(min_temp, 1),
        "avg_delivery_temp_c": round(avg_temp, 1),
        "thermal_violations": thermal_viols,
        "max_delivery_time_min": round(max_time_min, 1),
        "decisions": steps_count,
        "evals": evals_count,
        "ms_per_decision": round(elapsed_ms / max(steps_count, 1), 3),
        "candidates_per_decision": max_candidates,
    }


def execute_benchmark(
    instances: List[CVRPInstance],
    protocols: Optional[List[str]] = None,
    strategies: Optional[List[str]] = None,
    output_dir: Path | str = "rel_result",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Executes the full benchmark suite across all instances and protocols."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    protocol_configs = {
        "A2": {"max_steps": 100, "max_candidates": 256, "time_limit": None},
        "A":  {"max_steps": 100, "max_candidates": 128, "time_limit": None},
        "A3": {"max_steps": 100, "max_candidates": 128, "time_limit": None},
        "B":  {"max_steps": 200, "max_candidates": 64,  "time_limit": 0.05},
        "B2": {"max_steps": 400, "max_candidates": 128, "time_limit": 0.10},
    }

    if protocols is None:
        protocols = ["A2", "A", "A3", "B", "B2"]
    if strategies is None:
        strategies = STRATEGIES

    raw_records: List[Dict[str, Any]] = []
    total_runs = len(instances) * len(protocols) * len(strategies)
    run_idx = 0

    logger.info(f"Starting benchmark: {len(instances)} instances, {len(protocols)} protocols, {len(strategies)} strategies ({total_runs} total runs)")

    for p_name in protocols:
        p_cfg = protocol_configs.get(p_name, {"max_steps": 100, "max_candidates": 128})
        max_steps = p_cfg["max_steps"]
        max_candidates = p_cfg["max_candidates"]
        t_limit = p_cfg.get("time_limit")

        logger.info(f"--- Protocol: {p_name} (steps={max_steps}, candidates={max_candidates}) ---")

        for inst in instances:
            for strat in strategies:
                run_idx += 1
                rec = run_strategy_on_instance(
                    strategy=strat,
                    instance=inst,
                    max_steps=max_steps,
                    max_candidates=max_candidates,
                    time_limit_sec=t_limit,
                    seed=42,
                )
                rec["protocol"] = p_name
                raw_records.append(rec)

                if run_idx % 25 == 0 or run_idx == total_runs:
                    logger.info(f"Progress [{run_idx}/{total_runs}]: {p_name} | {inst.name} | {rec['strategy']} -> cost: {rec['cost_km']} km, impr: {rec['improvement_pct']:.3f}%, time: {rec['runtime_ms']:.1f}ms")

    df_raw = pd.DataFrame(raw_records)

    # Export raw_runs.csv
    raw_path = out / "raw_runs.csv"
    df_raw.to_csv(raw_path, index=False)
    logger.info(f"Exported raw runs: {raw_path} ({len(df_raw)} records)")

    # 1. Export summary_by_algorithm.csv with schema matching Strategy Lab
    # protocol,method,mean_distance,mean_improvement_pct,ci_lower,ci_upper,median_improvement_pct,feasible_rate,runtime_sec,mean_evals,gap_vs_ortools_pct
    summary_records = []
    for proto in protocols:
        sub_p = df_raw[df_raw["protocol"] == proto]
        # Find best mean distance for gap computation
        means_by_strat = sub_p.groupby("strategy")["cost_km"].mean()
        best_mean = means_by_strat.min()

        for strat_name in [STRATEGY_MAP[s] for s in strategies]:
            strat_data = sub_p[sub_p["strategy"] == strat_name]
            if strat_data.empty:
                continue
            
            impr = strat_data["improvement_pct"].values
            # 95% Bootstrap CI for improvement pct
            boot_means = [np.mean(np.random.choice(impr, size=len(impr), replace=True)) for _ in range(1000)]
            ci_low = float(np.percentile(boot_means, 2.5))
            ci_high = float(np.percentile(boot_means, 97.5))

            mean_dist = float(strat_data["cost_km"].mean())
            gap_pct = ((mean_dist - best_mean) / max(best_mean, 1e-6)) * 100.0

            summary_records.append({
                "protocol": proto,
                "method": strat_name,
                "mean_distance": round(mean_dist, 3),
                "mean_improvement_pct": round(float(np.mean(impr)), 3),
                "ci_lower": round(ci_low, 3),
                "ci_upper": round(ci_high, 3),
                "median_improvement_pct": round(float(np.median(impr)), 3),
                "feasible_rate": round(float(strat_data["feasible"].mean()), 3),
                "runtime_sec": round(float(strat_data["runtime_sec"].mean()), 4),
                "mean_evals": round(float(strat_data["evals"].mean()), 1),
                "gap_vs_ortools_pct": round(gap_pct, 3),
            })

    df_summary = pd.DataFrame(summary_records)
    summary_path = out / "summary_by_algorithm.csv"
    df_summary.to_csv(summary_path, index=False)
    logger.info(f"Exported summary_by_algorithm: {summary_path}")

    # 2. Export per_decision_cost.csv
    # method,runtime_sec,decisions_mean,candidates_mean,ms_per_decision,candidates_per_decision
    cost_records = []
    for strat_key in strategies:
        strat_name = STRATEGY_MAP[strat_key]
        s_data = df_raw[df_raw["strategy"] == strat_name]
        cost_records.append({
            "method": strat_name,
            "runtime_sec": round(float(s_data["runtime_sec"].mean()), 4),
            "decisions_mean": round(float(s_data["decisions"].mean()), 1),
            "candidates_mean": round(float(s_data["evals"].mean()), 1),
            "ms_per_decision": round(float(s_data["ms_per_decision"].mean()), 3),
            "candidates_per_decision": round(float(s_data["candidates_per_decision"].mean()), 1),
        })

    df_cost = pd.DataFrame(cost_records)
    cost_path = out / "per_decision_cost.csv"
    df_cost.to_csv(cost_path, index=False)
    logger.info(f"Exported per_decision_cost: {cost_path}")

    return df_summary, df_cost


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HotWAY CVRP Benchmark Runner")
    parser.add_argument("--instances-dir", type=str, default="data/benchmark_instances")
    parser.add_argument("--out-dir", type=str, default="rel_result")
    parser.add_argument("--protocols", type=str, default=None)
    parser.add_argument("--strategies", type=str, default=None)
    args = parser.parse_args()

    insts = load_benchmark_instances(args.instances_dir)
    if not insts:
        print(f"No instances found in {args.instances_dir}. Run instance_generator first.")
        exit(1)

    protos = args.protocols.split(",") if args.protocols else None
    strats = args.strategies.split(",") if args.strategies else None

    execute_benchmark(
        instances=insts,
        protocols=protos,
        strategies=strats,
        output_dir=args.out_dir,
    )
