"""
Runnable Slice: T1 Multi-Criteria Motorbike Route Optimization.
Executes candidate path generation, Monte Carlo stochastic evaluation, Pareto filtering,
and archetype labeling on the real HCMC Binh Thanh subgraph.
Outputs structured JSON and a publication-quality route comparison figure.
"""

from __future__ import annotations

import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

from src.routing.multicriteria_router import MultiCriteriaRouter


def run_t1_slice(
    origin_node: int | None = 1497276525,
    dest_node: int | None = 5337055581,
    radius_km: float = 1.2,
    output_json: str = "results/t1_routes_sample.json",
    output_fig: str = "results/figures/t1_pareto_routes.png",
):
    print("=" * 70)
    print("HOTWAY T1 MULTI-CRITERIA MOTORBIKE ROUTING RUNNABLE SLICE")
    print("=" * 70)

    print(f"[*] Loading HCMC subgraph (radius {radius_km} km around Binh Thanh depot)...")
    router = MultiCriteriaRouter.from_hcmc_subgraph(radius_km=radius_km)
    G = router.graph
    print(f"[+] Subgraph loaded: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges (Strongly Connected).")

    nodes = list(G.nodes())
    if origin_node is None or dest_node is None:
        # Pick two nodes separated by distance across the subgraph
        lats = [G.nodes[n]["y"] for n in nodes]
        min_lat, max_lat = min(lats), max(lats)
        origin_node = [n for n in nodes if G.nodes[n]["y"] == min_lat][0]
        dest_node = [n for n in nodes if G.nodes[n]["y"] == max_lat][0]

    orig_data = G.nodes[origin_node]
    dest_data = G.nodes[dest_node]
    print(f"[*] Origin node {origin_node}: lat={orig_data['y']:.5f}, lon={orig_data['x']:.5f}")
    print(f"[*] Destination node {dest_node}: lat={dest_data['y']:.5f}, lon={dest_data['x']:.5f}")

    print("\n[*] Generating candidate paths and evaluating Pareto multi-criteria...")
    labeled_routes = router.select_four_labeled_routes(origin_node, dest_node, k_candidates=20)

    if not labeled_routes:
        print("[!] Error: No candidate paths found between the selected nodes.")
        return

    print("\n" + "=" * 88)
    print(f"{'Archetype':<26} | {'Dist (m)':<9} | {'Exp (min)':<9} | {'p90 (min)':<9} | {'Turns (L)':<9} | {'Alley %':<7} | {'Signals':<7}")
    print("-" * 88)

    serializable_results = {
        "metadata": {
            "origin": {"node_id": origin_node, "lat": orig_data["y"], "lon": orig_data["x"]},
            "destination": {"node_id": dest_node, "lat": dest_data["y"], "lon": dest_data["x"]},
            "subgraph_nodes": G.number_of_nodes(),
            "subgraph_edges": G.number_of_edges(),
            "monte_carlo_runs": 200,
        },
        "routes": {},
    }

    for key, route in labeled_routes.items():
        turns_str = f"{route['num_turns']} ({route['num_left_turns']})"
        print(
            f"{route['label']:<26} | "
            f"{route['distance_m']:<9.1f} | "
            f"{route['expected_time_min']:<9.2f} | "
            f"{route['p90_time_min']:<9.2f} | "
            f"{turns_str:<9} | "
            f"{route['alley_ratio_pct']:<7.1f} | "
            f"{route['num_signals']:<7}"
        )
        serializable_results["routes"][key] = {
            "key": key,
            "label": route["label"],
            "tag": route["tag"],
            "distance_m": route["distance_m"],
            "expected_time_min": route["expected_time_min"],
            "p90_time_min": route["p90_time_min"],
            "num_turns": route["num_turns"],
            "num_left_turns": route["num_left_turns"],
            "alley_ratio_pct": route["alley_ratio_pct"],
            "num_signals": route["num_signals"],
            "ease_penalty_score": route["ease_penalty_score"],
            "path_nodes": route["path_nodes"],
            "coordinates": route["coords"],  # List of [lat, lon]
        }

    print("=" * 88)

    # Save JSON
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(serializable_results, f, indent=2, ensure_ascii=False)
    print(f"\n[+] Saved route data to: {output_json}")

    # Plot map
    print(f"[*] Rendering comparison visualization to: {output_fig}...")
    os.makedirs(os.path.dirname(output_fig), exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 8), dpi=200)

    # 1. Plot background network
    for u, v in G.edges():
        u_pt = (G.nodes[u]["x"], G.nodes[u]["y"])
        v_pt = (G.nodes[v]["x"], G.nodes[v]["y"])
        ax.plot([u_pt[0], v_pt[0]], [u_pt[1], v_pt[1]], color="#E2E8F0", linewidth=0.7, zorder=1)

    # Colors and styles for 4 routes
    styles = {
        "fastest": {"color": "#10B981", "lw": 3.2, "ls": "-", "label": f"Fastest Expected ({labeled_routes['fastest']['expected_time_min']} min)"},
        "shortest": {"color": "#3B82F6", "lw": 2.6, "ls": "--", "label": f"Shortest Distance ({labeled_routes['shortest']['distance_m']:.0f} m)"},
        "stable": {"color": "#F59E0B", "lw": 2.4, "ls": "-.", "label": f"Most Stable p90 ({labeled_routes['stable']['p90_time_min']} min)"},
        "easiest": {"color": "#8B5CF6", "lw": 2.0, "ls": ":", "label": f"Easiest Ride (Score {labeled_routes['easiest']['ease_penalty_score']:.1f})"},
    }

    # Plot routes in order
    for key in ["easiest", "stable", "shortest", "fastest"]:
        if key in labeled_routes:
            coords = labeled_routes[key]["coords"]
            lons = [pt[1] for pt in coords]
            lats = [pt[0] for pt in coords]
            st = styles[key]
            ax.plot(lons, lats, color=st["color"], linewidth=st["lw"], linestyle=st["ls"], label=st["label"], alpha=0.85, zorder=3)

    # Plot Origin & Destination
    ax.scatter([orig_data["x"]], [orig_data["y"]], color="#059669", s=110, edgecolor="black", linewidth=1.5, zorder=5, label=f"Origin ({origin_node})")
    ax.scatter([dest_data["x"]], [dest_data["y"]], color="#DC2626", s=110, marker="s", edgecolor="black", linewidth=1.5, zorder=5, label=f"Destination ({dest_node})")

    ax.set_title("HotWAY T1: Multi-Criteria Motorbike Route Optimization\n(Binh Thanh District Subgraph - 568 Nodes)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Longitude (°E)", fontsize=10)
    ax.set_ylabel("Latitude (°N)", fontsize=10)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(loc="upper left", frameon=True, framealpha=0.92, fontsize=9)
    plt.tight_layout()

    plt.savefig(output_fig, dpi=200)
    plt.close()
    print(f"[+] Visualization saved successfully: {output_fig}")
    print("[+] T1 Slice execution completed successfully.\n")


if __name__ == "__main__":
    run_t1_slice()
