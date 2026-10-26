"""
Training and Evaluation Pipeline for HotWAY GĐ2 (Gate G4).
Trains DQN, Double DQN, and PPO across >= 5 seeds.
Performs Ablation Studies, OOD Stress Testing, Sensitivity Analysis,
and exports all results to results/training/.
"""

from __future__ import annotations

import collections
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple

import numpy as np
import pandas as pd
import torch

from src.envs.dispatch_env import DispatchEnv
from src.agents.dqn_dispatch import DQNAgent
from src.agents.ppo_dispatch import PPOAgent


def train_dqn_seed(
    seed: int,
    is_double: bool = False,
    num_episodes: int = 40,
    gamma: float = 0.99,
    state_dim: int = 12,
    ablate_spatial: bool = False,
    ablate_arrival: bool = False,
) -> Tuple[DQNAgent, List[Dict[str, Any]]]:
    """Trains a single DQN or Double DQN agent on one seed."""
    agent_name = "Double_DQN" if is_double else "DQN"
    agent = DQNAgent(state_dim=state_dim, action_dim=5, gamma=gamma, is_double=is_double, name=agent_name)

    training_logs = []
    rng = np.random.default_rng(seed)

    for ep in range(num_episodes):
        ep_seed = int(rng.integers(1, 100000))
        env = DispatchEnv(enable_event_logging=False)
        obs, _ = env.reset(seed=ep_seed)

        if ablate_spatial:
            obs[6] = 0.0
        if ablate_arrival:
            obs[11] = 0.0

        terminated = False
        truncated = False
        ep_reward = 0.0

        # Epsilon decay
        eps = max(0.05, 1.0 - (ep / (num_episodes * 0.7)))

        while not (terminated or truncated):
            act = agent.select_action(obs, epsilon=eps)
            next_obs, r, terminated, truncated, _ = env.step(act)

            if ablate_spatial:
                next_obs[6] = 0.0
            if ablate_arrival:
                next_obs[11] = 0.0

            agent.buffer.push(obs, act, r, next_obs, terminated)
            agent.update()

            ep_reward += r
            obs = next_obs

        metrics = env.get_metrics()
        training_logs.append({
            "agent": agent.name,
            "seed": seed,
            "episode": ep + 1,
            "reward": ep_reward,
            "mean_wait_min": metrics["mean_wait_min"],
            "p90_wait_min": metrics["p90_wait_min"],
            "late_rate_pct": metrics["late_rate_pct"],
        })

    return agent, training_logs


def train_ppo_seed(
    seed: int,
    num_episodes: int = 40,
    gamma: float = 0.99,
) -> Tuple[PPOAgent, List[Dict[str, Any]]]:
    """Trains a single PPO agent on one seed."""
    agent = PPOAgent(state_dim=12, action_dim=5, gamma=gamma, name="PPO")
    training_logs = []
    rng = np.random.default_rng(seed)

    for ep in range(num_episodes):
        ep_seed = int(rng.integers(1, 100000))
        env = DispatchEnv(enable_event_logging=False)
        obs, _ = env.reset(seed=ep_seed)

        states, actions, log_probs, rewards, dones, values = [], [], [], [], [], []
        terminated = False
        truncated = False
        ep_reward = 0.0

        while not (terminated or truncated):
            act, lp, val = agent.select_action(obs)
            next_obs, r, terminated, truncated, _ = env.step(act)

            states.append(obs)
            actions.append(act)
            log_probs.append(lp)
            rewards.append(r)
            dones.append(terminated)
            values.append(val)

            ep_reward += r
            obs = next_obs

        # Update PPO after each episode rollout
        agent.update(states, actions, log_probs, rewards, dones, values)

        metrics = env.get_metrics()
        training_logs.append({
            "agent": "PPO",
            "seed": seed,
            "episode": ep + 1,
            "reward": ep_reward,
            "mean_wait_min": metrics["mean_wait_min"],
            "p90_wait_min": metrics["p90_wait_min"],
            "late_rate_pct": metrics["late_rate_pct"],
        })

    return agent, training_logs


def evaluate_agent_on_test_seeds(
    agent: Any,
    test_seeds: List[int],
    matrix_path: str = "data/matrix_standard.npz",
    address_pool_path: str = "data/address_pool_standard.json",
    is_ood: bool = False,
    rain_factor: float = 1.0,
    kitchen_mean_min: float = 12.0,
    ablate_spatial: bool = False,
    ablate_arrival: bool = False,
) -> List[Dict[str, Any]]:
    """Evaluates trained agent deterministically on frozen test seeds."""
    eval_runs = []
    for s in test_seeds:
        t0 = time.perf_counter()
        env = DispatchEnv(
            matrix_path=matrix_path,
            address_pool_path=address_pool_path,
            enable_event_logging=False,
            rain_factor=rain_factor,
            kitchen_mean_min=kitchen_mean_min,
        )
        obs, _ = env.reset(seed=s)

        terminated = False
        truncated = False
        latencies = []

        while not (terminated or truncated):
            if ablate_spatial:
                obs[6] = 0.0
            if ablate_arrival:
                obs[11] = 0.0

            t_dec = time.perf_counter()
            if isinstance(agent, DQNAgent):
                act = agent.select_action(obs, epsilon=0.0)
            elif isinstance(agent, PPOAgent):
                act, _, _ = agent.select_action(obs)
            else:
                act = 0
            latencies.append((time.perf_counter() - t_dec) * 1000.0)

            obs, _, terminated, truncated, _ = env.step(act)

        run_time = time.perf_counter() - t0
        metrics = env.get_metrics()
        metrics["agent"] = agent.name
        metrics["seed"] = s
        metrics["is_ood"] = is_ood
        metrics["run_time_sec"] = run_time
        metrics["mean_decision_latency_ms"] = float(np.mean(latencies))
        metrics["utility_score"] = float(-metrics["mean_wait_min"] - 2.0 * metrics["mean_lateness_min"])
        eval_runs.append(metrics)

    return eval_runs


def bootstrap_ci_mean(data: np.ndarray, n_boot: int = 2000, ci: float = 0.95) -> Tuple[float, float]:
    rng = np.random.default_rng(2026)
    boot_means = [float(np.mean(rng.choice(data, size=len(data), replace=True))) for _ in range(n_boot)]
    alpha = (1.0 - ci) / 2.0
    return float(np.percentile(boot_means, 100.0 * alpha)), float(np.percentile(boot_means, 100.0 * (1.0 - alpha)))


def run_gate4_experiments():
    print("=== STARTING GATE G4 RL TRAINING & COMPREHENSIVE BENCHMARK ===")
    out_dir = Path("results/training")
    out_dir.mkdir(parents=True, exist_ok=True)

    train_seeds = [2026, 2027, 2028, 2029, 2030]
    test_seeds = [2041, 2042, 2043, 2044, 2045]
    ood_seeds = [2046, 2047, 2048, 2049, 2050]

    all_curve_logs = []
    all_test_evals = []
    all_ood_evals = []

    # 1. Train DQN (5 seeds)
    print("\n--- 1. Training DQN (5 seeds) ---")
    dqn_agents = []
    for s in train_seeds:
        t0 = time.perf_counter()
        agent, logs = train_dqn_seed(seed=s, is_double=False, num_episodes=40)
        dur = time.perf_counter() - t0
        dqn_agents.append(agent)
        all_curve_logs.extend(logs)
        print(f"DQN Seed {s} trained in {dur:.1f}s | Final ep wait: {logs[-1]['mean_wait_min']:.2f}m")
        # Save checkpoint
        agent.save(out_dir / f"dqn_seed_{s}.pt")

    # 2. Train Double DQN (5 seeds)
    print("\n--- 2. Training Double DQN (5 seeds) ---")
    ddqn_agents = []
    for s in train_seeds:
        t0 = time.perf_counter()
        agent, logs = train_dqn_seed(seed=s, is_double=True, num_episodes=40)
        dur = time.perf_counter() - t0
        ddqn_agents.append(agent)
        all_curve_logs.extend(logs)
        print(f"Double DQN Seed {s} trained in {dur:.1f}s | Final ep wait: {logs[-1]['mean_wait_min']:.2f}m")
        agent.save(out_dir / f"double_dqn_seed_{s}.pt")

    # 3. Train PPO (5 seeds)
    print("\n--- 3. Training PPO (5 seeds) ---")
    ppo_agents = []
    for s in train_seeds:
        t0 = time.perf_counter()
        agent, logs = train_ppo_seed(seed=s, num_episodes=40)
        dur = time.perf_counter() - t0
        ppo_agents.append(agent)
        all_curve_logs.extend(logs)
        print(f"PPO Seed {s} trained in {dur:.1f}s | Final ep wait: {logs[-1]['mean_wait_min']:.2f}m")
        agent.save(out_dir / f"ppo_seed_{s}.pt")

    # Save training curves
    df_curves = pd.DataFrame(all_curve_logs)
    df_curves.to_csv(out_dir / "training_curves.csv", index=False)
    print(f"Saved training curves to {out_dir / 'training_curves.csv'}")

    # 4. Evaluate all checkpoints on Frozen Test Set (5 seeds)
    print("\n--- 4. Evaluating Checkpoints on Frozen Test Set ---")
    for name, agent_list in [("DQN", dqn_agents), ("Double_DQN", ddqn_agents), ("PPO", ppo_agents)]:
        agent_runs = []
        for ag in agent_list:
            eval_runs = evaluate_agent_on_test_seeds(ag, test_seeds)
            agent_runs.extend(eval_runs)
        all_test_evals.extend(agent_runs)

        mean_w = float(np.mean([r["mean_wait_min"] for r in agent_runs]))
        p90_w = float(np.mean([r["p90_wait_min"] for r in agent_runs]))
        late_pct = float(np.mean([r["late_rate_pct"] for r in agent_runs]))
        gini = float(np.mean([r["gini_coefficient"] for r in agent_runs]))
        util = float(np.mean([r["fleet_utilization"] for r in agent_runs])) * 100.0
        lat_ms = float(np.mean([r["mean_decision_latency_ms"] for r in agent_runs]))
        print(f"TEST | {name:<12}: Mean Wait={mean_w:5.2f}m, p90={p90_w:5.2f}m, Late={late_pct:4.1f}%, Gini={gini:.3f}, Util={util:4.1f}%, Latency={lat_ms:.2f}ms")

    # 5. Evaluate on OOD Split
    print("\n--- 5. Evaluating Checkpoints on OOD Split ---")
    best_ddqn = ddqn_agents[0]
    best_dqn = dqn_agents[0]
    best_ppo = ppo_agents[0]

    for ag in [best_dqn, best_ddqn, best_ppo]:
        ood_runs = evaluate_agent_on_test_seeds(
            ag,
            ood_seeds,
            matrix_path="data/matrix_ood.npz",
            address_pool_path="data/address_pool_ood.json",
            is_ood=True,
        )
        all_ood_evals.extend(ood_runs)
        mean_w = float(np.mean([r["mean_wait_min"] for r in ood_runs]))
        p90_s = float(np.mean([r["p90_surge_wait_min"] for r in ood_runs]))
        print(f"OOD  | {ag.name:<12}: Mean Wait={mean_w:5.2f}m, Surge p90={p90_s:5.2f}m")

    # 6. Ablation Studies
    print("\n--- 6. Running Ablation Studies ---")
    ablation_results = []

    # Ablation A: No spatial dispersion feature
    runs_no_spatial = evaluate_agent_on_test_seeds(best_ddqn, test_seeds, ablate_spatial=True)
    mean_w = float(np.mean([r["mean_wait_min"] for r in runs_no_spatial]))
    ablation_results.append({"ablation": "No Spatial Feature", "mean_wait_min": mean_w})
    print(f"Ablation: No Spatial Feature -> Mean Wait: {mean_w:5.2f}m")

    # Ablation B: No arrival rate feature
    runs_no_arrival = evaluate_agent_on_test_seeds(best_ddqn, test_seeds, ablate_arrival=True)
    mean_w = float(np.mean([r["mean_wait_min"] for r in runs_no_arrival]))
    ablation_results.append({"ablation": "No Arrival Rate Feature", "mean_wait_min": mean_w})
    print(f"Ablation: No Arrival Rate Feature -> Mean Wait: {mean_w:5.2f}m")

    # Ablation C: Discount factor gamma = 0.95
    ag_gamma95, _ = train_dqn_seed(seed=2026, is_double=True, num_episodes=20, gamma=0.95)
    runs_g95 = evaluate_agent_on_test_seeds(ag_gamma95, test_seeds)
    mean_w = float(np.mean([r["mean_wait_min"] for r in runs_g95]))
    ablation_results.append({"ablation": "Gamma=0.95", "mean_wait_min": mean_w})
    print(f"Ablation: Gamma=0.95 -> Mean Wait: {mean_w:5.2f}m")

    df_ablation = pd.DataFrame(ablation_results)
    df_ablation.to_csv(out_dir / "ablation_results.csv", index=False)

    # 7. Sensitivity Analysis: Weather & Kitchen Prep Time
    print("\n--- 7. Running Sensitivity Analysis ---")
    sensitivity_rows = []
    for rain in [1.0, 1.4]:
        for k_prep in [8.0, 12.0, 16.0]:
            runs_sens = evaluate_agent_on_test_seeds(
                best_ddqn,
                test_seeds[:2],
                rain_factor=rain,
                kitchen_mean_min=k_prep,
            )
            mean_w = float(np.mean([r["mean_wait_min"] for r in runs_sens]))
            sensitivity_rows.append({
                "rain_factor": rain,
                "kitchen_mean_min": k_prep,
                "mean_wait_min": mean_w,
            })
            print(f"Sensitivity: Rain={rain}, Kitchen Prep={k_prep}m -> Mean Wait: {mean_w:5.2f}m")

    df_sens = pd.DataFrame(sensitivity_rows)
    df_sens.to_csv(out_dir / "sensitivity_analysis.csv", index=False)

    # 8. Consolidate and Save Summary Test Results
    df_test_evals = pd.DataFrame(all_test_evals)
    df_test_evals.to_csv(out_dir / "raw_rl_test_runs.csv", index=False)

    summary_rows = []
    for ag_name in df_test_evals["agent"].unique():
        sub = df_test_evals[df_test_evals["agent"] == ag_name]
        w_vals = sub["mean_wait_min"].to_numpy()
        ci_l, ci_u = bootstrap_ci_mean(w_vals)

        summary_rows.append({
            "agent": ag_name,
            "mean_wait_min": float(np.mean(w_vals)),
            "ci_95_lower": ci_l,
            "ci_95_upper": ci_u,
            "p90_wait_min": float(np.mean(sub["p90_wait_min"])),
            "p95_wait_min": float(np.mean(sub["p95_wait_min"])),
            "late_rate_pct": float(np.mean(sub["late_rate_pct"])),
            "gini_coefficient": float(np.mean(sub["gini_coefficient"])),
            "fleet_utilization_pct": float(np.mean(sub["fleet_utilization"])) * 100.0,
            "total_km": float(np.mean(sub["total_km"])),
            "decision_latency_ms": float(np.mean(sub["mean_decision_latency_ms"])),
        })

    df_summary = pd.DataFrame(summary_rows)
    df_summary.to_csv(out_dir / "summary_rl_test.csv", index=False)
    print(f"\nSaved RL test summary to {out_dir / 'summary_rl_test.csv'}")


if __name__ == "__main__":
    run_gate4_experiments()
