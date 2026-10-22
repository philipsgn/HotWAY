"""Independent DQN / Double DQN retraining with strict train/val/test isolation.

Train: HCMC_VN_01..20 ; Validation: 21..24 ; Test: 25..30 (test never touched here).
Replicates the documented 28->128->128->4 MLP, replay buffer, epsilon-greedy,
Huber loss and soft target updates, but adds:
  * deterministic seeding,
  * validation-based best-checkpoint selection,
  * proper train-only sampling.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.cvrp_solver.constructive import clarke_wright_savings  # noqa: E402
from src.cvrp_solver.operators import best_move  # noqa: E402
from src.cvrp_solver.problem import CVRPInstance  # noqa: E402
from src.cvrp_solver.q_network import PyTorchQNetwork  # noqa: E402
from src.cvrp_solver.state_f28 import compute_f28_state  # noqa: E402
from src.cvrp_solver.validator import calculate_route_distance  # noqa: E402
from src.benchmark.instance_generator import load_benchmark_instances  # noqa: E402


class ReplayBuffer:
    def __init__(self, capacity: int = 10000):
        self.buffer: deque = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size: int):
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        return (
            torch.FloatTensor(np.array(states)),
            torch.LongTensor(actions).unsqueeze(1),
            torch.FloatTensor(rewards).unsqueeze(1),
            torch.FloatTensor(np.array(next_states)),
            torch.FloatTensor(dones).unsqueeze(1),
        )

    def __len__(self):
        return len(self.buffer)


def seed_all(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(False)


def evaluate_policy(
    net: PyTorchQNetwork,
    instances: List[CVRPInstance],
    max_steps: int = 100,
    max_candidates: int = 128,
    seed: int = 999,
) -> Tuple[float, List[float]]:
    """Deterministic greedy evaluation of an in-memory Q-network."""
    net.eval()
    costs = []
    with torch.no_grad():
        for inst in instances:
            rng = random.Random(seed)
            routes = [list(r) for r in clarke_wright_savings(inst)]
            cost = sum(calculate_route_distance(r, inst.dist_matrix) for r in routes)
            init_cost = cost
            best_cost = cost
            action_counts = [0, 0, 0, 0]
            action_successes = [0, 0, 0, 0]
            last_action = -1
            last_success = False
            no_improve = 0
            for step in range(1, max_steps + 1):
                state = compute_f28_state(
                    routes, cost, init_cost, best_cost, step, max_steps,
                    no_improve, 30, action_counts, action_successes,
                    last_action, last_success, inst,
                )
                action = int(net(torch.FloatTensor(state).unsqueeze(0)).argmax(dim=1).item())
                action_counts[action] += 1
                applied, delta, new_routes, _ = best_move(
                    action, routes, inst, max_candidates=max_candidates, rng=rng
                )
                if applied:
                    routes = new_routes
                    cost += delta
                    action_successes[action] += 1
                    last_success = True
                    no_improve = 0
                    if cost < best_cost:
                        best_cost = cost
                else:
                    last_success = False
                    no_improve += 1
                last_action = action
            costs.append(best_cost)
    return float(np.mean(costs)), costs


def train(
    train_instances: List[CVRPInstance],
    val_instances: List[CVRPInstance],
    algorithm: str,
    episodes: int,
    steps_per_episode: int,
    max_candidates: int,
    seed: int,
    val_every: int,
    tag: str,
    weights_dir: Path,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    seed_all(seed)
    online = PyTorchQNetwork(28, 4)
    target = PyTorchQNetwork(28, 4)
    target.load_state_dict(online.state_dict())
    target.eval()
    optimizer = optim.Adam(online.parameters(), lr=1e-3)
    loss_fn = nn.SmoothL1Loss()
    replay = ReplayBuffer(10000)

    epsilon = 1.0
    eps_end = 0.05
    eps_decay = 0.92
    gamma = 0.95
    tau = 0.05
    batch_size = 32
    rng = random.Random(seed)

    history: List[Dict[str, Any]] = []
    best_val = float("inf")
    best_ep = -1
    best_path = weights_dir / f"{tag}_{algorithm}_best.pt"
    final_path = weights_dir / f"{tag}_{algorithm}_final.pt"

    t0 = time.time()
    for ep in range(1, episodes + 1):
        inst = train_instances[(ep - 1) % len(train_instances)]
        routes = [list(r) for r in clarke_wright_savings(inst)]
        cost = sum(calculate_route_distance(r, inst.dist_matrix) for r in routes)
        init_cost = cost
        best_cost = cost
        action_counts = [0, 0, 0, 0]
        action_successes = [0, 0, 0, 0]
        last_action = -1
        last_success = False
        no_improve = 0
        ep_loss = 0.0
        updates = 0
        ep_reward = 0.0

        for step in range(1, steps_per_episode + 1):
            state = compute_f28_state(
                routes, cost, init_cost, best_cost, step, steps_per_episode,
                no_improve, 30, action_counts, action_successes,
                last_action, last_success, inst,
            )
            if rng.random() < epsilon:
                action = rng.randint(0, 3)
            else:
                with torch.no_grad():
                    action = int(online(torch.FloatTensor(state).unsqueeze(0)).argmax(dim=1).item())
            action_counts[action] += 1

            applied, delta, new_routes, _ = best_move(
                action, routes, inst, max_candidates=max_candidates, rng=rng
            )
            if applied and delta < 0:
                reward = (-delta / 1000.0) * 2.0
                routes = new_routes
                cost += delta
                action_successes[action] += 1
                last_success = True
                no_improve = 0
                if cost < best_cost:
                    best_cost = cost
            else:
                reward = -0.05
                last_success = False
                no_improve += 1
            ep_reward += reward

            done = step == steps_per_episode
            next_state = compute_f28_state(
                routes, cost, init_cost, best_cost, step + 1, steps_per_episode,
                no_improve, 30, action_counts, action_successes,
                action, last_success, inst,
            )
            replay.push(state, action, reward, next_state, done)
            last_action = action

            if len(replay) >= batch_size:
                s_b, a_b, r_b, ns_b, d_b = replay.sample(batch_size)
                curr_q = online(s_b).gather(1, a_b)
                with torch.no_grad():
                    if algorithm.lower() in ("double_dqn", "ddqn"):
                        next_act = online(ns_b).argmax(dim=1, keepdim=True)
                        next_q = target(ns_b).gather(1, next_act)
                    else:
                        next_q = target(ns_b).max(dim=1, keepdim=True)[0]
                    target_q = r_b + (1.0 - d_b) * gamma * next_q
                loss = loss_fn(curr_q, target_q)
                optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(online.parameters(), max_norm=1.0)
                optimizer.step()
                ep_loss += loss.item()
                updates += 1
                for tp, op in zip(target.parameters(), online.parameters()):
                    tp.data.copy_(tau * op.data + (1.0 - tau) * tp.data)

        epsilon = max(eps_end, epsilon * eps_decay)
        avg_loss = ep_loss / max(updates, 1)
        train_improvement_km = (init_cost - best_cost) / 1000.0

        val_cost = None
        saved = False
        if val_every > 0 and (ep % val_every == 0 or ep == 1 or ep == episodes):
            val_mean, _ = evaluate_policy(online, val_instances, seed=999)
            val_cost = val_mean / 1000.0
            if val_mean < best_val:
                best_val = val_mean
                best_ep = ep
                torch.save(online.state_dict(), best_path)
                saved = True

        history.append({
            "episode": ep,
            "algorithm": algorithm,
            "tag": tag,
            "epsilon": round(epsilon, 3),
            "loss": round(avg_loss, 4),
            "reward": round(ep_reward, 2),
            "train_improvement_km": round(train_improvement_km, 2),
            "train_final_cost_km": round(best_cost / 1000.0, 2),
            "val_cost_km": None if val_cost is None else round(val_cost, 3),
            "best_val_cost_km": round(best_val / 1000.0, 3) if best_val < float("inf") else None,
            "best_episode": best_ep if best_val < float("inf") else None,
            "checkpoint_saved": saved,
        })
        if ep % 10 == 0 or ep == episodes:
            print(
                f"[{tag}/{algorithm}] ep {ep:3d}/{episodes} eps={epsilon:.3f} "
                f"loss={avg_loss:.4f} rew={ep_reward:.2f} train_saved={train_improvement_km:.2f}km "
                f"val={val_cost if val_cost is not None else float('nan'):.3f} best_val={best_val/1000.0:.3f}",
                flush=True,
            )

    # Always save the final model too
    torch.save(online.state_dict(), final_path)
    info = {
        "algorithm": algorithm,
        "tag": tag,
        "episodes": episodes,
        "steps_per_episode": steps_per_episode,
        "max_candidates": max_candidates,
        "seed": seed,
        "best_val_cost_km": best_val / 1000.0 if best_val < float("inf") else None,
        "best_episode": best_ep,
        "best_weights": str(best_path) if best_path.exists() else None,
        "final_weights": str(final_path),
        "seconds": round(time.time() - t0, 1),
    }
    return history, info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=30)
    ap.add_argument("--steps", type=int, default=50)
    ap.add_argument("--candidates", type=int, default=64)
    ap.add_argument("--val-every", type=int, default=1)
    ap.add_argument("--seed", type=int, default=2027)
    ap.add_argument("--tag", type=str, default="repro")
    ap.add_argument("--algorithms", type=str, default="dqn,double_dqn")
    args = ap.parse_args()

    instances = load_benchmark_instances(ROOT / "data" / "benchmark_instances")
    by_name = {i.name: i for i in instances}
    train_instances = [by_name[f"HCMC_VN_{i:02d}"] for i in range(1, 21)]
    val_instances = [by_name[f"HCMC_VN_{i:02d}"] for i in range(21, 25)]
    test_instances = [by_name[f"HCMC_VN_{i:02d}"] for i in range(25, 31)]
    assert len(train_instances) == 20 and len(val_instances) == 4 and len(test_instances) == 6

    weights_dir = ROOT / "audit" / "weights"
    weights_dir.mkdir(parents=True, exist_ok=True)

    all_history = []
    infos = []
    for algo in [a.strip() for a in args.algorithms.split(",") if a.strip()]:
        hist, info = train(
            train_instances=train_instances,
            val_instances=val_instances,
            algorithm=algo,
            episodes=args.episodes,
            steps_per_episode=args.steps,
            max_candidates=args.candidates,
            seed=args.seed,
            val_every=args.val_every,
            tag=args.tag,
            weights_dir=weights_dir,
        )
        all_history.extend(hist)
        infos.append(info)

    df = pd.DataFrame(all_history)
    curves_path = ROOT / "audit" / "results" / f"training_curves_{args.tag}.csv"
    df.to_csv(curves_path, index=False)
    info_path = ROOT / "audit" / "results" / f"training_info_{args.tag}.json"
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(infos, f, indent=2)

    print(f"Wrote {curves_path}")
    for info in infos:
        print(info)


if __name__ == "__main__":
    main()
