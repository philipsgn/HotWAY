"""Automated test suite for Neural TSP Attention Model (Kool et al., 2019)
and Live Traffic Fallback Adapter.
"""

import pytest
import torch
import numpy as np
from src.agents.attention_model.model import AttentionModel
from src.agents.attention_model.time_dependent_env import TimeDependentTSPEnv, get_congestion_factor
from src.services.neural_tsp_service import NeuralTSPService
from src.services.live_traffic_adapter import LiveTrafficAdapter


def test_attention_model_architecture():
    """Verify AttentionModel dimensions, forward pass, and permutation validity."""
    batch_size = 2
    n_nodes = 10
    input_dim = 3

    model = AttentionModel(input_dim=input_dim, embed_dim=64, n_heads=4, n_layers=2)
    model.eval()

    dummy_nodes = torch.randn(batch_size, n_nodes, input_dim)
    tours, log_probs = model(dummy_nodes, decode_type="greedy")

    assert tours.shape == (batch_size, n_nodes)
    assert log_probs.shape == (batch_size,)

    # Each tour must be a valid permutation of [0 .. n_nodes - 1]
    for b in range(batch_size):
        tour = tours[b].tolist()
        assert len(set(tour)) == n_nodes
        assert tour[0] == 0  # Starts at depot


def test_time_dependent_congestion_factor():
    """Verify empirical C(t) congestion factor curve."""
    assert get_congestion_factor(2.0) == 1.00   # Night off-peak
    assert get_congestion_factor(7.5) == 2.10   # Morning rush peak
    assert get_congestion_factor(12.0) == 1.35  # Mid-day rush
    assert get_congestion_factor(17.5) == 2.25  # Evening rush peak


def test_time_dependent_tsp_env():
    """Verify batch generation and tour evaluation in TimeDependentTSPEnv."""
    env = TimeDependentTSPEnv()
    batch = env.generate_batch(batch_size=4, n_nodes=15, seed=2026)

    assert "nodes" in batch
    assert batch["nodes"].shape == (4, 15, 3)

    # Evaluate a sample tour
    sample_tour = np.arange(15)
    sample_indices = batch["indices"][0]
    metrics = env.evaluate_tour(sample_tour, sample_indices, departure_hour=8.0)

    assert "duration_min" in metrics
    assert "distance_km" in metrics
    assert metrics["distance_km"] > 0
    assert metrics["duration_min"] > 0


def test_neural_tsp_service():
    """Verify NeuralTSPService produces valid solutions on CPU."""
    service = NeuralTSPService(model_path="results/attention_tsp50_hcmc.pt")
    
    depot = {"lat": 10.8016, "lon": 106.7115, "name": "Bưu cục Bình Thạnh"}
    stops = [
        {"id": "STOP_1", "lat": 10.8025, "lon": 106.7140, "demand": 1},
        {"id": "STOP_2", "lat": 10.7990, "lon": 106.7180, "demand": 2},
        {"id": "STOP_3", "lat": 10.8050, "lon": 106.7090, "demand": 1},
    ]

    res = service.solve(depot=depot, stops=stops, departure_hour=7.5)

    assert res["algorithm"] == "Attention Model (Kool et al., 2019)"
    assert len(res["tour_indices"]) == 4
    assert res["total_distance_km"] > 0
    assert res["total_duration_min"] > 0
    assert res["latency_ms"] < 200.0  # CPU microsecond/millisecond performance


def test_live_traffic_adapter_offline_fallback():
    """Verify 3-layer live traffic adapter gracefully falls back to synthetic offline."""
    adapter = LiveTrafficAdapter()
    
    # Query without external API keys should fall back to SYNTHETIC_OFFLINE
    res = adapter.get_segment_travel_time(
        origin_lat=10.8016,
        origin_lon=106.7115,
        dest_lat=10.8055,
        dest_lon=106.7128,
        departure_hour=8.0,
    )

    assert res["source"] == "SYNTHETIC_OFFLINE"
    assert res["distance_km"] > 0
    assert res["duration_min"] > 0
