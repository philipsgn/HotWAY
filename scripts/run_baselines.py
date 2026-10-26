"""
Benchmark and Hyperparameter Grid Search Runner for Baselines (Gate G3).
Tunes baseline parameters on the Validation Split (5 seeds),
evaluates best configurations on Frozen Test Split (5 seeds) and OOD Split (5 seeds),
and outputs raw CSVs and summary JSONs with Bootstrap CI.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from src.envs.dispatch_env import DispatchEnv
from src.baselines.rule_baselines import (
    BaseDispatchPolicy,
    ImmediateDispatchPolicy,
    PeriodicDispatchPolicy,
    BatchSizeDispatchPolicy,
    AgeThresholdDispatchPolicy,
)


def evaluate_policy_on_seeds(
    policy: BaseDispatchPolicy,
    seeds: List[int],
    matrix_path: str = "data/matrix_standard.npz",
    address_pool_path: str = "data/address_pool_standard.json",
    is_ood: bool = False,
) -> List[Dict[str, Any]]:
    """Runs a policy across multiple seeds and returns individual run metrics."""
    runs = []
    for seed in seeds:
        t0 = time.perf_counter()
        env = DispatchEnv(
            matrix_path=matrix_path,
            address_pool_path=address_pool_path,
            enable_event_logging=False,
        )
        obs, _ = env.reset(seed=seed)
        terminated = False
        truncated = False
        decision_latencies = []

        while not (terminated or truncated):
            t_dec0 = time.perf_counter()
            act = policy.select_action(env, obs)
            decision_latencies.append((time.perf_counter() - t_dec0) * 1000.0)

            obs, _, terminated, truncated, _ = env.step(act)

        run_time_sec = time.perf_counter() - t0
        metrics = env.get_metrics()
        metrics["policy"] = policy.name
        metrics["seed"] = seed
        metrics["is_ood"] = is_ood
        metrics["run_time_sec"] = run_time_sec
        metrics["mean_decision_latency_ms"] = float(np.mean(decision_latencies)) if decision_latencies else 0.0

        # Utility U = -W - lambda * Lateness (lambda = 2.0)
        metrics["utility_score"] = float(-metrics["mean_wait_min"] - 2.0 * metrics["mean_lateness_min"])
        runs.append(metrics)

    return runs


def bootstrap_ci_mean(data: np.ndarray, n_boot: int = 2000, ci: float = 0.95) -> Tuple[float, float]:
    """Computes non-parametric bootstrap confidence interval for the mean."""
    if len(data) <= 1:
        return float(data[0]), float(data[0])
    rng = np.random.default_rng(2026)
    boot_means = [float(np.mean(rng.choice(data, size=len(data), replace=True))) for _ in range(n_boot)]
    alpha = (1.0 - ci) / 2.0
    return float(np.percentile(boot_means, 100.0 * alpha)), float(np.percentile(boot_means, 100.0 * (1.0 - alpha)))


def run_gate3_baseline_tuning() -> Dict[str, Any]:
    print("=== STARTING GATE G3 BASELINE GRID SEARCH & EVALUATION ===")
    out_dir = Path("results/baselines")
    out_dir.mkdir(parents=True, exist_ok=True)

    val_seeds = [2036, 2037, 2038, 2039, 2040]
    test_seeds = [2041, 2042, 2043, 2044, 2045]
    ood_seeds = [2046, 2047, 2048, 2049, 2050]

    # 1. Grid Search Candidates on Validation Split
    print("\n--- 1. Tuning Candidates on Validation Set (5 seeds) ---")

    # Immediate
    immed_runs = evaluate_policy_on_seeds(ImmediateDispatchPolicy(capacity=4), val_seeds)
    best_immediate = ImmediateDispatchPolicy(capacity=4)

    # Periodic T in [5, 8, 10, 12, 15, 20, 25]
    t_candidates = [5.0, 8.0, 10.0, 12.0, 15.0, 20.0, 25.0]
    best_t_score = -float("inf")
    best_t = 12.0
    periodic_grid_results = []
    for t_val in t_candidates:
        pol = PeriodicDispatchPolicy(interval_min=t_val, capacity=4)
        runs = evaluate_policy_on_seeds(pol, val_seeds)
        mean_u = float(np.mean([r["utility_score"] for r in runs]))
        mean_w = float(np.mean([r["mean_wait_min"] for r in runs]))
        periodic_grid_results.append({"T": t_val, "utility": mean_u, "mean_wait": mean_w})
        print(f"Periodic T={t_val:4.1f}m -> Val Utility: {mean_u:6.2f}, Mean Wait: {mean_w:5.2f}m")
        if mean_u > best_t_score:
            best_t_score = mean_u
            best_t = t_val

    best_periodic = PeriodicDispatchPolicy(interval_min=best_t, capacity=4)
    best_periodic.name = f"Periodic (T={best_t:.1f}m)"
    print(f"-> Best Periodic: T={best_t} min")

    # Batch k in [1, 2, 3, 4]
    k_candidates = [1, 2, 3, 4]
    best_k_score = -float("inf")
    best_k = 3
    for k_val in k_candidates:
        pol = BatchSizeDispatchPolicy(batch_k=k_val, capacity=4)
        runs = evaluate_policy_on_seeds(pol, val_seeds)
        mean_u = float(np.mean([r["utility_score"] for r in runs]))
        mean_w = float(np.mean([r["mean_wait_min"] for r in runs]))
        print(f"Batch k={k_val}       -> Val Utility: {mean_u:6.2f}, Mean Wait: {mean_w:5.2f}m")
        if mean_u > best_k_score:
            best_k_score = mean_u
            best_k = k_val

    best_batch = BatchSizeDispatchPolicy(batch_k=best_k, capacity=4)
    best_batch.name = f"BatchSize (k={best_k})"
    print(f"-> Best BatchSize: k={best_k}")

    # Age Threshold theta in [10, 15, 20, 25, 30, 35]
    theta_candidates = [10.0, 15.0, 20.0, 25.0, 30.0, 35.0]
    best_theta_score = -float("inf")
    best_theta = 20.0
    for th in theta_candidates:
        pol = AgeThresholdDispatchPolicy(theta_age_min=th, capacity=4)
        runs = evaluate_policy_on_seeds(pol, val_seeds)
        mean_u = float(np.mean([r["utility_score"] for r in runs]))
        mean_w = float(np.mean([r["mean_wait_min"] for r in runs]))
        print(f"AgeThreshold th={th:4.1f}m -> Val Utility: {mean_u:6.2f}, Mean Wait: {mean_w:5.2f}m")
        if mean_u > best_theta_score:
            best_theta_score = mean_u
            best_theta = th

    best_age_threshold = AgeThresholdDispatchPolicy(theta_age_min=best_theta, capacity=4)
    best_age_threshold.name = f"AgeThreshold (theta={best_theta:.1f}m)"
    print(f"-> Best AgeThreshold: theta={best_theta} min")

    # 2. Frozen Evaluation on Test Set (5 seeds)
    print("\n--- 2. Evaluating Best Baselines on Frozen Test Set (5 seeds) ---")
    best_policies = [
        best_immediate,
        best_periodic,
        best_batch,
        best_age_threshold,
    ]

    all_test_runs = []
    for pol in best_policies:
        runs = evaluate_policy_on_seeds(pol, test_seeds)
        all_test_runs.extend(runs)
        mean_wait = float(np.mean([r["mean_wait_min"] for r in runs]))
        p90 = float(np.mean([r["p90_wait_min"] for r in runs]))
        lateness = float(np.mean([r["late_rate_pct"] for r in runs]))
        gini = float(np.mean([r["gini_coefficient"] for r in runs]))
        util = float(np.mean([r["fleet_utilization"] for r in runs])) * 100.0
        print(f"TEST | {pol.name:<25}: Wait={mean_wait:5.2f}m, p90={p90:5.2f}m, Late={lateness:4.1f}%, Gini={gini:.3f}, Util={util:4.1f}%")

    # 3. Evaluation on Out-of-Distribution Set (5 seeds)
    print("\n--- 3. Evaluating Best Baselines on Out-of-Distribution Split (5 seeds) ---")
    all_ood_runs = []
    for pol in best_policies:
        runs = evaluate_policy_on_seeds(
            pol,
            ood_seeds,
            matrix_path="data/matrix_ood.npz",
            address_pool_path="data/address_pool_ood.json",
            is_ood=True,
        )
        all_ood_runs.extend(runs)
        mean_wait = float(np.mean([r["mean_wait_min"] for r in runs]))
        p90_surge = float(np.mean([r["p90_surge_wait_min"] for r in runs]))
        print(f"OOD  | {pol.name:<25}: Mean Wait={mean_wait:5.2f}m, Surge p90={p90_surge:5.2f}m")

    # Save raw results
    df_test = pd.DataFrame(all_test_runs)
    df_ood = pd.DataFrame(all_ood_runs)
    df_all = pd.concat([df_test, df_ood], ignore_index=True)

    raw_csv = out_dir / "raw_baseline_runs.csv"
    df_all.to_csv(raw_csv, index=False)
    print(f"\nSaved raw runs to {raw_csv}")

    # Compute Summary Table with Bootstrap CI
    summary_rows = []
    for pol_name in df_test["policy"].unique():
        sub = df_test[df_test["policy"] == pol_name]
        w_vals = sub["mean_wait_min"].to_numpy()
        ci_low, ci_high = bootstrap_ci_mean(w_vals)

        summary_rows.append({
            "policy": pol_name,
            "mean_wait_min": float(np.mean(w_vals)),
            "ci_95_lower": ci_low,
            "ci_95_upper": ci_high,
            "p90_wait_min": float(np.mean(sub["p90_wait_min"])),
            "p95_wait_min": float(np.mean(sub["p95_wait_min"])),
            "late_rate_pct": float(np.mean(sub["late_rate_pct"])),
            "gini_coefficient": float(np.mean(sub["gini_coefficient"])),
            "fleet_utilization_pct": float(np.mean(sub["fleet_utilization"])) * 100.0,
            "total_km": float(np.mean(sub["total_km"])),
            "decision_latency_ms": float(np.mean(sub["mean_decision_latency_ms"])),
        })

    df_summary = pd.DataFrame(summary_rows)
    sum_csv = out_dir / "summary_baseline_test.csv"
    df_summary.to_csv(sum_csv, index=False)
    print(f"Saved summary to {sum_csv}")

    # Save best configs
    best_configs = {
        "best_periodic_T": best_t,
        "best_batch_k": best_k,
        "best_age_threshold_theta": best_theta,
        "val_seeds": val_seeds,
        "test_seeds": test_seeds,
        "ood_seeds": ood_seeds,
    }
    with open(out_dir / "best_baseline_configs.json", "w", encoding="utf-8") as f:
        json.dump(best_configs, f, indent=2)

    return {"summary": summary_rows, "configs": best_configs}


if __name__ == "__main__":
    run_gate3_baseline_tuning()
