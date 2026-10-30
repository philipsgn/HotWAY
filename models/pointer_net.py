"""
Model 2: Pointer Network with Advantage Actor-Critic (A2C).
Sequential Transition Baseline: Demonstrates the progression from value-based methods (DQN)
to sequence-to-sequence policy mechanisms, while illustrating recurrent bottleneck latencies.
Based on Vinyals et al. (2015) and Bello et al. (2016).
"""

from __future__ import annotations

import math
import time
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from env.traffic_tsp_env import (
    TrafficTSPEnv,
    compute_traffic_multiplier,
    compute_traffic_multiplier_tensor,
    dynamic_isotropic_scale_latlon,
    simulate_route,
)


class AttentionPointer(nn.Module):
    """Additive Attention Pointer mechanism (Bahdanau-style) for pointing to graph nodes."""

    def __init__(self, hidden_dim: int = 128):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.w_enc = nn.Linear(hidden_dim, hidden_dim, bias=False)
        self.w_dec = nn.Linear(hidden_dim, hidden_dim, bias=False)
        self.v = nn.Linear(hidden_dim, 1, bias=False)

    def forward(
        self,
        encoder_outputs: torch.Tensor,  # (B, N, H)
        decoder_state: torch.Tensor,    # (B, H)
        mask: Optional[torch.Tensor] = None  # (B, N) True for valid, False for masked
    ) -> torch.Tensor:
        # encoder_proj: (B, N, H)
        enc_proj = self.w_enc(encoder_outputs)
        # dec_proj: (B, 1, H)
        dec_proj = self.w_dec(decoder_state).unsqueeze(1)

        # scores: (B, N)
        scores = self.v(torch.tanh(enc_proj + dec_proj)).squeeze(-1)
        scores = 10.0 * torch.tanh(scores / math.sqrt(self.hidden_dim))

        if mask is not None:
            scores = torch.where(mask, scores, torch.tensor(-1e9, device=scores.device, dtype=scores.dtype))
        return scores


class PointerNetwork(nn.Module):
    """
    Bi-directional LSTM Encoder + Unidirectional LSTM Decoder with Additive Attention Pointer.
    Includes parametric Critic head for A2C baseline.
    """

    def __init__(self, input_dim: int = 4, hidden_dim: int = 128):
        super().__init__()
        self.hidden_dim = hidden_dim

        # Project input features: [norm_lat, norm_lon, norm_dist_to_depot, congestion_weight]
        self.embedding = nn.Linear(input_dim, hidden_dim)

        # Bi-LSTM Encoder
        self.encoder = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim // 2,
            batch_first=True,
            bidirectional=True
        )

        # Decoder LSTM
        self.decoder_cell = nn.LSTMCell(input_size=hidden_dim + 3, hidden_size=hidden_dim)
        self.pointer = AttentionPointer(hidden_dim=hidden_dim)

        # Parametric Critic for A2C
        self.critic_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )

    def forward(
        self,
        node_inputs: torch.Tensor,      # (B, N, input_dim)
        mask: Optional[torch.Tensor] = None,
        deterministic: bool = True,
        departure_hours: Optional[torch.Tensor] = None,
        base_duration_matrix: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        B, N, _ = node_inputs.shape
        if departure_hours is None:
            departure_hours = torch.zeros(B, device=node_inputs.device, dtype=node_inputs.dtype)
        else:
            departure_hours = torch.as_tensor(
                departure_hours, device=node_inputs.device, dtype=node_inputs.dtype
            ).reshape(-1)
            if departure_hours.numel() == 1 and B > 1:
                departure_hours = departure_hours.expand(B)
            if departure_hours.numel() != B:
                raise ValueError("departure_hours must contain one value per graph")
        if base_duration_matrix is None:
            base_duration_matrix = torch.cdist(node_inputs[..., :2], node_inputs[..., :2]) * 36.0
        else:
            base_duration_matrix = torch.as_tensor(
                base_duration_matrix, device=node_inputs.device, dtype=node_inputs.dtype
            )
            if base_duration_matrix.ndim == 2:
                base_duration_matrix = base_duration_matrix.unsqueeze(0).expand(B, -1, -1)
            if base_duration_matrix.shape != (B, N, N):
                raise ValueError("base_duration_matrix must have shape (B, N, N) or (N, N)")

        # 1. Encode
        embedded = self.embedding(node_inputs)
        enc_outputs, (h_n, c_n) = self.encoder(embedded)

        # Graph representation for Critic
        graph_repr = enc_outputs.mean(dim=1)
        baseline_pred = self.critic_head(graph_repr).squeeze(-1)

        # 2. Decode sequentially
        dec_h = graph_repr
        dec_c = torch.zeros_like(dec_h)

        visited_mask = torch.ones(B, N, dtype=torch.bool, device=node_inputs.device)
        visited_mask[:, 0] = False  # Depot starts visited

        actions = []
        log_probs = []

        curr_input = embedded[:, 0, :]  # Start at depot embedding
        curr_node = torch.zeros(B, dtype=torch.long, device=node_inputs.device)
        elapsed_minutes = torch.zeros(B, device=node_inputs.device, dtype=node_inputs.dtype)
        batch_idx = torch.arange(B, device=node_inputs.device)

        for step in range(N - 1):
            current_hour = torch.remainder(departure_hours + elapsed_minutes / 60.0, 24.0)
            current_traffic = compute_traffic_multiplier_tensor(current_hour)
            angle = 2.0 * math.pi * current_hour / 24.0
            time_context = torch.stack(
                [torch.sin(angle), torch.cos(angle), current_traffic / 2.25], dim=-1
            )
            dec_input = torch.cat([curr_input, time_context], dim=-1)
            dec_h, dec_c = self.decoder_cell(dec_input, (dec_h, dec_c))

            # Point to next stop
            scores = self.pointer(enc_outputs, dec_h, visited_mask)
            probs = F.softmax(scores, dim=-1)

            if deterministic:
                action = torch.argmax(probs, dim=-1)
            else:
                dist = torch.distributions.Categorical(probs)
                action = dist.sample()

            log_p = torch.log(probs.gather(1, action.unsqueeze(1)) + 1e-9).squeeze(1)

            actions.append(action)
            log_probs.append(log_p)

            # Mask chosen action
            visited_mask = visited_mask.clone()
            visited_mask.scatter_(1, action.unsqueeze(1), False)
            leg_base = base_duration_matrix[batch_idx, curr_node, action]
            elapsed_minutes = elapsed_minutes + leg_base * current_traffic

            # Next step input is the embedding of the chosen node
            curr_node = action
            curr_input = embedded.gather(1, action.view(B, 1, 1).expand(B, 1, self.hidden_dim)).squeeze(1)

        # Final step: return to depot 0
        actions.append(torch.zeros(B, dtype=torch.long, device=node_inputs.device))

        action_seq = torch.stack(actions, dim=1)  # (B, N)
        total_log_prob = torch.stack(log_probs, dim=1).sum(dim=1)  # (B,)

        return action_seq, total_log_prob, baseline_pred


class PointerNetSolver:
    """Wrapper Solver for evaluation across the 100 POI benchmark."""

    def __init__(self, model: Optional[PointerNetwork] = None, weights_path: Optional[str] = None):
        self.device = torch.device("cpu")
        default_weights = Path("results/checkpoints/pointer_net_a2c.pt")
        target_weights = Path(weights_path) if weights_path else default_weights
        self.weights_loaded = model is not None
        self.weights_path = str(target_weights) if model is None else None
        if model is not None:
            self.model = model.to(self.device)
        else:
            self.model = PointerNetwork().to(self.device)
            if target_weights.exists():
                try:
                    self.model.load_state_dict(torch.load(target_weights, map_location="cpu", weights_only=True))
                    self.weights_loaded = True
                except Exception as e:
                    print(f"Notice: Could not load PointerNet weights ({e}), using initialized weights.")
        self.model.eval()

    def solve(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.perf_counter()

        num_stops = instance.get("num_stops", len(instance.get("stops", [])))
        total_nodes = num_stops + 1

        depot = instance.get("depot")
        if depot is None:
            raise ValueError("benchmark instance must include an explicit depot")
        raw_coords = [[depot["lat"], depot["lon"]]]
        for s in instance.get("stops", []):
            raw_coords.append([s["lat"], s["lon"]])
        coords = np.array(raw_coords, dtype=np.float32)

        norm_coords = dynamic_isotropic_scale_latlon(coords)

        # Feature tensor: [norm_lat, norm_lon, dist_depot, congestion]
        dep_hour = instance.get("departure_hour", 8.0)
        c_t = compute_traffic_multiplier(dep_hour)

        feats = np.zeros((total_nodes, 4), dtype=np.float32)
        feats[:, :2] = norm_coords
        feats[:, 2] = np.linalg.norm(norm_coords - norm_coords[0], axis=1)
        feats[:, 3] = c_t / 2.25

        node_tensor = torch.tensor(feats, dtype=torch.float32).unsqueeze(0)
        base_duration_matrix = torch.as_tensor(
            instance["duration_matrix_min"], dtype=torch.float32
        ).unsqueeze(0)

        with torch.no_grad():
            action_seq, _, _ = self.model(
                node_tensor,
                deterministic=True,
                departure_hours=torch.tensor([dep_hour], dtype=torch.float32),
                base_duration_matrix=base_duration_matrix,
            )
            route = action_seq.squeeze(0).cpu().tolist()
            if not route or route[0] != 0:
                route.insert(0, 0)
            if route[-1] != 0:
                route.append(0)

        solve_time_ms = (time.perf_counter() - start_time) * 1000.0

        # Calculate total distance and duration with dynamic traffic C(t)
        total_dist, total_dur = simulate_route(instance, route)

        return {
            "model": "Pointer Network (A2C)",
            "route": route,
            "total_dist_km": round(float(total_dist), 2),
            "total_duration_min": round(float(total_dur), 2),
            "solve_time_ms": round(solve_time_ms, 2),
            "valid": len(route) == total_nodes + 1 and len(set(route[:-1])) == total_nodes
        }

