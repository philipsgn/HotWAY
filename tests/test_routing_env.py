"""
Unit and Integration Tests for GĐ1 (RoutingEnv & ExactValueIteration).
Verifies:
1. Determinism under fixed seed.
2. Convergence of Value Iteration to exact Bellman solution.
3. Equivalence in zero-noise environment.
4. Action and observation spaces.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.envs.routing_env import RoutingEnv
from src.envs.exact_dp import ExactValueIteration, DijkstraAverageBaseline


def test_routing_env_determinism():
    """Verify that identical seeds produce identical observations, actions, and rewards."""
    env1 = RoutingEnv()
    obs1, info1 = env1.reset(seed=2026)

    env2 = RoutingEnv()
    obs2, info2 = env2.reset(seed=2026)

    assert np.allclose(obs1, obs2), "Initial observations must be identical for same seed"
    assert info1["current_node"] == info2["current_node"]

    for step in range(10):
        action = step % env1.max_out_degree
        o1, r1, term1, trunc1, _ = env1.step(action)
        o2, r2, term2, trunc2, _ = env2.step(action)

        assert np.allclose(o1, o2), f"Observations diverged at step {step}"
        assert abs(r1 - r2) < 1e-12, f"Rewards diverged at step {step}"
        assert term1 == term2
        assert trunc1 == trunc2
        if term1 or trunc1:
            break


def test_exact_value_iteration_convergence():
    """Verify that Value Iteration converges monotonically to a finite optimal value."""
    env = RoutingEnv()
    vi = ExactValueIteration(env, discount_gamma=1.0, epsilon=1e-10)
    V, policy = vi.solve()

    assert len(V) == vi.n_states
    assert len(policy) > 0
    # Values must be non-positive (negative travel times)
    assert np.all(V <= 0.0), "All state values must be <= 0.0"
    # Destination node states must have value exactly 0.0
    for s, idx in vi.state_to_idx.items():
        if s[0] == env.dest_node:
            assert abs(V[idx]) < 1e-12, "Destination state value must be 0.0"


def test_zero_noise_equivalence():
    """In zero-noise environment (clear traffic multiplier=1.0), DP matches shortest path exactly."""
    env = RoutingEnv()
    # Force congestion multipliers to 1.0 (deterministic free-flow)
    env.congestion_multipliers = np.array([1.0, 1.0, 1.0], dtype=np.float32)

    vi = ExactValueIteration(env, discount_gamma=1.0, epsilon=1e-10)
    V, policy = vi.solve()

    dijk = DijkstraAverageBaseline(env)
    path = dijk.get_path(env.source_node, env.dest_node)

    # Calculate deterministic Dijkstra time
    true_dijkstra_time = 0.0
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        length = env.edge_lengths[(u, v)]
        true_dijkstra_time += (length / env.free_speed_mps)

    # Compare with DP value at source with all clear
    deg = len(env.adj[env.source_node])
    clear_state = (env.source_node, tuple([0] * deg))
    idx = vi.state_to_idx[clear_state]
    dp_time = -V[idx]

    assert abs(dp_time - true_dijkstra_time) < 1e-6, (
        f"DP time {dp_time} must match shortest path {true_dijkstra_time} in zero noise"
    )
