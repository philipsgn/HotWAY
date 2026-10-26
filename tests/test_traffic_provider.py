"""
Unit tests for TrafficProvider implementations (Synthetic, Replay, Live).
Verifies Markov row-sum conservation, seed determinism, physical bounds, and rain impact.
"""

import numpy as np
import pytest

from src.traffic.provider import (
    TrafficState,
    SyntheticProvider,
    ReplayProvider,
    LiveProvider,
)


def test_markov_matrix_stochastic_conservation():
    prov = SyntheticProvider(seed=2026)
    # Check normal hours matrix row sums
    for r in prov.trans_normal:
        assert np.isclose(np.sum(r), 1.0, atol=1e-9)

    # Check peak hours matrix row sums
    for r in prov.trans_peak:
        assert np.isclose(np.sum(r), 1.0, atol=1e-9)


def test_seed_determinism():
    prov1 = SyntheticProvider(seed=42)
    prov2 = SyntheticProvider(seed=42)

    speeds1 = [prov1.get_edge_speed_kph(1, 2, "primary", 480.0) for _ in range(20)]
    speeds2 = [prov2.get_edge_speed_kph(1, 2, "primary", 480.0) for _ in range(20)]

    assert np.allclose(speeds1, speeds2, atol=1e-9)


def test_physical_speed_bounds():
    prov = SyntheticProvider(seed=123, noise_sigma=0.30)
    for _ in range(100):
        spd = prov.get_edge_speed_kph(10, 20, "living_street", 500.0, rain=True)
        assert 3.0 <= spd <= 50.0, f"Speed {spd} violates physical bounds [3.0, 50.0]"


def test_rain_factor_inflation():
    prov = SyntheticProvider(seed=2026, noise_sigma=0.0)  # No noise to isolate rain effect
    prov.reset(seed=2026)
    t_dry = prov.get_edge_travel_time_sec(1, 2, length_m=100.0, highway="secondary", rain=False)

    prov.reset(seed=2026)
    t_wet = prov.get_edge_travel_time_sec(1, 2, length_m=100.0, highway="secondary", rain=True)

    ratio = t_wet / t_dry
    assert np.isclose(ratio, prov.rain_factor, atol=1e-4), f"Rain factor ratio {ratio} != {prov.rain_factor}"


def test_incident_degradation():
    prov = SyntheticProvider(seed=999, incident_prob=1.0)  # Guarantee incident
    state = prov.get_edge_state(100, 200, "primary", 450.0)
    assert state == TrafficState.CONGESTED


def test_live_provider_fallback_and_label():
    live_prov = LiveProvider(api_key=None)
    assert "MÔ PHỎNG" in live_prov.get_provider_label()
    assert "CẢNH BÁO" in live_prov.get_compliance_disclaimer()
    spd = live_prov.get_edge_speed_kph(1, 2, "tertiary")
    assert 3.0 <= spd <= 50.0
