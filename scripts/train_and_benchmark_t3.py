"""
Training and Evaluation Pipeline for T3 Adaptive Motorbike Routing (Gate G4).
Trains Candidate Edge-Scoring DQN and benchmarks against Static and Dynamic Dijkstra.
Outputs model checkpoint, JSON results, and publication-quality figures.
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
import scipy.stats as stats
import torch

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.envs.adaptive_routing_env import AdaptiveRoutingEnv
from src.traffic.provider import SyntheticProvider
from src.agents.candidate_edge_dqn import (
    EdgeScoringDQNAgent,
    extract_candidate_edge_features,
)
from src.agents.baseline_policies import (
    StaticDijkstraPolicy,
    DynamicDijkstraPolicy,
)


def run_training_and_benchmark(
    num_train_episodes: int = 250,
    num_eval_episodes: int = 30,
    model_save_path: str = "results/t3_edge_dqn_model.pt",
    metrics_json_path: str = "results/t3_training_metrics.json",
    comparison_json_path: str = "results/t3_policy_comparison.json",
    fig_train_path: str = "results/figures/t3_training_curves.png",
    fig_comp_path: str = "results/figures/t3_policy_benchmark.png",
    seed: int = 2026,
):
    print("=" * 80)
    print("HOTWAY T3: CANDIDATE EDGE-SCORING DQN TRAINING & BENCHMARK")
    print("=" * 80)

    # 1. Environment Setup
    traffic_train = SyntheticProvider(seed=seed, noise_sigma=0.15, incident_prob=0.02)
    env = AdaptiveRoutingEnv(traffic_provider=traffic_train, max_steps=45)
    nodes = list(env.nodes)
    print(f"[+] Loaded environment with {len(nodes)} nodes, {env.graph.number_of_edges()} edges.")

    agent = EdgeScoringDQNAgent(
        in_features=10,
        hidden_dim=64,
        lr=7e-4,
        gamma=0.98,
        epsilon_start=1.0,
        epsilon_end=0.08,
        epsilon_decay_steps=num_train_episodes * 12,
        buffer_size=12000,
        batch_size=32,
        target_update_interval=80,
    )

    rng = np.random.default_rng(seed)

    # Sample OD pairs for training
    print(f"\n[*] Training Edge-Scoring DQN for {num_train_episodes} episodes...")
    train_rewards = []
    train_times = []
    train_losses = []
    epsilons = []

    t0_train = time.perf_counter()

    for ep in range(num_train_episodes):
        # Pick OD pair separated by at least 1.0 km
        o, d = rng.choice(nodes), rng.choice(nodes)
        while o == d:
            d = rng.choice(nodes)

        rain = bool(rng.random() < 0.3)
        time_of_day = float(rng.choice([480.0, 600.0, 1050.0]))  # rush or normal

        obs, info = env.reset(
            options={"source_node": o, "target_node": d, "rain": rain, "time_of_day_min": time_of_day}
        )

        ep_reward = 0.0
        losses = []

        for step in range(env.max_steps):
            curr_u = env.current_node
            if curr_u == env.target_node:
                break

            feats, succs = extract_candidate_edge_features(
                env, curr_u, env.target_node, env.prev_node, env.current_time_min, rain
            )

            action = agent.select_action(feats, deterministic=False)
            agent.decay_epsilon()

            chosen_feat = feats[action].copy()
            next_obs, reward, term, trunc, next_info = env.step(action)
            ep_reward += reward

            next_u = env.current_node
            if term:
                next_feats = np.zeros((0, 10), dtype=np.float32)
            else:
                next_feats, _ = extract_candidate_edge_features(
                    env, next_u, env.target_node, env.prev_node, env.current_time_min, rain
                )

            agent.store_transition(chosen_feat, reward, next_feats, term)
            loss_val = agent.update()
            if loss_val is not None:
                losses.append(loss_val)

            if term or trunc:
                break

        train_rewards.append(ep_reward)
        train_times.append(info.get("total_travel_time_sec", 0.0) / 60.0)
        train_losses.append(float(np.mean(losses)) if losses else 0.0)
        epsilons.append(agent.epsilon)

        if (ep + 1) % 50 == 0 or ep == num_train_episodes - 1:
            avg_r = np.mean(train_rewards[-30:])
            avg_t = np.mean(train_times[-30:])
            avg_l = np.mean(train_losses[-30:])
            print(f"  Episode {ep+1:03d}/{num_train_episodes} | Avg Return: {avg_r:6.2f} | Avg Time: {avg_t:5.2f}m | Loss: {avg_l:6.4f} | Epsilon: {agent.epsilon:.2f}")

    total_train_sec = time.perf_counter() - t0_train
    print(f"[+] Training completed in {total_train_sec:.2f} seconds.")

    # Save model
    os.makedirs(os.path.dirname(model_save_path), exist_ok=True)
    agent.save(model_save_path)
    print(f"[+] Saved model checkpoint: {model_save_path}")

    # Save training metrics
    train_record = {
        "num_episodes": num_train_episodes,
        "total_train_sec": float(round(total_train_sec, 2)),
        "rewards": [float(r) for r in train_rewards],
        "travel_times_min": [float(t) for t in train_times],
        "losses": [float(l) for l in train_losses],
        "epsilons": [float(e) for e in epsilons],
    }
    with open(metrics_json_path, "w", encoding="utf-8") as f:
        json.dump(train_record, f, indent=2)
    print(f"[+] Saved training metrics: {metrics_json_path}")

    # 2. Evaluation Phase
    print("\n" + "=" * 80)
    print(f"[*] Benchmarking Policies on {num_eval_episodes} Unseen Test OD Pairs Across 3 Scenarios")
    print("=" * 80)

    eval_rng = np.random.default_rng(9999)
    eval_pairs = []
    for _ in range(num_eval_episodes):
        uo, ud = eval_rng.choice(nodes), eval_rng.choice(nodes)
        while uo == ud:
            ud = eval_rng.choice(nodes)
        eval_pairs.append((uo, ud))

    scenarios = [
        {"name": "Scenario A: Normal Hours (Dry)", "time": 600.0, "rain": False, "inc_prob": 0.0},
        {"name": "Scenario B: Morning Peak (Dry)", "time": 480.0, "rain": False, "inc_prob": 0.02},
        {"name": "Scenario C: Evening Peak (Rain & Incidents)", "time": 1050.0, "rain": True, "inc_prob": 0.05},
    ]

    static_policy = StaticDijkstraPolicy(env)
    dynamic_policy = DynamicDijkstraPolicy(env)

    comparison_results = {"scenarios": {}}

    for sc in scenarios:
        sc_name = sc["name"]
        print(f"\n--- {sc_name} ---")
        traffic_eval = SyntheticProvider(
            seed=8888,
            noise_sigma=0.20,
            rain_factor=1.40,
            incident_prob=sc["inc_prob"],
        )
        env_eval = AdaptiveRoutingEnv(traffic_provider=traffic_eval, max_steps=50)

        perf = {
            "Static Dijkstra": {"times": [], "success": 0, "latencies": [], "congestions": []},
            "Dynamic Dijkstra": {"times": [], "success": 0, "latencies": [], "congestions": []},
            "Edge-Scoring DQN": {"times": [], "success": 0, "latencies": [], "congestions": []},
        }

        for (o, d) in eval_pairs:
            # 1. Static Dijkstra
            traffic_eval.reset(seed=8888)
            obs, info = env_eval.reset(options={"source_node": o, "target_node": d, "rain": sc["rain"], "time_of_day_min": sc["time"]})
            static_policy.reset(o, d)
            c_count = 0
            t_start = time.perf_counter()

            for _ in range(env_eval.max_steps):
                if env_eval.current_node == env_eval.target_node:
                    break
                a = static_policy.select_action(env_eval.current_node)
                # check congestion
                succs = env_eval.adj[env_eval.current_node]
                next_v = succs[a]
                if traffic_eval.get_edge_state(env_eval.current_node, next_v) != 0:
                    c_count += 1
                _, _, term, trunc, _ = env_eval.step(a)
                if term or trunc:
                    break
            lat_static = (time.perf_counter() - t_start) * 1000.0 / max(1, env_eval.step_count)
            perf["Static Dijkstra"]["times"].append(env_eval.total_travel_time_sec / 60.0)
            perf["Static Dijkstra"]["success"] += (1 if env_eval.current_node == env_eval.target_node else 0)
            perf["Static Dijkstra"]["latencies"].append(lat_static)
            perf["Static Dijkstra"]["congestions"].append(c_count)

            # 2. Dynamic Dijkstra (Recompute at every node)
            traffic_eval.reset(seed=8888)
            obs, info = env_eval.reset(options={"source_node": o, "target_node": d, "rain": sc["rain"], "time_of_day_min": sc["time"]})
            c_count = 0
            t_start = time.perf_counter()

            for _ in range(env_eval.max_steps):
                if env_eval.current_node == env_eval.target_node:
                    break
                a = dynamic_policy.select_action(env_eval.current_node, env_eval.target_node)
                succs = env_eval.adj[env_eval.current_node]
                next_v = succs[a]
                if traffic_eval.get_edge_state(env_eval.current_node, next_v) != 0:
                    c_count += 1
                _, _, term, trunc, _ = env_eval.step(a)
                if term or trunc:
                    break
            lat_dyn = (time.perf_counter() - t_start) * 1000.0 / max(1, env_eval.step_count)
            perf["Dynamic Dijkstra"]["times"].append(env_eval.total_travel_time_sec / 60.0)
            perf["Dynamic Dijkstra"]["success"] += (1 if env_eval.current_node == env_eval.target_node else 0)
            perf["Dynamic Dijkstra"]["latencies"].append(lat_dyn)
            perf["Dynamic Dijkstra"]["congestions"].append(c_count)

            # 3. Edge-Scoring DQN
            traffic_eval.reset(seed=8888)
            obs, info = env_eval.reset(options={"source_node": o, "target_node": d, "rain": sc["rain"], "time_of_day_min": sc["time"]})
            c_count = 0
            t_start = time.perf_counter()

            for _ in range(env_eval.max_steps):
                if env_eval.current_node == env_eval.target_node:
                    break
                feats, succs = extract_candidate_edge_features(
                    env_eval, env_eval.current_node, env_eval.target_node, env_eval.prev_node, env_eval.current_time_min, sc["rain"]
                )
                a = agent.select_action(feats, deterministic=True)
                next_v = succs[a]
                if traffic_eval.get_edge_state(env_eval.current_node, next_v) != 0:
                    c_count += 1
                _, _, term, trunc, _ = env_eval.step(a)
                if term or trunc:
                    break
            lat_dqn = (time.perf_counter() - t_start) * 1000.0 / max(1, env_eval.step_count)
            perf["Edge-Scoring DQN"]["times"].append(env_eval.total_travel_time_sec / 60.0)
            perf["Edge-Scoring DQN"]["success"] += (1 if env_eval.current_node == env_eval.target_node else 0)
            perf["Edge-Scoring DQN"]["latencies"].append(lat_dqn)
            perf["Edge-Scoring DQN"]["congestions"].append(c_count)

        # Statistical Wilcoxon signed-rank test
        t_stat = perf["Static Dijkstra"]["times"]
        t_dyn = perf["Dynamic Dijkstra"]["times"]
        t_dqn = perf["Edge-Scoring DQN"]["times"]

        w_dqn_vs_stat = stats.wilcoxon(t_dqn, t_stat, alternative="two-sided")
        w_dqn_vs_dyn = stats.wilcoxon(t_dqn, t_dyn, alternative="two-sided")
        w_dyn_vs_stat = stats.wilcoxon(t_dyn, t_stat, alternative="two-sided")

        sc_summary = {
            "Static Dijkstra": {
                "mean_time_min": float(round(np.mean(t_stat), 2)),
                "std_time_min": float(round(np.std(t_stat), 2)),
                "success_rate_pct": float(round(perf["Static Dijkstra"]["success"] / num_eval_episodes * 100.0, 1)),
                "avg_congestion_encounters": float(round(np.mean(perf["Static Dijkstra"]["congestions"]), 2)),
                "decision_latency_ms": float(round(np.mean(perf["Static Dijkstra"]["latencies"]), 3)),
            },
            "Dynamic Dijkstra": {
                "mean_time_min": float(round(np.mean(t_dyn), 2)),
                "std_time_min": float(round(np.std(t_dyn), 2)),
                "success_rate_pct": float(round(perf["Dynamic Dijkstra"]["success"] / num_eval_episodes * 100.0, 1)),
                "avg_congestion_encounters": float(round(np.mean(perf["Dynamic Dijkstra"]["congestions"]), 2)),
                "decision_latency_ms": float(round(np.mean(perf["Dynamic Dijkstra"]["latencies"]), 3)),
            },
            "Edge-Scoring DQN": {
                "mean_time_min": float(round(np.mean(t_dqn), 2)),
                "std_time_min": float(round(np.std(t_dqn), 2)),
                "success_rate_pct": float(round(perf["Edge-Scoring DQN"]["success"] / num_eval_episodes * 100.0, 1)),
                "avg_congestion_encounters": float(round(np.mean(perf["Edge-Scoring DQN"]["congestions"]), 2)),
                "decision_latency_ms": float(round(np.mean(perf["Edge-Scoring DQN"]["latencies"]), 3)),
            },
            "wilcoxon_tests": {
                "dqn_vs_static": {"statistic": float(w_dqn_vs_stat.statistic), "p_value": float(w_dqn_vs_stat.pvalue)},
                "dqn_vs_dynamic": {"statistic": float(w_dqn_vs_dyn.statistic), "p_value": float(w_dqn_vs_dyn.pvalue)},
                "dyn_vs_static": {"statistic": float(w_dyn_vs_stat.statistic), "p_value": float(w_dyn_vs_stat.pvalue)},
            },
        }

        comparison_results["scenarios"][sc_name] = sc_summary

        print(f"  Static Dijkstra:   {sc_summary['Static Dijkstra']['mean_time_min']:5.2f} min | Congest: {sc_summary['Static Dijkstra']['avg_congestion_encounters']:.1f} | Latency: {sc_summary['Static Dijkstra']['decision_latency_ms']:.2f}ms")
        print(f"  Dynamic Dijkstra:  {sc_summary['Dynamic Dijkstra']['mean_time_min']:5.2f} min | Congest: {sc_summary['Dynamic Dijkstra']['avg_congestion_encounters']:.1f} | Latency: {sc_summary['Dynamic Dijkstra']['decision_latency_ms']:.2f}ms")
        print(f"  Edge-Scoring DQN:  {sc_summary['Edge-Scoring DQN']['mean_time_min']:5.2f} min | Congest: {sc_summary['Edge-Scoring DQN']['avg_congestion_encounters']:.1f} | Latency: {sc_summary['Edge-Scoring DQN']['decision_latency_ms']:.2f}ms")
        print(f"  -> Wilcoxon p-value (DQN vs Dynamic): {w_dqn_vs_dyn.pvalue:.4e} | (DQN vs Static): {w_dqn_vs_stat.pvalue:.4e}")

    # Save benchmark JSON
    with open(comparison_json_path, "w", encoding="utf-8") as f:
        json.dump(comparison_results, f, indent=2, ensure_ascii=False)
    print(f"\n[+] Saved T3 benchmark comparison to: {comparison_json_path}")

    # 3. Generate Training Curves Figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.5), dpi=200)

    # Smooth curve
    def smooth(vals, w=15):
        if len(vals) < w: return vals
        return np.convolve(vals, np.ones(w)/w, mode='valid')

    ax1.plot(train_rewards, color="#CBD5E1", alpha=0.5, label="Raw Episode Return")
    ax1.plot(np.arange(14, len(train_rewards)), smooth(train_rewards), color="#10B981", linewidth=2.0, label="15-Episode Moving Avg")
    ax1.set_title("Edge-Scoring DQN Training Return Curve", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Episode", fontsize=10)
    ax1.set_ylabel("Cumulative Return (Negative Trip Time)", fontsize=10)
    ax1.grid(True, linestyle=":", alpha=0.5)
    ax1.legend(fontsize=9, loc="lower right")

    ax2.plot(train_losses, color="#F59E0B", linewidth=1.5, label="Smooth L1 (Huber) TD Loss")
    ax2.set_title("Bellman TD Error Loss Convergence", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Episode", fontsize=10)
    ax2.set_ylabel("Huber Loss", fontsize=10)
    ax2.set_yscale("log")
    ax2.grid(True, linestyle=":", alpha=0.5)
    ax2.legend(fontsize=9, loc="upper right")

    plt.tight_layout()
    plt.savefig(fig_train_path, dpi=200)
    plt.close()
    print(f"[+] Saved training curve figure: {fig_train_path}")

    # 4. Generate Benchmark Comparison Figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.0), dpi=200)

    sc_labels = ["Scenario A\n(Normal)", "Scenario B\n(Rush Hour)", "Scenario C\n(Rain & Crash)"]
    x = np.arange(len(sc_labels))
    w = 0.25

    policies = ["Static Dijkstra", "Dynamic Dijkstra", "Edge-Scoring DQN"]
    colors = ["#94A3B8", "#3B82F6", "#10B981"]

    for i, p_name in enumerate(policies):
        means = [comparison_results["scenarios"][sc["name"]][p_name]["mean_time_min"] for sc in scenarios]
        stds = [comparison_results["scenarios"][sc["name"]][p_name]["std_time_min"] for sc in scenarios]
        ax1.bar(x + (i - 1) * w, means, width=w, yerr=stds, capsize=3, label=p_name, color=colors[i], edgecolor="black", linewidth=0.8)

    ax1.set_title("Mean Trip Duration by Policy Across Scenarios (min)\n[Lower is Better]", fontsize=11, fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(sc_labels, fontsize=9)
    ax1.set_ylabel("Travel Time (minutes)", fontsize=10)
    ax1.grid(axis="y", linestyle=":", alpha=0.5)
    ax1.legend(fontsize=9, loc="upper left")

    # Decision Latency
    lats = [
        [comparison_results["scenarios"][sc["name"]][p_name]["decision_latency_ms"] for sc in scenarios]
        for p_name in policies
    ]
    avg_lats = [np.mean(lats[i]) for i in range(len(policies))]

    ax2.bar(policies, avg_lats, color=colors, width=0.55, edgecolor="black", linewidth=0.8)
    ax2.set_title("Decision Latency per Node Step (ms)\n[Lower is Faster]", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Latency (milliseconds)", fontsize=10)
    ax2.set_yscale("log")
    ax2.grid(axis="y", linestyle=":", alpha=0.5)
    for i, v in enumerate(avg_lats):
        ax2.text(i, v * 1.2, f"{v:.2f} ms", ha="center", fontsize=9, fontweight="bold")

    plt.tight_layout()
    plt.savefig(fig_comp_path, dpi=200)
    plt.close()
    print(f"[+] Saved policy benchmark figure: {fig_comp_path}\n")


if __name__ == "__main__":
    run_training_and_benchmark()
