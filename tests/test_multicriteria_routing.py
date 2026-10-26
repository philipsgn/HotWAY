"""
Unit & Property Tests for T1 Multi-Criteria Motorbike Routing.
Verifies strongly connected subgraph properties, Pareto dominance logic,
Monte Carlo p90 consistency, and turn classification.
"""

import pytest
import networkx as nx
import numpy as np

from src.routing.multicriteria_router import (
    MultiCriteriaRouter,
    turn_classification,
    calculate_bearing,
)


def test_turn_classification():
    # Heading North (0 deg) -> heading North (0 deg) = STRAIGHT
    assert turn_classification(0.0, 0.0) == "STRAIGHT"
    # Heading North (0 deg) -> heading East (90 deg) = RIGHT
    assert turn_classification(0.0, 90.0) == "RIGHT"
    # Heading North (0 deg) -> heading West (270 deg) = LEFT
    assert turn_classification(0.0, 270.0) == "LEFT"
    # Heading North (0 deg) -> heading South (180 deg) = UTURN
    assert turn_classification(0.0, 180.0) == "UTURN"


def test_subgraph_extraction_and_properties():
    router = MultiCriteriaRouter.from_hcmc_subgraph(radius_km=1.2)
    G = router.graph

    assert isinstance(G, nx.DiGraph)
    assert G.number_of_nodes() > 200
    assert nx.is_strongly_connected(G), "Extracted subgraph must be strongly connected"

    # Verify precomputed attributes
    for u, v, d in G.edges(data=True):
        assert "travel_time_sec" in d
        assert "comfort_cost" in d
        assert "stable_cost" in d
        assert d["travel_time_sec"] > 0


def test_t1_routing_and_pareto_archetypes():
    router = MultiCriteriaRouter.from_hcmc_subgraph(radius_km=1.2)
    o, d = 1497276525, 5337055581

    labeled = router.select_four_labeled_routes(o, d, k_candidates=15)
    assert len(labeled) == 4
    for key in ["fastest", "shortest", "stable", "easiest"]:
        assert key in labeled
        route = labeled[key]
        assert route["distance_m"] > 0
        assert route["expected_time_min"] > 0
        # Invariant: p90 travel time must be greater than or equal to expected travel time
        assert route["p90_time_min"] >= route["expected_time_min"] - 1e-4
        assert route["path_nodes"][0] == o
        assert route["path_nodes"][-1] == d


def test_pareto_dominance_logic():
    router = MultiCriteriaRouter(nx.DiGraph())
    # r1 dominates r2 if r1 is better or equal in all and strictly better in at least one
    r_good = {
        "distance_m": 1000.0,
        "expected_time_min": 10.0,
        "p90_time_min": 11.0,
        "num_left_turns": 2,
        "ease_penalty_score": 15.0,
    }
    r_bad = {
        "distance_m": 1200.0,
        "expected_time_min": 12.0,
        "p90_time_min": 13.0,
        "num_left_turns": 4,
        "ease_penalty_score": 25.0,
    }
    r_tradeoff = {
        "distance_m": 900.0,  # Shorter distance
        "expected_time_min": 14.0,  # Slower
        "p90_time_min": 15.0,
        "num_left_turns": 5,
        "ease_penalty_score": 20.0,
    }

    pareto = router.filter_pareto([r_good, r_bad, r_tradeoff])
    # r_bad should be pruned, while r_good and r_tradeoff must remain in Pareto set
    assert r_good in pareto
    assert r_tradeoff in pareto
    assert r_bad not in pareto
