"""
Unified Training Entry Point for Reinforcement Learning Route Optimization Models:
1. Dueling DQN with Action Masking & PER (--model=dqn)
2. Pointer Network with Bi-LSTM & A2C (--model=ptr)
3. Attention Model Graph Transformer (--model=am)

Supports both local CPU smoke testing and large-scale Kaggle/Colab GPU training (2x T4).
Upgraded with 128-d/3L Gold Architecture, Multi-Scale Curriculum & Cost Perturbation.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import random
import time
from typing import List

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

from env.traffic_tsp_env import TrafficTSPEnv, compute_traffic_multiplier_tensor
from models.dqn_agent import DQNAgent
from models.pointer_net import PointerNetwork
from src.agents.attention_model.model import AttentionModel as GraphAttentionModel


def train_dqn(epochs: int, batch_size: int, lr: float, device: str, save_dir: Path):
    print(f"\n=======================================================")
    print(f"--- Training Model 1: Dueling DQN with Action Masking ---")
    print(f"Device: {device} | Epochs: {epochs} | Batch Size: {batch_size}")
    print(f"=======================================================")

    agent = DQNAgent(max_nodes=20, lr=lr, device=device)
    env = TrafficTSPEnv(fixed_max_nodes=20)

    save_dir.mkdir(parents=True, exist_ok=True)
    step_count = 0

    for ep in range(1, epochs + 1):
        obs, info = env.reset()
        done = False
        ep_reward = 0.0
        losses = []

        while not done:
            step_count += 1
            state_vec, mask = env.get_dqn_state_vector(max_nodes=20)
            action = agent.select_action(state_vec, mask, eval_mode=False)

            next_obs, reward, terminated, truncated, step_info = env.step(action)
            done = terminated or truncated

            next_state_vec, next_mask = env.get_dqn_state_vector(max_nodes=20)
            agent.memory.push(state_vec, action, reward, next_state_vec, done, next_mask)

            loss = agent.train_step(batch_size=min(batch_size, len(agent.memory)))
            if loss is not None:
                losses.append(loss)

            if step_count % 500 == 0:
                agent.update_target()

            ep_reward += reward

        mean_loss = float(np.mean(losses)) if losses else 0.0
        print(f"Epoch {ep:03d}/{epochs:03d} | Reward: {ep_reward:8.2f} | Loss: {mean_loss:.4f} | Epsilon: {agent.epsilon:.3f}")

    out_file = save_dir / "dqn_dueling_masked.pt"
    torch.save(agent.q_net.state_dict(), out_file)
    print(f"Saved DQN weights to: {out_file}\n")


def train_pointer_net(epochs: int, batch_size: int, lr: float, device: str, save_dir: Path):
    print(f"\n=======================================================")
    print(f"--- Training Model 2: Pointer Network with A2C ---")
    print(f"Device: {device} | Epochs: {epochs} | Batch Size: {batch_size}")
    print(f"=======================================================")

    model = PointerNetwork(input_dim=4, hidden_dim=128).to(device)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    scheduler = optim.lr_scheduler.ExponentialLR(optimizer, gamma=0.96)

    save_dir.mkdir(parents=True, exist_ok=True)
    for ep in range(1, epochs + 1):
        model.train()
        n_nodes = random.randint(10, 25) if random.random() < 0.6 else random.randint(26, 50)
        raw_coords = torch.rand(batch_size, n_nodes, 2, device=device)
        coord_min = raw_coords.amin(dim=1, keepdim=True)
        coord_range = (raw_coords.amax(dim=1, keepdim=True) - coord_min).clamp_min(1e-6)
        batch_coords = (raw_coords - coord_min) / coord_range
        departure_hours = torch.rand(batch_size, device=device) * 24.0
        departure_traffic = compute_traffic_multiplier_tensor(departure_hours).view(batch_size, 1, 1)
        depot_dist = torch.linalg.vector_norm(batch_coords - batch_coords[:, :1, :], dim=-1, keepdim=True)
        batch_input = torch.cat([
            batch_coords,
            depot_dist,
            (departure_traffic / 2.25).expand(-1, n_nodes, -1),
        ], dim=-1)

        action_seq, total_log_prob, baseline_pred = model(batch_input, deterministic=False)
        ordered = torch.gather(batch_coords, 1, action_seq.unsqueeze(-1).expand(batch_size, n_nodes, 2))
        next_coords = torch.roll(ordered, shifts=-1, dims=1)
        seg_dist = torch.linalg.vector_norm(ordered - next_coords, dim=-1)
        elapsed = torch.zeros(batch_size, device=device)
        cost = torch.zeros_like(elapsed)
        for step in range(n_nodes):
            leg = seg_dist[:, step] * compute_traffic_multiplier_tensor(departure_hours + elapsed / 60.0)
            cost = cost + leg
            elapsed = elapsed + leg

        advantage = (cost - baseline_pred).detach()
        actor_loss = (advantage * total_log_prob).mean()
        critic_loss = F.mse_loss(baseline_pred, cost.detach())
        total_loss = actor_loss + 0.5 * critic_loss

        optimizer.zero_grad()
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        scheduler.step()

        print(f"Epoch {ep:03d}/{epochs:03d} (N={n_nodes}) | Actor Loss: {actor_loss.item():.4f} | Critic Loss: {critic_loss.item():.4f} | Mean Tour Cost: {cost.mean().item():.2f}")

    out_file = save_dir / "pointer_net_a2c.pt"
    torch.save(model.state_dict(), out_file)
    print(f"Saved PointerNet weights to: {out_file}\n")


def train_attention_model(epochs: int, batch_size: int, lr: float, device: str, save_dir: Path):
    print(f"\n=======================================================")
    print(f"--- Training Model 3: Graph Attention Model (Kool et al.) ---")
    print(f"Device: {device} | Epochs: {epochs} | Batch Size: {batch_size}")
    print(f"Architecture: 128-d, 3 Layers, 8 Heads (741,504 Params)")
    print(f"Generalization: Dynamic Min-Max + Multi-Scale + Cost Perturbation")
    print(f"=======================================================")

    # 128-d, 3 layers, 8 heads (Gold Config)
    model = GraphAttentionModel(input_dim=3, embed_dim=128, n_heads=8, n_layers=3).to(device)
    baseline_model = GraphAttentionModel(input_dim=3, embed_dim=128, n_heads=8, n_layers=3).to(device)
    baseline_model.load_state_dict(model.state_dict())
    baseline_model.eval()

    optimizer = optim.Adam(model.parameters(), lr=lr)
    scheduler = optim.lr_scheduler.ExponentialLR(optimizer, gamma=0.985)
    save_dir.mkdir(parents=True, exist_ok=True)

    # Fixed held-out instances make baseline updates comparable across epochs.
    val_nodes = 20
    val_raw_coords = torch.rand(batch_size, val_nodes, 2, device=device)
    val_min = val_raw_coords.amin(dim=1, keepdim=True)
    val_range = (val_raw_coords.amax(dim=1, keepdim=True) - val_min).clamp_min(1e-6)
    val_coords = (val_raw_coords - val_min) / val_range
    val_departures = torch.full((batch_size,), 8.25, device=device)

    def calc_tour_cost(t_seq, coords_batch, departure_hours):
        bsz, node_count, _ = coords_batch.shape
        ordered = torch.gather(coords_batch, 1, t_seq.unsqueeze(-1).expand(bsz, node_count, 2))
        next_coords = torch.roll(ordered, shifts=-1, dims=1)
        seg_dist = torch.linalg.vector_norm(ordered - next_coords, dim=-1)
        # Synthetic unit-square edge length is used as base travel minutes for curriculum training.
        elapsed = torch.zeros(bsz, device=coords_batch.device)
        total = torch.zeros_like(elapsed)
        for step in range(node_count):
            c_t = compute_traffic_multiplier_tensor(departure_hours + elapsed / 60.0)
            leg = seg_dist[:, step] * c_t
            total = total + leg
            elapsed = elapsed + leg
        return total

    for ep in range(1, epochs + 1):
        model.train()

        # Multi-scale curriculum: 60% N in [10, 25], 40% N in [26, 50]
        if random.random() < 0.6:
            n_nodes = random.randint(10, 25)
        else:
            n_nodes = random.randint(26, 50)

        # Dynamic Min-Max normalized coordinates in [0, 1]^2
        raw_coords = torch.rand(batch_size, n_nodes, 2, device=device)
        coord_min = raw_coords.amin(dim=1, keepdim=True)
        coord_range = (raw_coords.amax(dim=1, keepdim=True) - coord_min).clamp_min(1e-6)
        coords = (raw_coords - coord_min) / coord_range

        departure_hours = torch.rand(batch_size, device=device) * 24.0
        departure_traffic = compute_traffic_multiplier_tensor(departure_hours).view(batch_size, 1, 1)
        # Features: [per-instance normalized coordinates, departure traffic context].
        nodes = torch.cat([coords, (departure_traffic / 2.25).expand(-1, n_nodes, -1)], dim=-1)

        # Rollout model vs baseline
        tours, log_probs = model(nodes, decode_type="sampling")
        with torch.no_grad():
            baseline_tours, _ = baseline_model(nodes, decode_type="greedy")

        # Compute traffic-aware dynamic tour cost: sum(dist_ij * avg_traffic)
        cost = calc_tour_cost(tours, coords, departure_hours)
        baseline_cost = calc_tour_cost(baseline_tours, coords, departure_hours)

        advantage = (cost - baseline_cost).detach()
        loss = (advantage * log_probs).mean()

        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        scheduler.step()

        # Update rollout baseline only after improvement on fixed validation instances.
        model.eval()
        val_features = torch.cat([
            val_coords,
            (compute_traffic_multiplier_tensor(val_departures).view(batch_size, 1, 1) / 2.25).expand(-1, val_nodes, -1),
        ], dim=-1)
        with torch.no_grad():
            model_tours, _ = model(val_features, decode_type="greedy")
            baseline_val_tours, _ = baseline_model(val_features, decode_type="greedy")
            val_diff = (
                calc_tour_cost(model_tours, val_coords, val_departures)
                - calc_tour_cost(baseline_val_tours, val_coords, val_departures)
            ).mean().item()
        if val_diff < -0.01:
            baseline_model.load_state_dict(model.state_dict())
        model.train()

        print(f"Epoch {ep:03d}/{epochs:03d} (N={n_nodes:02d}) | Loss: {loss.item():.4f} | Model Cost: {cost.mean().item():.3f} | Baseline Cost: {baseline_cost.mean().item():.3f} | Val Diff: {val_diff:+.4f}")

    out_file = save_dir / "attention_model_reproduce.pt"
    torch.save(model.state_dict(), out_file)
    print(f"Saved Attention Model weights to: {out_file}\n")


def main():
    parser = argparse.ArgumentParser(description="Unified Training Harness for Vietnam Routing Optimization")
    parser.add_argument("--model", type=str, choices=["dqn", "ptr", "am", "all"], default="all", help="Model architecture")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu", help="Device (cpu or cuda)")
    parser.add_argument("--save-dir", type=str, default="results/checkpoints", help="Output weights directory")
    args = parser.parse_args()

    save_path = Path(args.save_dir)

    if args.model in ["dqn", "all"]:
        train_dqn(args.epochs, args.batch_size, args.lr, args.device, save_path)
    if args.model in ["ptr", "all"]:
        train_pointer_net(args.epochs, args.batch_size, args.lr, args.device, save_path)
    if args.model in ["am", "all"]:
        train_attention_model(args.epochs, args.batch_size, args.lr, args.device, save_path)


if __name__ == "__main__":
    main()
