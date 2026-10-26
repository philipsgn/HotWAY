"""
Unit Tests for Reinforcement Learning (Candidate Edge-Scoring DQN and Dynamic Baselines).
Verifies MLP scoring, feature extraction, replay buffer transitions, and policy actions.
"""

import numpy as np
import pytest
import torch

from src.envs.adaptive_routing_env import AdaptiveRoutingEnv
from src.traffic.provider import SyntheticProvider
from src.agents.candidate_edge_dqn import (
    CandidateEdgeScoringNetwork,
    EdgeScoringDQNAgent,
    extract_candidate_edge_features,
)
from src.agents.baseline_policies import (
    StaticDijkstraPolicy,
    DynamicDijkstraPolicy,
)


def test_edge_scoring_network_forward():
    net = CandidateEdgeScoringNetwork(in_features=10, hidden_dim=32)
    x = torch.randn(4, 10)
    out = net(x)
    assert out.shape == (4,)
    assert not torch.isnan(out).any()


def test_feature_extraction():
    env = AdaptiveRoutingEnv()
    obs, info = env.reset(seed=2026)
    curr = env.current_node
    target = env.target_node

    feats, succs = extract_candidate_edge_features(
        env, curr, target, prev_node=None, current_time_min=480.0
    )
    assert feats.shape[0] == len(succs)
    assert feats.shape[1] == 10
    assert not np.isnan(feats).any()


def test_edge_scoring_dqn_step_and_update():
    agent = EdgeScoringDQNAgent(in_features=10, hidden_dim=32, batch_size=4)
    # Populate buffer with dummy transitions
    for _ in range(10):
        curr_f = np.random.randn(10).astype(np.float32)
        r = float(np.random.uniform(-5.0, -0.5))
        next_f = np.random.randn(3, 10).astype(np.float32)
        done = bool(np.random.choice([True, False]))
        agent.store_transition(curr_f, r, next_f, done)

    loss = agent.update()
    assert loss is not None
    assert loss >= 0.0


def test_baseline_policies_execution():
    env = AdaptiveRoutingEnv()
    obs, info = env.reset(seed=2026)

    # Static Dijkstra
    static_pol = StaticDijkstraPolicy(env)
    static_pol.reset(env.current_node, env.target_node)
    a_static = static_pol.select_action(env.current_node)
    assert 0 <= a_static < len(env.adj[env.current_node])

    # Dynamic Dijkstra
    dyn_pol = DynamicDijkstraPolicy(env)
    a_dyn = dyn_pol.select_action(env.current_node, env.target_node)
    assert 0 <= a_dyn < len(env.adj[env.current_node])
