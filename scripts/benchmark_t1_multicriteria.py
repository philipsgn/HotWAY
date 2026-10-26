"""
Benchmark Script for T1 Multi-Criteria Motorbike Routing (Gate G3).
Evaluates Pareto optimization and trade-offs across 50 diverse OD pairs in Binh Thanh HCMC.
Outputs structured JSON and publication-quality trade-off figure.
"""

from __future__ import annotations

import json
import os
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.routing.multicriteria_router import MultiCriteriaRouter


def run_t1_benchmark(
    num_pairs: int = 50,
    radius_km: float = 1.2,
    output_json: str = "results/baselines/t1_multicriteria_benchmark.json",
    output_fig: str = "results/figures/t1_pareto_tradeoffs.png",
    seed: int = 2026,
):
    print("=" * 75)
    print(f"HOTWAY T1: MULTI-CRITERIA MOTORBIKE ROUTING BENCHMARK ({num_pairs} OD PAIRS)")
    print("=" * 75)

    router = MultiCriteriaRouter.from_hcmc_subgraph(radius_km=radius_km)
    G = router.graph
    nodes = list(G.nodes())
    print(f"[+] Loaded subgraph: {len(nodes)} nodes, {G.number_of_edges()} edges.")

    # Select 50 diverse OD pairs with Euclidean distance > 800m
    rng = np.random.default_rng(seed)
    selected_pairs = []
    shuffled_nodes = list(nodes)
    rng.shuffle(shuffled_nodes)

    for i in range(len(shuffled_nodes)):
        u = shuffled_nodes[i]
        u_lat, u_lon = G.nodes[u]["y"], G.nodes[u]["x"]
        for j in range(i + 1, len(shuffled_nodes)):
            v = shuffled_nodes[j]
            v_lat, v_lon = G.nodes[v]["y"], G.nodes[v]["x"]
            # approximate distance in meters
            d_lat = (u_lat - v_lat) * 111000.0
            d_lon = (u_lon - v_lon) * 111000.0 * np.cos(np.radians(u_lat))
            dist_m = np.sqrt(d_lat**2 + d_lon**2)
            if 900.0 <= dist_m <= 2400.0:
                if nx.has_path(G, u, v):
                    selected_pairs.append((u, v, dist_m))
                    if len(selected_pairs) >= num_pairs:
                        break
        if len(selected_pairs) >= num_pairs:
            break

    print(f"[+] Selected {len(selected_pairs)} distinct OD pairs with distance 900m - 2400m.")

    results_list = []
    diff_dist_fastest_vs_shortest = []
    diff_time_shortest_vs_fastest = []
    left_turns_fastest = []
    left_turns_easiest = []
    pareto_sizes = []

    for idx, (o, d, straight_dist) in enumerate(selected_pairs):
        labeled = router.select_four_labeled_routes(o, d, k_candidates=15)
        if not labeled:
            continue

        fastest = labeled["fastest"]
        shortest = labeled["shortest"]
        stable = labeled["stable"]
        easiest = labeled["easiest"]

        # Track metrics
        d_fast = fastest["distance_m"]
        d_short = shortest["distance_m"]
        t_fast = fastest["expected_time_min"]
        t_short = shortest["expected_time_min"]

        diff_dist_fastest_vs_shortest.append(d_fast - d_short)
        diff_time_shortest_vs_fastest.append(t_short - t_fast)
        left_turns_fastest.append(fastest["num_left_turns"])
        left_turns_easiest.append(easiest["num_left_turns"])

        # Count Pareto size from candidate paths
        paths = router.generate_candidate_paths(o, d, k_target=15)
        evaluated = [router.evaluate_path(p) for p in paths]
        pareto = router.filter_pareto(evaluated)
        pareto_sizes.append(len(pareto))

        results_list.append({
            "pair_idx": idx,
            "origin": o,
            "destination": d,
            "euclidean_m": float(round(straight_dist, 1)),
            "pareto_size": len(pareto),
            "fastest": {
                "dist_m": fastest["distance_m"],
                "exp_time_min": fastest["expected_time_min"],
                "p90_time_min": fastest["p90_time_min"],
                "left_turns": fastest["num_left_turns"],
                "signals": fastest["num_signals"],
            },
            "shortest": {
                "dist_m": shortest["distance_m"],
                "exp_time_min": shortest["expected_time_min"],
                "p90_time_min": shortest["p90_time_min"],
                "left_turns": shortest["num_left_turns"],
                "signals": shortest["num_signals"],
            },
            "stable": {
                "dist_m": stable["distance_m"],
                "exp_time_min": stable["expected_time_min"],
                "p90_time_min": stable["p90_time_min"],
                "left_turns": stable["num_left_turns"],
                "signals": stable["num_signals"],
            },
            "easiest": {
                "dist_m": easiest["distance_m"],
                "exp_time_min": easiest["expected_time_min"],
                "p90_time_min": easiest["p90_time_min"],
                "left_turns": easiest["num_left_turns"],
                "signals": easiest["num_signals"],
            },
        })

    # Summary Statistics
    summary = {
        "num_pairs_evaluated": len(results_list),
        "avg_pareto_size": float(np.mean(pareto_sizes)),
        "avg_dist_saving_shortest_m": float(np.mean(diff_dist_fastest_vs_shortest)),
        "avg_time_penalty_shortest_min": float(np.mean(diff_time_shortest_vs_fastest)),
        "avg_left_turns_fastest": float(np.mean(left_turns_fastest)),
        "avg_left_turns_easiest": float(np.mean(left_turns_easiest)),
        "avg_left_turn_reduction_pct": float(
            (1.0 - np.mean(left_turns_easiest) / max(1e-3, np.mean(left_turns_fastest))) * 100.0
        ),
    }

    print("\n" + "=" * 75)
    print("BENCHMARK SUMMARY RESULTS (50 OD PAIRS)")
    print("-" * 75)
    print(f"Average Pareto frontier size:          {summary['avg_pareto_size']:.2f} non-dominated routes")
    print(f"Average distance saved by Shortest:    {summary['avg_dist_saving_shortest_m']:.1f} meters")
    print(f"Average time penalty of Shortest:      +{summary['avg_time_penalty_shortest_min']:.2f} minutes")
    print(f"Average left turns (Fastest route):    {summary['avg_left_turns_fastest']:.2f} turns")
    print(f"Average left turns (Easiest route):    {summary['avg_left_turns_easiest']:.2f} turns")
    print(f"Left turn reduction in Easiest route:  {summary['avg_left_turn_reduction_pct']:.1f}% reduction")
    print("=" * 75)

    # Save JSON
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "pairs": results_list}, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved structured benchmark to: {output_json}")

    # Generate Publication Figure
    os.makedirs(os.path.dirname(output_fig), exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=200)

    # Subplot 1: Distance vs Travel Time Trade-off
    d_f = [p["fastest"]["dist_m"] for p in results_list]
    t_f = [p["fastest"]["exp_time_min"] for p in results_list]
    d_s = [p["shortest"]["dist_m"] for p in results_list]
    t_s = [p["shortest"]["exp_time_min"] for p in results_list]
    d_e = [p["easiest"]["dist_m"] for p in results_list]
    t_e = [p["easiest"]["exp_time_min"] for p in results_list]

    ax1.scatter(d_f, t_f, color="#10B981", s=35, alpha=0.8, label="Fastest Expected (Min Time)")
    ax1.scatter(d_s, t_s, color="#3B82F6", s=35, alpha=0.8, marker="^", label="Shortest Distance (Min Distance)")
    ax1.scatter(d_e, t_e, color="#8B5CF6", s=35, alpha=0.8, marker="s", label="Easiest Ride (Min Turns/Signals)")

    for i in range(min(15, len(results_list))):
        ax1.plot([d_s[i], d_f[i]], [t_s[i], t_f[i]], color="#94A3B8", linestyle=":", linewidth=0.8, alpha=0.6)

    ax1.set_title("Distance vs Travel Time Trade-offs (50 OD Pairs)", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Route Distance (meters)", fontsize=10)
    ax1.set_ylabel("Expected Travel Time (minutes)", fontsize=10)
    ax1.grid(True, linestyle=":", alpha=0.5)
    ax1.legend(fontsize=9, loc="upper left")

    # Subplot 2: Left Turn Distribution Comparison
    ax2.hist(
        [left_turns_fastest, left_turns_easiest],
        bins=np.arange(0, max(left_turns_fastest + left_turns_easiest) + 2) - 0.5,
        color=["#10B981", "#8B5CF6"],
        label=["Fastest Route", "Easiest Route (Safety)"],
        rwidth=0.8,
        alpha=0.85,
    )
    ax2.set_title("Left Turns Cutting Opposing Traffic Distribution", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Number of Left Turns per Route", fontsize=10)
    ax2.set_ylabel("Frequency (OD Pairs)", fontsize=10)
    ax2.grid(True, linestyle=":", alpha=0.5)
    ax2.legend(fontsize=9, loc="upper right")

    plt.tight_layout()
    plt.savefig(output_fig, dpi=200)
    plt.close()
    print(f"[+] Saved trade-off figure to: {output_fig}\n")


if __name__ == "__main__":
    run_t1_benchmark()
