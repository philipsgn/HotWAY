"""
The 4 CVRP Local Search Operators (Matching Section 4.2 & Table 2 of Final Report):
Action 0: two_opt (Reverse segment route[r][i..j], exact asymmetric delta)
Action 1: intra_relocate (Move customer within same route)
Action 2: inter_relocate (Move customer from r1 to r2, checking capacity <= Q)
Action 3: inter_swap (Swap two customers between r1 and r2, checking capacities <= Q)

Candidate sampling: Evaluates up to 128 sampled moves per decision.
Strict improvement rule: Applies move only if delta < -1e-9 and capacity feasible.
"""

from __future__ import annotations

import random
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.cvrp_solver.problem import CVRPInstance
from src.cvrp_solver.validator import calculate_route_distance


def evaluate_two_opt_move(
    routes: List[List[int]],
    r_idx: int,
    i: int,
    j: int,
    dist_matrix: List[List[float]],
) -> Tuple[float, List[List[int]]]:
    """
    Evaluates 2-opt move on routes[r_idx] reversing segment from index i to j.
    Calculates exact asymmetric delta.
    """
    old_route = routes[r_idx]
    old_dist = calculate_route_distance(old_route, dist_matrix)

    # Reverse slice old_route[i : j + 1]
    new_route = old_route[:i] + old_route[i : j + 1][::-1] + old_route[j + 1:]
    new_dist = calculate_route_distance(new_route, dist_matrix)
    delta = new_dist - old_dist

    new_routes = [list(r) for r in routes]
    new_routes[r_idx] = new_route
    return delta, new_routes


def evaluate_intra_relocate_move(
    routes: List[List[int]],
    r_idx: int,
    i: int,
    j: int,
    dist_matrix: List[List[float]],
) -> Tuple[float, List[List[int]]]:
    """
    Moves customer at index i to position j in routes[r_idx].
    """
    old_route = routes[r_idx]
    old_dist = calculate_route_distance(old_route, dist_matrix)

    node = old_route[i]
    temp = [n for idx, n in enumerate(old_route) if idx != i]
    new_route = temp[:j] + [node] + temp[j:]
    new_dist = calculate_route_distance(new_route, dist_matrix)
    delta = new_dist - old_dist

    new_routes = [list(r) for r in routes]
    new_routes[r_idx] = new_route
    return delta, new_routes


def evaluate_inter_relocate_move(
    routes: List[List[int]],
    r1_idx: int,
    i: int,
    r2_idx: int,
    k: int,
    instance: CVRPInstance,
) -> Tuple[float, List[List[int]]]:
    """
    Moves customer routes[r1_idx][i] to position k of routes[r2_idx].
    Checks capacity constraint on r2.
    """
    node = routes[r1_idx][i]
    node_demand = instance.demands[node]

    # Check capacity on receiving route
    r2_curr_load = sum(instance.demands[n] for n in routes[r2_idx])
    if r2_curr_load + node_demand > instance.capacity:
        return 999999.0, routes

    dist_matrix = instance.dist_matrix
    old_dist_r1 = calculate_route_distance(routes[r1_idx], dist_matrix)
    old_dist_r2 = calculate_route_distance(routes[r2_idx], dist_matrix)

    new_r1 = [n for idx, n in enumerate(routes[r1_idx]) if idx != i]
    new_r2 = routes[r2_idx][:k] + [node] + routes[r2_idx][k:]

    new_dist_r1 = calculate_route_distance(new_r1, dist_matrix)
    new_dist_r2 = calculate_route_distance(new_r2, dist_matrix)

    delta = (new_dist_r1 + new_dist_r2) - (old_dist_r1 + old_dist_r2)

    new_routes = [list(r) for r in routes]
    new_routes[r1_idx] = new_r1
    new_routes[r2_idx] = new_r2

    # Remove empty routes if any
    new_routes = [r for r in new_routes if len(r) > 0]
    return delta, new_routes


def evaluate_inter_swap_move(
    routes: List[List[int]],
    r1_idx: int,
    i: int,
    r2_idx: int,
    j: int,
    instance: CVRPInstance,
) -> Tuple[float, List[List[int]]]:
    """
    Swaps customer routes[r1_idx][i] with routes[r2_idx][j].
    Checks capacity constraints on both routes.
    """
    node1 = routes[r1_idx][i]
    node2 = routes[r2_idx][j]
    d1 = instance.demands[node1]
    d2 = instance.demands[node2]

    load_r1 = sum(instance.demands[n] for n in routes[r1_idx])
    load_r2 = sum(instance.demands[n] for n in routes[r2_idx])

    if (load_r1 - d1 + d2 > instance.capacity) or (load_r2 - d2 + d1 > instance.capacity):
        return 999999.0, routes

    dist_matrix = instance.dist_matrix
    old_dist_r1 = calculate_route_distance(routes[r1_idx], dist_matrix)
    old_dist_r2 = calculate_route_distance(routes[r2_idx], dist_matrix)

    new_r1 = list(routes[r1_idx])
    new_r2 = list(routes[r2_idx])
    new_r1[i] = node2
    new_r2[j] = node1

    new_dist_r1 = calculate_route_distance(new_r1, dist_matrix)
    new_dist_r2 = calculate_route_distance(new_r2, dist_matrix)

    delta = (new_dist_r1 + new_dist_r2) - (old_dist_r1 + old_dist_r2)

    new_routes = [list(r) for r in routes]
    new_routes[r1_idx] = new_r1
    new_routes[r2_idx] = new_r2
    return delta, new_routes


def generate_candidate_moves(
    action: int,
    routes: List[List[int]],
    instance: CVRPInstance,
) -> List[Callable[[], Tuple[float, List[List[int]]]]]:
    """Generates all legal move closures for the specified operator."""
    closures = []

    if action == 0:
        # two_opt
        for r_idx, r in enumerate(routes):
            m = len(r)
            if m >= 2:
                for i in range(m - 1):
                    for j in range(i + 1, m):
                        closures.append(
                            lambda r_idx=r_idx, i=i, j=j: evaluate_two_opt_move(
                                routes, r_idx, i, j, instance.dist_matrix
                            )
                        )

    elif action == 1:
        # intra_relocate
        for r_idx, r in enumerate(routes):
            m = len(r)
            if m >= 2:
                for i in range(m):
                    for j in range(m):
                        if i != j and i != j - 1:
                            closures.append(
                                lambda r_idx=r_idx, i=i, j=j: evaluate_intra_relocate_move(
                                    routes, r_idx, i, j, instance.dist_matrix
                                )
                            )

    elif action == 2:
        # inter_relocate
        n_routes = len(routes)
        if n_routes >= 2:
            for r1_idx in range(n_routes):
                for r2_idx in range(n_routes):
                    if r1_idx != r2_idx:
                        for i in range(len(routes[r1_idx])):
                            for k in range(len(routes[r2_idx]) + 1):
                                closures.append(
                                    lambda r1=r1_idx, i=i, r2=r2_idx, k=k: evaluate_inter_relocate_move(
                                        routes, r1, i, r2, k, instance
                                    )
                                )

    elif action == 3:
        # inter_swap
        n_routes = len(routes)
        if n_routes >= 2:
            for r1_idx in range(n_routes - 1):
                for r2_idx in range(r1_idx + 1, n_routes):
                    for i in range(len(routes[r1_idx])):
                        for j in range(len(routes[r2_idx])):
                            closures.append(
                                lambda r1=r1_idx, i=i, r2=r2_idx, j=j: evaluate_inter_swap_move(
                                    routes, r1, i, r2, j, instance
                                )
                            )

    return closures


def best_move(
    action: int,
    routes: List[List[int]],
    instance: CVRPInstance,
    max_candidates: int = 128,
    rng: Optional[random.Random] = None,
) -> Tuple[bool, float, List[List[int]], int]:
    """
    Executes best_move matching Section 4.1 of the report:
    - Lists valid moves of the operator.
    - Samples up to max_candidates (128) without replacement.
    - Applies the feasible move with the smallest delta (< -1e-9), or preserves the solution.
    Returns (applied, best_delta, new_routes, evaluated_count).
    """
    closures = generate_candidate_moves(action, routes, instance)
    if not closures:
        return False, 0.0, routes, 0

    if rng is None:
        rng = random.Random()

    sample_size = min(len(closures), max_candidates)
    sampled_closures = rng.sample(closures, sample_size)

    best_delta = 0.0
    best_solution = routes
    applied = False

    for closure in sampled_closures:
        delta, cand_routes = closure()
        if delta < -1e-9 and delta < best_delta:
            best_delta = delta
            best_solution = cand_routes
            applied = True

    return applied, best_delta, best_solution, sample_size
