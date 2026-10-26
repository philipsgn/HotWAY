"""
Permutation Router and Order Bundler for HotWAY GĐ2.
Implements:
1. Seed selection: oldest READY order.
2. Detour-constrained greedy bundling.
3. Exhaustive permutation search (m! <= 120) minimizing sum of customer arrival timestamps.
"""

from __future__ import annotations

import itertools
from typing import Dict, List, Tuple, Any, Optional
import numpy as np


def check_detour(
    root_idx: int,
    cand_idx: int,
    dist_matrix: np.ndarray,
    max_detour_km: float = 1.5,
) -> bool:
    """
    Checks detour: d(0, root) + d(root, cand) - d(0, cand) <= max_detour_m
    """
    d_0_root = dist_matrix[0, root_idx]
    d_root_cand = dist_matrix[root_idx, cand_idx]
    d_0_cand = dist_matrix[0, cand_idx]
    detour_m = (d_0_root + d_root_cand) - d_0_cand
    return bool(detour_m <= (max_detour_km * 1000.0))


def bundle_orders(
    ready_orders: List[Dict[str, Any]],
    dist_matrix: np.ndarray,
    target_m: int = 4,
    max_detour_km: float = 1.5,
) -> List[Dict[str, Any]]:
    """
    Selects up to target_m orders from ready_orders:
    - Root order: the oldest ready order.
    - Additional orders: nearest to current cluster satisfying detour threshold.
    """
    if not ready_orders:
        return []
    if len(ready_orders) <= target_m and target_m == 1:
        # Just oldest order
        oldest = max(ready_orders, key=lambda o: o["order_age"])
        return [oldest]

    # Sort ready orders by age descending (oldest first)
    sorted_orders = sorted(ready_orders, key=lambda o: o["order_age"], reverse=True)
    root = sorted_orders[0]
    bundled = [root]
    root_loc = root["address_idx"]

    # Candidate pool for bundling
    remaining = sorted_orders[1:]
    # Sort remaining by distance to root
    remaining.sort(key=lambda o: dist_matrix[root_loc, o["address_idx"]])

    for cand in remaining:
        if len(bundled) >= target_m:
            break
        cand_loc = cand["address_idx"]
        if check_detour(root_loc, cand_loc, dist_matrix, max_detour_km=max_detour_km):
            bundled.append(cand)

    return bundled


def route_batch_exhaustive(
    bundled_orders: List[Dict[str, Any]],
    time_matrix: np.ndarray,
    current_time: float,
    service_time_min: float = 3.0,
    rain_factor: float = 1.0,
) -> Dict[str, Any]:
    """
    Finds the exact permutation pi* in P_m minimizing sum of delivery timestamps.
    Returns:
    - best_perm: ordered list of orders
    - delivery_times: dict of order_id -> arrival timestamp
    - driver_return_time: float
    - tour_distance_km: float (travel only)
    """
    m = len(bundled_orders)
    if m == 0:
        return {
            "ordered_orders": [],
            "delivery_times": {},
            "driver_return_time": current_time,
            "tour_travel_time": 0.0,
        }

    if m == 1:
        o = bundled_orders[0]
        loc = o["address_idx"]
        t_leg1 = time_matrix[0, loc] * rain_factor
        t_delivery = current_time + t_leg1
        t_leg2 = time_matrix[loc, 0] * rain_factor
        t_return = t_delivery + service_time_min + t_leg2
        return {
            "ordered_orders": [o],
            "delivery_times": {o["id"]: t_delivery},
            "driver_return_time": t_return,
            "tour_travel_time": t_leg1 + t_leg2,
        }

    best_sum_arr = float("inf")
    best_perm: Optional[Tuple[Dict[str, Any], ...]] = None
    best_deliveries: Dict[int, float] = {}
    best_return = current_time
    best_travel = 0.0

    # Exhaustive search over all m! permutations (m <= 5 -> at most 120 iterations)
    for perm in itertools.permutations(bundled_orders):
        t_cursor = current_time
        curr_loc = 0  # depot
        sum_arr = 0.0
        deliv_times = {}
        travel_time_acc = 0.0

        for order in perm:
            next_loc = order["address_idx"]
            leg_time = time_matrix[curr_loc, next_loc] * rain_factor
            travel_time_acc += leg_time
            arr_time = t_cursor + leg_time
            deliv_times[order["id"]] = arr_time
            sum_arr += arr_time
            t_cursor = arr_time + service_time_min
            curr_loc = next_loc

        # Return to depot
        ret_leg = time_matrix[curr_loc, 0] * rain_factor
        travel_time_acc += ret_leg
        ret_time = t_cursor + ret_leg

        if sum_arr < best_sum_arr:
            best_sum_arr = sum_arr
            best_perm = perm
            best_deliveries = deliv_times
            best_return = ret_time
            best_travel = travel_time_acc

    return {
        "ordered_orders": list(best_perm) if best_perm is not None else bundled_orders,
        "delivery_times": best_deliveries,
        "driver_return_time": best_return,
        "tour_travel_time": best_travel,
    }
