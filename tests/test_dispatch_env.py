"""
Unit and Integration Tests for GĐ2 (DispatchEnv).
Verifies:
1. Determinism under fixed seed.
2. Order conservation (0 lost, 0 duplicates).
3. 5-state FSM compliance (only READY orders loaded).
4. Vehicle capacity constraint (<= Q).
5. Exact Bellman reward equivalence (|sum(r) - (-sum(W))| < 1e-9).
6. Clean termination through Drain Phase.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.envs.dispatch_env import DispatchEnv


def test_dispatch_env_determinism():
    """Verify that identical seeds produce identical order streams, states, and rewards."""
    env1 = DispatchEnv()
    obs1, info1 = env1.reset(seed=42)

    env2 = DispatchEnv()
    obs2, info2 = env2.reset(seed=42)

    assert info1["total_orders"] == info2["total_orders"]
    assert np.allclose(obs1, obs2)

    for step in range(25):
        # Deterministic periodic action
        ready1 = sum(1 for o in env1.orders if o["state"] == "READY")
        act1 = min(3, ready1) if ready1 > 0 else 0

        ready2 = sum(1 for o in env2.orders if o["state"] == "READY")
        act2 = min(3, ready2) if ready2 > 0 else 0

        assert act1 == act2
        o1, r1, term1, trunc1, _ = env1.step(act1)
        o2, r2, term2, trunc2, _ = env2.step(act2)

        assert np.allclose(o1, o2), f"Observations diverged at step {step}"
        assert abs(r1 - r2) < 1e-12, f"Rewards diverged at step {step}"
        assert term1 == term2
        if term1:
            break


def test_order_conservation_and_fsm():
    """Verify that all generated orders transition through proper FSM and are 100% delivered."""
    env = DispatchEnv()
    env.reset(seed=123)

    initial_order_ids = set(o["id"] for o in env.orders)
    total_orders = len(initial_order_ids)

    terminated = False
    truncated = False

    while not (terminated or truncated):
        ready = sum(1 for o in env.orders if o["state"] == "READY")
        act = min(4, ready) if ready > 0 else 0
        _, _, terminated, truncated, _ = env.step(act)

    assert terminated, "Episode must reach full termination"
    assert not truncated, "Episode must not be truncated prematurely"

    final_order_ids = set(o["id"] for o in env.orders)
    assert initial_order_ids == final_order_ids, "No orders can be lost or created"

    # Verify 100% delivered
    for o in env.orders:
        assert o["state"] == "DELIVERED", f"Order {o['id']} ended in state {o['state']}, expected DELIVERED"
        assert o["placed_time"] < o["ready_time"], "Placed time must precede ready time"
        assert o["dispatched_time"] is not None, "Dispatched time must be recorded"
        assert o["dispatched_time"] >= o["ready_time"] - 1e-9, "Order cannot be dispatched before READY"
        assert o["delivered_time"] is not None, "Delivered time must be recorded"
        assert o["delivered_time"] > o["dispatched_time"], "Delivered time must follow dispatch"


def test_capacity_constraint():
    """Verify that no driver is ever dispatched with more than Q orders."""
    env = DispatchEnv(vehicle_capacity=4)
    env.reset(seed=999)

    terminated = False
    truncated = False

    while not (terminated or truncated):
        # Intentionally attempt to dispatch oversized batch of 10 orders
        ready = sum(1 for o in env.orders if o["state"] == "READY")
        act = 10 if ready > 0 else 0
        _, _, terminated, truncated, step_info = env.step(act)
        assert step_info["dispatched_count"] <= 4, "Capacity Q=4 was violated!"


def test_bellman_reward_exact_equivalence():
    """Verify that |sum(r_k) - (-sum(W_i))| < 1e-9 across full episode."""
    env = DispatchEnv()
    env.reset(seed=777)

    terminated = False
    truncated = False

    while not (terminated or truncated):
        ready = sum(1 for o in env.orders if o["state"] == "READY")
        act = min(4, ready) if ready > 0 else 0
        _, _, terminated, truncated, _ = env.step(act)

    metrics = env.get_metrics()
    assert metrics["num_orders"] > 50, "Should simulate realistic day order volume"
    assert metrics["bellman_abs_error"] < 1e-9, (
        f"Bellman error {metrics['bellman_abs_error']} exceeded tolerance 1e-9! "
        f"true={metrics['true_sum_wait']}, reward={metrics['reward_sum_wait']}"
    )
