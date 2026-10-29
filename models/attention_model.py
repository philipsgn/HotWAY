"""
Model 3: Attention Model - AM (Graph Multi-Head Transformer with Dynamic Context Pointer Decoder).
Proposed Champion Core Architecture: Permutation-invariant, sub-15ms CPU inference,
seamless zero-shot transferability across graph sizes (N=10, 20, 30, 50).
Based on Kool et al. (ICLR 2019).
Upgraded with Dynamic Min-Max Scaling (per-instance) and Adaptive Architecture Detection.
"""

from __future__ import annotations

import math
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from env.traffic_tsp_env import compute_traffic_multiplier, simulate_route
from src.agents.attention_model.model import AttentionModel as CoreAttentionModel


class AttentionModelSolver:
    """Wrapper Solver for evaluation across the 100 POI benchmark."""

    def __init__(self, model: Optional[CoreAttentionModel] = None, weights_path: Optional[str] = None):
        self.device = torch.device("cpu")
        default_weights = Path("results/attention_tsp50_hcmc.pt")
        target_weights = Path(weights_path) if weights_path else default_weights
        self.weights_loaded = model is not None
        self.weights_path = str(target_weights) if model is None else None

        if model is not None:
            self.model = model.to(self.device)
        else:
            loaded = False
            if target_weights.exists():
                try:
                    state_dict = torch.load(target_weights, map_location="cpu", weights_only=True)
                    # Dynamically detect embed_dim and number of layers from state_dict
                    embed_dim = state_dict["encoder.init_embed.weight"].shape[0]
                    layer_keys = [k for k in state_dict.keys() if k.startswith("encoder.layers.") and k.endswith(".norm1.weight")]
                    n_layers = max(1, len(layer_keys))
                    self.model = CoreAttentionModel(input_dim=3, embed_dim=embed_dim, n_heads=8, n_layers=n_layers).to(self.device)
                    self.model.load_state_dict(state_dict)
                    loaded = True
                    self.weights_loaded = True
                except Exception:
                    loaded = False

            if not loaded:
                # Default gold standard: 128-d, 3 layers, 8 heads
                self.model = CoreAttentionModel(input_dim=3, embed_dim=128, n_heads=8, n_layers=3).to(self.device)

        self.model.eval()

    def solve(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.perf_counter()

        num_stops = instance.get("num_stops", len(instance.get("stops", [])))
        total_nodes = num_stops + 1

        depot = instance.get("depot", {"lat": 10.8012, "lon": 106.7145})
        raw_coords = [[depot["lat"], depot["lon"]]]
        for s in instance.get("stops", []):
            raw_coords.append([s["lat"], s["lon"]])
        coords = np.array(raw_coords, dtype=np.float32)

        dep_hour = float(instance.get("departure_hour", 8.0))

        # 3-feature input: [norm_lat, norm_lon, normalized_traffic_factor]
        # DYNAMIC MIN-MAX SCALING PER-INSTANCE (Eliminates Regional Distribution Shift)
        lat_min, lat_max = float(coords[:, 0].min()), float(coords[:, 0].max())
        lon_min, lon_max = float(coords[:, 1].min()), float(coords[:, 1].max())
        lat_range = max(lat_max - lat_min, 1e-6)
        lon_range = max(lon_max - lon_min, 1e-6)

        features = np.zeros((total_nodes, 3), dtype=np.float32)
        features[:, 0] = (coords[:, 0] - lat_min) / lat_range
        features[:, 1] = (coords[:, 1] - lon_min) / lon_range

        # Feature 3: Normalized traffic congestion factor C(t) in [0, 1]
        traffic_mult = compute_traffic_multiplier(dep_hour)
        features[:, 2] = traffic_mult / 2.25

        node_tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0)

        model_device = next(self.model.parameters()).device
        if model_device.type == "cuda":
            torch.cuda.synchronize(model_device)
        inference_start = time.perf_counter()
        with torch.no_grad():
            tours, _ = self.model(node_tensor, decode_type="greedy")
            perm = tours.squeeze(0).tolist()
        if model_device.type == "cuda":
            torch.cuda.synchronize(model_device)
        inference_latency_ms = (time.perf_counter() - inference_start) * 1000.0

        solve_time_ms = (time.perf_counter() - start_time) * 1000.0

        # Construct full tour starting and ending at depot 0
        tour = [0]
        for idx in perm:
            if idx != 0:
                tour.append(int(idx))
        tour.append(0)

        # Calculate actual dynamic travel duration and distance
        dist_mat = np.array(instance["dist_matrix_km"], dtype=np.float32)
        total_dist, total_dur = simulate_route(instance, tour)

        return {
            "model": "Attention Model (Graph Transformer)",
            "route": tour,
            "total_dist_km": round(float(total_dist), 2),
            "total_duration_min": round(float(total_dur), 2),
            "inference_latency_ms": round(inference_latency_ms, 2),
            "solve_time_ms": round(solve_time_ms, 2),
            "valid": len(tour) == total_nodes + 1 and len(set(tour[:-1])) == total_nodes
        }
