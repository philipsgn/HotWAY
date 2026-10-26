"""
Constructive Heuristics for CVRP:
1. Clarke-Wright Savings Algorithm (Asymmetric Road Distance).
2. Nearest Neighbor Heuristic.
"""

from __future__ import annotations

from typing import List, Tuple
from src.cvrp_solver.problem import CVRPInstance


def clarke_wright_savings(instance: CVRPInstance) -> List[List[int]]:
    """
    Constructs an initial CVRP solution using the Clarke-Wright Savings method.
    Adapted for asymmetric road distance matrices:
    Saving s(i, j) = C(i, 0) + C(0, j) - C(i, j).
    """
    n = instance.n_customers
    dist = instance.dist_matrix
    demands = instance.demands
    capacity = instance.capacity

    # Compute savings for all pairs (i, j), i != j
    savings: List[Tuple[float, int, int]] = []
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if i != j:
                s = dist[i][0] + dist[0][j] - dist[i][j]
                savings.append((s, i, j))

    # Sort descending by savings
    savings.sort(key=lambda x: x[0], reverse=True)

    # Initial solution: each customer has its own route
    routes: List[List[int]] = [[i] for i in range(1, n + 1)]

    def find_route(node: int) -> int:
        for idx, r in enumerate(routes):
            if node in r:
                return idx
        return -1

    for s_val, i, j in savings:
        r_i_idx = find_route(i)
        r_j_idx = find_route(j)

        if r_i_idx == -1 or r_j_idx == -1 or r_i_idx == r_j_idx:
            continue

        r_i = routes[r_i_idx]
        r_j = routes[r_j_idx]

        # Check capacity constraint
        load_i = sum(demands[k] for k in r_i)
        load_j = sum(demands[k] for k in r_j)
        if load_i + load_j > capacity:
            continue

        # Merge condition: i must be the end of r_i and j must be the start of r_j
        if r_i[-1] == i and r_j[0] == j:
            new_route = r_i + r_j
            routes.pop(max(r_i_idx, r_j_idx))
            routes.pop(min(r_i_idx, r_j_idx))
            routes.append(new_route)

    return [r for r in routes if len(r) > 0]


def nearest_neighbor_constructive(instance: CVRPInstance) -> List[List[int]]:
    """
    Constructs an initial CVRP solution using Nearest Neighbor.
    Greedily visits the closest unvisited customer subject to capacity.
    """
    n = instance.n_customers
    dist = instance.dist_matrix
    demands = instance.demands
    capacity = instance.capacity

    unvisited = set(range(1, n + 1))
    routes: List[List[int]] = []

    while unvisited:
        curr_route: List[int] = []
        curr_load = 0
        curr_node = 0 # depot

        while unvisited:
            # Find closest feasible unvisited customer
            feasible_candidates = [
                c for c in unvisited if curr_load + demands[c] <= capacity
            ]
            if not feasible_candidates:
                break

            next_node = min(feasible_candidates, key=lambda c: dist[curr_node][c])
            curr_route.append(next_node)
            curr_load += demands[next_node]
            unvisited.remove(next_node)
            curr_node = next_node

        if curr_route:
            routes.append(curr_route)
        else:
            # Safety break if cannot pack remaining customers
            break

    return routes
