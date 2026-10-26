"""
Benchmark Script for T2 Multi-Stop Motorbike VRPTW Solvers (Gate G3).
Evaluates Greedy, Clarke-Wright+LS, and Google OR-Tools across 10 instances on matrix_standard.npz.
Evaluates both deterministic metrics and stochastic robustness under rain.
Outputs structured JSON and comparison figure.
"""

from __future__ import annotations

import json
import os
import sys
import time
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.baselines.vrptw_solvers import (
    VRPTWInstance,
    GreedyVRPTWSolver,
    ClarkeWrightLSSolver,
    OrToolsVRPTWSolver,
    evaluate_solution_stochastic,
)


def run_t2_benchmark(
    matrix_path: str = "data/matrix_standard.npz",
    output_json: str = "results/baselines/t2_vrptw_benchmark.json",
    output_fig: str = "results/figures/t2_solver_comparison.png",
    seed: int = 2026,
):
    print("=" * 80)
    print("HOTWAY T2: MULTI-STOP MOTORBIKE VRPTW SOLVER BENCHMARK")
    print("=" * 80)

    # Load matrix
    m = np.load(matrix_path)
    full_dist = m["dist_matrix"]  # (401, 401) meters
    full_time = m["time_matrix"]  # (401, 401) minutes

    rng = np.random.default_rng(seed)

    # Define 10 benchmark instances: (num_orders, num_vehicles, capacity)
    configs = [
        # Small instances (15 orders)
        (15, 3, 8),
        (15, 3, 8),
        (15, 3, 8),
        (15, 3, 8),
        # Medium instances (25 orders)
        (25, 4, 8),
        (25, 4, 8),
        (25, 4, 8),
        (25, 4, 8),
        # Large surge instances (40 orders)
        (40, 5, 8),
        (40, 5, 8),
    ]

    instances: List[VRPTWInstance] = []
    for idx, (N, K, Q) in enumerate(configs):
        # Sample N random customers from pool (indices 1..400)
        cust_indices = rng.choice(np.arange(1, 401), size=N, replace=False)
        sub_indices = [0] + list(cust_indices)

        sub_dist = full_dist[np.ix_(sub_indices, sub_indices)]
        sub_time = full_time[np.ix_(sub_indices, sub_indices)]

        # Generate realistic soft time windows and order ages
        time_windows = []
        order_ages = []
        for _ in range(N):
            ready = float(rng.uniform(0.0, 15.0))
            duration = float(rng.uniform(30.0, 55.0))
            deadline = ready + duration
            time_windows.append((ready, deadline))
            age = float(rng.uniform(5.0, 75.0))
            order_ages.append(age)

        inst = VRPTWInstance(
            instance_id=f"inst_{idx + 1:02d}_N{N}_K{K}",
            num_orders=N,
            num_vehicles=K,
            capacity=Q,
            dist_matrix=sub_dist,
            time_matrix=sub_time,
            time_windows=time_windows,
            order_ages=order_ages,
            service_time_min=3.0,
        )
        instances.append(inst)

    solvers = {
        "Greedy Urgency": GreedyVRPTWSolver(),
        "Clarke-Wright + LS": ClarkeWrightLSSolver(),
        "Google OR-Tools": OrToolsVRPTWSolver(),
    }

    benchmark_records = []
    solver_aggregates: Dict[str, Dict[str, List[float]]] = {
        s: {
            "dist_km": [],
            "duration_min": [],
            "avg_wait_min": [],
            "late_rate_pct": [],
            "backlog_penalty": [],
            "solve_time_sec": [],
            "stoch_late_rate": [],
        }
        for s in solvers
    }

    print(f"\n[*] Running 3 solvers across {len(instances)} VRPTW instances...")
    print("-" * 88)
    print(f"{'Instance':<16} | {'Solver':<18} | {'Dist(km)':<8} | {'Wait(m)':<8} | {'Late%':<6} | {'RainLate%':<9} | {'Time(s)':<7}")
    print("-" * 88)

    for inst in instances:
        inst_record = {"instance_id": inst.instance_id, "num_orders": inst.num_orders, "results": {}}

        for s_name, solver in solvers.items():
            res = solver.solve(inst)

            # Evaluate under stochastic rain simulation
            sim = evaluate_solution_stochastic(
                res["routes"], inst, num_mc_runs=25, rain_factor=1.40, noise_sigma=0.20
            )

            res["stochastic_simulation"] = sim

            # Record
            solver_aggregates[s_name]["dist_km"].append(res["total_dist_km"])
            solver_aggregates[s_name]["duration_min"].append(res["total_route_time_min"])
            solver_aggregates[s_name]["avg_wait_min"].append(res["avg_wait_min"])
            solver_aggregates[s_name]["late_rate_pct"].append(res["late_rate_pct"])
            solver_aggregates[s_name]["backlog_penalty"].append(res["backlog_penalty"])
            solver_aggregates[s_name]["solve_time_sec"].append(res["solve_time_sec"])
            solver_aggregates[s_name]["stoch_late_rate"].append(sim["stoch_late_rate_mean"])

            inst_record["results"][s_name] = res

            print(
                f"{inst.instance_id:<16} | "
                f"{s_name:<18} | "
                f"{res['total_dist_km']:<8.1f} | "
                f"{res['avg_wait_min']:<8.1f} | "
                f"{res['late_rate_pct']:<6.1f} | "
                f"{sim['stoch_late_rate_mean']:<9.1f} | "
                f"{res['solve_time_sec']:<7.3f}"
            )

        benchmark_records.append(inst_record)
        print("-" * 88)

    # Compute overall summary
    summary = {}
    for s_name, data in solver_aggregates.items():
        summary[s_name] = {
            "mean_dist_km": float(round(np.mean(data["dist_km"]), 2)),
            "mean_duration_min": float(round(np.mean(data["duration_min"]), 2)),
            "mean_wait_min": float(round(np.mean(data["avg_wait_min"]), 2)),
            "mean_late_rate_pct": float(round(np.mean(data["late_rate_pct"]), 1)),
            "mean_stoch_late_rate_pct": float(round(np.mean(data["stoch_late_rate"]), 1)),
            "mean_backlog_penalty": float(round(np.mean(data["backlog_penalty"]), 2)),
            "mean_solve_time_sec": float(round(np.mean(data["solve_time_sec"]), 4)),
        }

    print("\n" + "=" * 80)
    print("OVERALL SOLVER SUMMARY (AVERAGE ACROSS 10 INSTANCES)")
    print("=" * 80)
    for s_name, stats in summary.items():
        print(f"[{s_name}]")
        print(f"  - Distance:          {stats['mean_dist_km']:.2f} km")
        print(f"  - Route Duration:    {stats['mean_duration_min']:.2f} min")
        print(f"  - Customer Wait:     {stats['mean_wait_min']:.2f} min")
        print(f"  - Late Rate (Dry):   {stats['mean_late_rate_pct']:.1f}%")
        print(f"  - Late Rate (Rain):  {stats['mean_stoch_late_rate_pct']:.1f}%")
        print(f"  - Backlog Penalty:   {stats['mean_backlog_penalty']:.2f}")
        print(f"  - Compute Time:      {stats['mean_solve_time_sec']:.4f} s")
    print("=" * 80)

    # Save JSON
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "instances": benchmark_records}, f, indent=2, ensure_ascii=False)
    print(f"\n[+] Saved T2 benchmark results to: {output_json}")

    # Generate Publication Figure
    os.makedirs(os.path.dirname(output_fig), exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), dpi=200)

    solver_names = list(summary.keys())
    x = np.arange(len(solver_names))
    colors = ["#94A3B8", "#3B82F6", "#10B981"]

    # 1. Total Distance (km)
    dists = [summary[s]["mean_dist_km"] for s in solver_names]
    axes[0].bar(x, dists, color=colors, width=0.55, edgecolor="black", linewidth=0.8)
    axes[0].set_title("Total Fleet Distance (km)\n[Lower is Better]", fontsize=11, fontweight="bold")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(solver_names, fontsize=9)
    axes[0].set_ylabel("Distance (km)", fontsize=10)
    axes[0].grid(axis="y", linestyle=":", alpha=0.5)
    for i, v in enumerate(dists):
        axes[0].text(i, v + 0.5, f"{v:.1f}", ha="center", fontsize=9, fontweight="bold")

    # 2. Late Rate: Dry vs Rain (%)
    dry_late = [summary[s]["mean_late_rate_pct"] for s in solver_names]
    rain_late = [summary[s]["mean_stoch_late_rate_pct"] for s in solver_names]
    w = 0.35
    axes[1].bar(x - w / 2, dry_late, width=w, label="Dry Weather (Base)", color="#60A5FA", edgecolor="black", linewidth=0.8)
    axes[1].bar(x + w / 2, rain_late, width=w, label="Rain Inflation (η=1.40)", color="#F59E0B", edgecolor="black", linewidth=0.8)
    axes[1].set_title("Soft Window Late Rate (%)\n[Robustness under Rain]", fontsize=11, fontweight="bold")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(solver_names, fontsize=9)
    axes[1].set_ylabel("Late Deliveries (%)", fontsize=10)
    axes[1].grid(axis="y", linestyle=":", alpha=0.5)
    axes[1].legend(fontsize=8, loc="upper left")

    # 3. Customer Wait Time & Compute Latency
    waits = [summary[s]["mean_wait_min"] for s in solver_names]
    axes[2].bar(x, waits, color=colors, width=0.55, edgecolor="black", linewidth=0.8)
    axes[2].set_title("Average Customer Wait Time (min)\n[Lower is Better]", fontsize=11, fontweight="bold")
    axes[2].set_xticks(x)
    axes[2].set_xticklabels(solver_names, fontsize=9)
    axes[2].set_ylabel("Wait Time (minutes)", fontsize=10)
    axes[2].grid(axis="y", linestyle=":", alpha=0.5)
    for i, v in enumerate(waits):
        axes[2].text(i, v + 0.5, f"{v:.1f}m", ha="center", fontsize=9, fontweight="bold")

    plt.tight_layout()
    plt.savefig(output_fig, dpi=200)
    plt.close()
    print(f"[+] Saved comparison figure to: {output_fig}\n")


if __name__ == "__main__":
    run_t2_benchmark()
