"""
Unit & Mathematical Invariant Tests for AdaptiveRoutingEnv and ValueIterationSolver (Gate G2).
Verifies Gym API compliance, action masking, step invariant conservation, and Value Iteration ground truth vs Dijkstra.
"""

import networkx as nx
import numpy as np
import pytest

from src.envs.adaptive_routing_env import AdaptiveRoutingEnv, ValueIterationSolver
from src.traffic.provider import SyntheticProvider


def test_gym_api_compliance():
    env = AdaptiveRoutingEnv()
    obs, info = env.reset(seed=2026)

    assert obs.shape == env.observation_space.shape
    assert isinstance(info, dict)
    assert "action_mask" in info
    assert "current_node" in info

    # Take a step with valid action
    mask = info["action_mask"]
    valid_actions = np.where(mask)[0]
    assert len(valid_actions) > 0

    action = int(valid_actions[0])
    next_obs, reward, terminated, truncated, next_info = env.step(action)

    assert next_obs.shape == env.observation_space.shape
    assert reward <= 0.0, "Reward must be negative travel time"
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    assert "step_duration_sec" in next_info


def test_step_duration_reward_equality():
    """Bảo đảm đẳng thức tích lũy thưởng: Tổng thưởng = - Tổng thời gian hành trình (phút)."""
    env = AdaptiveRoutingEnv()
    obs, info = env.reset(seed=2026)

    total_rewards = 0.0
    for _ in range(5):
        mask = info["action_mask"]
        valid_actions = np.where(mask)[0]
        action = int(valid_actions[0])
        obs, reward, term, trunc, info = env.step(action)
        total_rewards += reward
        if term or trunc:
            break

    expected_total_min = info["total_travel_time_sec"] / 60.0
    assert np.isclose(total_rewards, -expected_total_min, atol=1e-5), (
        f"Cumulative reward {total_rewards} != -Total time min {-expected_total_min}"
    )


def test_value_iteration_ground_truth_vs_dijkstra():
    """
    Kiểm chứng giải tích tuyệt đối (Ground Truth):
    Khi triệt tiêu nhiễu giao thông (noise_sigma=0), nghiệm của quy hoạch động Bellman
    (Value Iteration) phải TRÙNG KHÍT 100% với đường ngắn nhất Dijkstra theo thời gian.
    """
    traffic = SyntheticProvider(seed=2026, noise_sigma=0.0, incident_prob=0.0)
    env = AdaptiveRoutingEnv(traffic_provider=traffic)

    target_node = env.nodes[-1]

    # Precompute deterministic edge costs once for both VI and Dijkstra
    edge_costs = {}
    G_time = nx.DiGraph()
    for u in env.nodes:
        for v in env.adj[u]:
            edge_data = env.graph[u][v]
            length_m = float(edge_data.get("length", 50.0))
            hw = str(edge_data.get("highway", "residential"))
            t_sec = traffic.get_edge_travel_time_sec(u, v, length_m, hw, time_of_day_min=480.0, rain=False)
            c_min = t_sec / 60.0
            edge_costs[(u, v)] = c_min
            G_time.add_edge(u, v, weight=c_min)

    solver = ValueIterationSolver(env, discount_gamma=1.0, epsilon=1e-9)
    V_star, policy = solver.solve(target_node=target_node, edge_costs=edge_costs)

    dijkstra_lengths = nx.single_source_dijkstra_path_length(
        G_time.reverse(), target_node, weight="weight"
    )

    for n in env.nodes:
        if n in dijkstra_lengths:
            v_dp = V_star[n]
            v_dijkstra = dijkstra_lengths[n]
            assert np.isclose(v_dp, v_dijkstra, atol=1e-7), (
                f"Node {n}: DP V* {v_dp} != Dijkstra {v_dijkstra}"
            )
