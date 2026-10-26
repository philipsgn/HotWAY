"""
HotWAY CVRP Deep Q-Network (DQN / Double DQN) Training Pipeline v5.0
Trains RL agents to select optimal Local Search operators using F28 state representations.

Operators:
0: two_opt
1: intra_relocate
2: inter_relocate
3: inter_swap

Network Architecture:
MLP: 28 -> 128 -> 128 -> 4 (ReLU)
Matching PyTorchQNetwork in src/cvrp_solver/q_network.py

Outputs:
- src/cvrp_solver/weights/dqn_model.pt
- src/cvrp_solver/weights/double_dqn_model.pt
- rel_result/training_curves.csv
"""

from __future__ import annotations

import argparse
import logging
import os
import random
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim

from src.cvrp_solver.constructive import clarke_wright_savings
from src.cvrp_solver.operators import best_move
from src.cvrp_solver.problem import CVRPInstance
from src.cvrp_solver.q_network import PyTorchQNetwork
from src.cvrp_solver.state_f28 import compute_f28_state
from src.cvrp_solver.validator import calculate_route_distance
from src.benchmark.instance_generator import load_benchmark_instances

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train_cvrp_rl")


class ReplayBuffer:
    def __init__(self, capacity: int = 10000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state: np.ndarray, action: int, reward: float, next_state: np.ndarray, done: bool):
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


def train_rl_agent(
    instances: List[CVRPInstance],
    algorithm: str = "double_dqn",
    episodes: int = 40,
    steps_per_episode: int = 50,
    batch_size: int = 32,
    lr: float = 1e-3,
    gamma: float = 0.95,
    tau: float = 0.05,
    epsilon_start: float = 1.0,
    epsilon_end: float = 0.05,
    epsilon_decay: float = 0.92,
    save_path: str = "src/cvrp_solver/weights/double_dqn_model.pt",
) -> Tuple[PyTorchQNetwork, List[Dict[str, Any]]]:
    """
    Trains a DQN or Double DQN agent over CVRP instances.
    """
    logger.info(f"Training {algorithm.upper()} for {episodes} episodes on {len(instances)} instances...")

    online_net = PyTorchQNetwork(state_dim=28, action_dim=4)
    target_net = PyTorchQNetwork(state_dim=28, action_dim=4)
    target_net.load_state_dict(online_net.state_dict())
    target_net.eval()

    optimizer = optim.Adam(online_net.parameters(), lr=lr)
    loss_fn = nn.SmoothL1Loss() # Huber loss for stability
    replay_buffer = ReplayBuffer(capacity=10000)

    epsilon = epsilon_start
    rng = random.Random(42)

    history: List[Dict[str, Any]] = []

    for ep in range(1, episodes + 1):
        # Pick an instance
        inst = instances[(ep - 1) % len(instances)]

        # Initial solution with Clarke-Wright
        init_routes = clarke_wright_savings(inst)
        current_routes = [r.copy() for r in init_routes]
        init_cost = sum(calculate_route_distance(r, inst.dist_matrix) for r in current_routes)
        current_cost = init_cost
        best_cost = init_cost

        action_counts = [0, 0, 0, 0]
        action_successes = [0, 0, 0, 0]
        last_action = -1
        last_success = False
        no_improve_streak = 0

        ep_loss = 0.0
        updates = 0
        total_ep_reward = 0.0

        for step in range(1, steps_per_episode + 1):
            state = compute_f28_state(
                current_routes,
                current_cost,
                init_cost,
                best_cost,
                step,
                steps_per_episode,
                no_improve_streak,
                30,
                action_counts,
                action_successes,
                last_action,
                last_success,
                inst,
            )

            # Epsilon-greedy action
            if rng.random() < epsilon:
                action = rng.randint(0, 3)
            else:
                with torch.no_grad():
                    q_vals = online_net(torch.FloatTensor(state).unsqueeze(0))
                    action = int(q_vals.argmax(dim=1).item())

            action_counts[action] += 1

            # Execute best move for selected operator
            applied, delta, new_routes, _ = best_move(
                action, current_routes, inst, max_candidates=64, rng=rng
            )

            # Compute reward
            if applied and delta < 0:
                reward = (-delta / 1000.0) * 2.0 # Kilometers saved
                current_routes = new_routes
                current_cost += delta
                action_successes[action] += 1
                last_success = True
                no_improve_streak = 0
                if current_cost < best_cost:
                    best_cost = current_cost
            else:
                reward = -0.05 # Step penalty for wasted action
                last_success = False
                no_improve_streak += 1

            total_ep_reward += reward

            # Next state
            done = (step == steps_per_episode)
            next_state = compute_f28_state(
                current_routes,
                current_cost,
                init_cost,
                best_cost,
                step + 1,
                steps_per_episode,
                no_improve_streak,
                30,
                action_counts,
                action_successes,
                action,
                last_success,
                inst,
            )

            replay_buffer.push(state, action, reward, next_state, done)
            last_action = action

            # Train network from replay buffer
            if len(replay_buffer) >= batch_size:
                s_b, a_b, r_b, ns_b, d_b = replay_buffer.sample(batch_size)
                
                curr_q = online_net(s_b).gather(1, a_b)

                with torch.no_grad():
                    if algorithm.lower() in ["double_dqn", "ddqn"]:
                        # Double DQN: action selected by online_net, evaluated by target_net
                        next_act = online_net(ns_b).argmax(dim=1, keepdim=True)
                        next_q = target_net(ns_b).gather(1, next_act)
                    else:
                        # Standard DQN: max over target_net
                        next_q = target_net(ns_b).max(dim=1, keepdim=True)[0]

                    target_q = r_b + (1.0 - d_b) * gamma * next_q

                loss = loss_fn(curr_q, target_q)
                optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(online_net.parameters(), max_norm=1.0)
                optimizer.step()

                ep_loss += loss.item()
                updates += 1

                # Soft target network update
                for target_param, online_param in zip(target_net.parameters(), online_net.parameters()):
                    target_param.data.copy_(tau * online_param.data + (1.0 - tau) * target_param.data)

        # Decay epsilon
        epsilon = max(epsilon_end, epsilon * epsilon_decay)

        avg_loss = ep_loss / max(updates, 1)
        improvement_km = (init_cost - best_cost) / 1000.0

        history.append({
            "episode": ep,
            "algorithm": algorithm,
            "epsilon": round(epsilon, 3),
            "loss": round(avg_loss, 4),
            "reward": round(total_ep_reward, 2),
            "improvement_km": round(improvement_km, 2),
            "final_cost_km": round(best_cost / 1000.0, 2),
        })

        if ep % 5 == 0 or ep == episodes:
            logger.info(
                f"[{algorithm.upper()}] Ep {ep:02d}/{episodes} | eps={epsilon:.2f} | loss={avg_loss:.4f} | "
                f"rew={total_ep_reward:.1f} | saved={improvement_km:.2f} km"
            )

    # Save trained model weights
    p_save = Path(save_path)
    p_save.parent.mkdir(parents=True, exist_ok=True)
    torch.save(online_net.state_dict(), p_save)
    logger.info(f"Saved trained {algorithm} model weights to {p_save}")

    return online_net, history


def main():
    parser = argparse.ArgumentParser(description="Train CVRP RL Operators")
    parser.add_argument("--instances-dir", type=str, default="data/benchmark_instances")
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--steps", type=int, default=50)
    args = parser.parse_args()

    instances = load_benchmark_instances(args.instances_dir)
    if not instances:
        logger.error(f"No instances found in {args.instances_dir}. Generate instances first.")
        return

    # Train standard DQN
    _, hist_dqn = train_rl_agent(
        instances=instances,
        algorithm="dqn",
        episodes=args.episodes,
        steps_per_episode=args.steps,
        save_path="src/cvrp_solver/weights/dqn_model.pt",
    )

    # Train Double DQN
    _, hist_ddqn = train_rl_agent(
        instances=instances,
        algorithm="double_dqn",
        episodes=args.episodes,
        steps_per_episode=args.steps,
        save_path="src/cvrp_solver/weights/double_dqn_model.pt",
    )

    # Export training curves
    all_hist = hist_dqn + hist_ddqn
    df_curves = pd.DataFrame(all_hist)
    out_curves = Path("rel_result/training_curves.csv")
    out_curves.parent.mkdir(parents=True, exist_ok=True)
    df_curves.to_csv(out_curves, index=False)
    logger.info(f"Saved training curves to {out_curves}")


if __name__ == "__main__":
    main()
