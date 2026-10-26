"""
F28 State Representation (28-dimensional Feature Vector)
Matching Table 3 and Section 4.3 of the Final Report:
- Global features (cost_ratio, routes/K, load utils, edge statistics).
- Dynamic progress features (step/max_actions, no_improve_streak with fixed feature_patience=30).
- Operator history (frequencies, success rates, last action one-hot, last success).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List
import numpy as np

from src.cvrp_solver.problem import CVRPInstance
from src.cvrp_solver.validator import calculate_route_distance


def compute_f28_state(
    routes: List[List[int]],
    current_cost: float,
    init_cost: float,
    best_cost: float,
    step: int,
    max_steps: int,
    no_improve_streak: int,
    feature_patience: int,
    action_counts: List[int],
    action_successes: List[int],
    last_action: int,
    last_success: bool,
    instance: CVRPInstance,
) -> np.ndarray:
    """
    Computes the 28-dimensional state vector F28.
    """
    f = np.zeros(28, dtype=np.float32)

    # 1. Cost & Fleet Features
    safe_init = max(init_cost, 1.0)
    cost_ratio = current_cost / safe_init
    f[0] = np.clip(cost_ratio, 0.0, 2.0)

    n_routes = len(routes)
    f[1] = n_routes / max(instance.max_vehicles, 1)

    # Route distance stats
    route_costs = [calculate_route_distance(r, instance.dist_matrix) for r in routes]
    if route_costs:
        max_route_cost = max(route_costs)
        mean_route_cost = np.mean(route_costs)
        std_route_cost = np.std(route_costs)
        f[2] = max_route_cost / max(current_cost, 1.0)
        f[3] = std_route_cost / max(mean_route_cost, 1.0)
    else:
        f[2] = 0.0
        f[3] = 0.0

    # 2. Capacity & Load Stats
    loads = [sum(instance.demands[n] for n in r) for r in routes]
    q = instance.capacity
    if loads:
        utils = [l / q for l in loads]
        f[4] = float(np.mean(utils))
        f[5] = float(np.max(utils))
        f[6] = float(np.min(utils))
        f[7] = float(np.std(utils) / max(np.mean(utils), 1e-6))
    else:
        f[4] = f[5] = f[6] = f[7] = 0.0

    # 3. Edge length stats
    edge_lengths = []
    for r in routes:
        if r:
            edge_lengths.append(instance.dist_matrix[0][r[0]])
            for k in range(len(r) - 1):
                edge_lengths.append(instance.dist_matrix[r[k]][r[k + 1]])
            edge_lengths.append(instance.dist_matrix[r[-1]][0])

    # Instance diameter estimate
    max_d = max(max(row) for row in instance.dist_matrix) if instance.dist_matrix else 1.0
    safe_diam = max(max_d, 1.0)

    if edge_lengths:
        f[8] = float(np.mean(edge_lengths) / safe_diam)
        f[9] = float(np.max(edge_lengths) / safe_diam)
        f[10] = float(np.std(edge_lengths) / safe_diam)
    else:
        f[8] = f[9] = f[10] = 0.0

    f[11] = 1.0 # normalized diameter baseline

    # 4. Search Progress Features
    f[12] = step / max(max_steps, 1)

    # Detached no_improve_streak (fixed feature_patience=30)
    f[13] = min(1.0, no_improve_streak / max(feature_patience, 1))

    # 5. Operator Frequencies (4 actions: two_opt, intra, inter_relocate, inter_swap)
    total_actions = max(sum(action_counts), 1)
    for a in range(4):
        f[14 + a] = action_counts[a] / total_actions

    # 6. Operator Success Rates (4 actions)
    for a in range(4):
        denom = max(action_counts[a], 1)
        f[18 + a] = action_successes[a] / denom

    # 7. Last Action One-Hot (4 actions)
    if 0 <= last_action < 4:
        f[22 + last_action] = 1.0

    # 8. Last Action Success
    f[26] = 1.0 if last_success else 0.0

    # 9. Current Best Gap
    f[27] = (current_cost - best_cost) / safe_init

    return f
