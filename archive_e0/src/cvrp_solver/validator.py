"""
Independent CVRP Validator.
Matches PROJECT_SPEC.md and validator.py from report:
- Recalculates total distance directly from cost matrix.
- Checks: missing/duplicate customers, invalid node IDs (including depot in routes),
  capacity violations (sum of demands <= Q), and max vehicle constraints (routes <= K).
- Feasibility here is an objective mathematical check; it does not imply optimality.
"""

from __future__ import annotations

from typing import List, Tuple
from src.cvrp_solver.problem import CVRPInstance, CVRPSolution


def calculate_route_distance(route: List[int], dist_matrix: List[List[float]]) -> float:
    """Calculates route distance including travel from and to depot (node 0)."""
    if not route:
        return 0.0
    cost = dist_matrix[0][route[0]]
    for i in range(len(route) - 1):
        cost += dist_matrix[route[i]][route[i + 1]]
    cost += dist_matrix[route[-1]][0]
    return cost


def validate_cvrp_solution(
    routes: List[List[int]],
    instance: CVRPInstance,
) -> Tuple[bool, float, str]:
    """
    Independently validates a CVRP solution.
    Returns (is_feasible, total_distance, message).
    """
    non_empty_routes = [r for r in routes if len(r) > 0]

    # Check vehicle count limit
    if len(non_empty_routes) > instance.max_vehicles:
        return (
            False,
            float("inf"),
            f"Vượt quá số xe tối đa: {len(non_empty_routes)} > {instance.max_vehicles}",
        )

    visited_customers = []
    total_dist = 0.0

    for r_idx, r in enumerate(non_empty_routes):
        route_load = 0
        for node in r:
            # Check valid customer node id
            if node <= 0 or node > instance.n_customers:
                return (
                    False,
                    float("inf"),
                    f"Mã điểm dừng không hợp lệ tại tuyến {r_idx}: node={node}",
                )
            route_load += instance.demands[node]
            visited_customers.append(node)

        # Check vehicle capacity
        if route_load > instance.capacity:
            return (
                False,
                float("inf"),
                f"Vượt quá sức chứa tại tuyến {r_idx}: tải={route_load} > sức_chứa={instance.capacity}",
            )

        # Recalculate route distance from matrix
        total_dist += calculate_route_distance(r, instance.dist_matrix)

    # Check that all customers 1..n are visited exactly once
    if len(visited_customers) != instance.n_customers:
        return (
            False,
            float("inf"),
            f"Số khách hàng phục vụ ({len(visited_customers)}) khác tổng số khách ({instance.n_customers})",
        )

    if len(set(visited_customers)) != instance.n_customers:
        return (
            False,
            float("inf"),
            "Có khách hàng bị trùng lặp giữa các tuyến",
        )

    return True, round(total_dist, 2), "Nghiệm hợp lệ và khả thi 100%"
