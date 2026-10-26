"""
CVRP Local Search Engine & Unified Strategy Runner.
Implements the 7 methods:
1. Clarke-Wright (baseline constructive)
2. Random (uniform random operator)
3. Cyclic (two_opt -> intra -> inter_relocate -> inter_swap)
4. Greedy (evaluates all 4 with 32 candidates each, applies best)
5. DQN (agent choosing operator via Q-network with F28 state)
6. Double DQN (agent choosing operator via Double DQN Q-network)
7. OR-Tools (Guided Local Search reference)

Tracks step-by-step search traces for the Search Replay interface.
Integrates Newton thermal constraints and detailed road route geometries.
"""

from __future__ import annotations

import logging
import math
import random
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from src.cvrp_solver.constructive import clarke_wright_savings
from src.cvrp_solver.operators import best_move
from src.cvrp_solver.problem import (
    CVRPInstance,
    CVRPSolution,
    RouteStopInfo,
    VehicleRoute,
)
from src.cvrp_solver.q_network import QNetworkInference
from src.cvrp_solver.state_f28 import compute_f28_state
from src.cvrp_solver.validator import calculate_route_distance, validate_cvrp_solution

logger = logging.getLogger("cvrp_search")

OPERATOR_NAMES = ["two_opt", "intra_relocate", "inter_relocate", "inter_swap"]


def calculate_thermal_profile(
    route: List[int],
    instance: CVRPInstance,
    t0_c: float = 85.0,
    tenv_c: float = 30.0,
    k_rate: float = 0.020,
    min_temp: float = 60.0,
    service_time_sec: float = 180.0,
) -> Tuple[List[RouteStopInfo], float, int]:
    """
    Computes arrival time, elapsed time, and Newton estimated temperature at each stop.
    T(t) = Tenv + (T0 - Tenv) * exp(-k * t_min).
    """
    stops: List[RouteStopInfo] = []
    curr_time_sec = 0.0
    violations_count = 0
    curr_node = 0 # depot
    remaining_load = sum(instance.demands[n] for n in route)

    for node in route:
        leg_time = instance.time_matrix[curr_node][node]
        curr_time_sec += leg_time
        elapsed_min = curr_time_sec / 60.0

        # Newton Cooling Law
        est_temp = tenv_c + (t0_c - tenv_c) * math.exp(-k_rate * elapsed_min)
        est_temp = round(est_temp, 1)

        is_violated = est_temp < min_temp
        if is_violated:
            violations_count += 1

        demand = instance.demands[node]
        remaining_load -= demand

        stop_obj = instance.stops[node] if node < len(instance.stops) else None
        order_id = stop_obj.order_id if stop_obj else f"ORD-{node}"
        lat = instance.coords[node][0]
        lon = instance.coords[node][1]

        stops.append(
            RouteStopInfo(
                node_idx=node,
                order_id=order_id,
                lat=lat,
                lon=lon,
                arrival_time_sec=round(curr_time_sec, 1),
                elapsed_time_min=round(elapsed_min, 1),
                demand=demand,
                remaining_load=remaining_load,
                estimated_temp_c=est_temp,
                thermal_violation=is_violated,
            )
        )

        curr_time_sec += service_time_sec
        curr_node = node

    # Add return to depot time
    curr_time_sec += instance.time_matrix[curr_node][0]
    return stops, curr_time_sec, violations_count


def solve_cvrp_strategy(
    strategy: str,
    instance: CVRPInstance,
    max_steps: int = 100,
    max_candidates: int = 128,
    feature_patience: int = 30,
    seed: int = 42,
    leg_geometries: Optional[List[List[List[List[float]]]]] = None,
    t0_c: float = 85.0,
    tenv_c: float = 30.0,
    k_rate: float = 0.020,
    min_temp: float = 60.0,
) -> CVRPSolution:
    """
    Executes CVRP optimization with the chosen strategy.
    """
    rng = random.Random(seed)
    start_time = time.time()

    # 1. Initial constructive solution: Clarke-Wright Savings
    init_routes = clarke_wright_savings(instance)
    current_routes = [list(r) for r in init_routes]
    current_cost = sum(calculate_route_distance(r, instance.dist_matrix) for r in current_routes)
    init_cost = current_cost
    best_routes = [list(r) for r in current_routes]
    best_cost = current_cost

    search_trace: List[Dict[str, Any]] = [
        {
            "step": 0,
            "action": -1,
            "operator": "init_clarke_wright",
            "applied": True,
            "delta": 0.0,
            "cost": round(current_cost, 1),
            "best_cost": round(best_cost, 1),
            "routes": [list(r) for r in current_routes],
        }
    ]

    # If Clarke-Wright alone is requested, return early
    if strategy.lower() in ["clarke_wright", "cw"]:
        return build_solution_result(
            best_routes, instance, search_trace, leg_geometries, t0_c, tenv_c, k_rate, min_temp
        )

    # 2. OR-Tools Reference Solver
    if strategy.lower() in ["ortools", "gls"]:
        try:
            from ortools.constraint_solver import routing_enums_pb2, pywrapcp

            manager = pywrapcp.RoutingIndexManager(
                instance.n_customers + 1, instance.max_vehicles, 0
            )
            routing = pywrapcp.RoutingModel(manager)

            def distance_callback(from_index: int, to_index: int) -> int:
                from_node = manager.IndexToNode(from_index)
                to_node = manager.IndexToNode(to_index)
                return int(instance.dist_matrix[from_node][to_node])

            transit_callback_index = routing.RegisterTransitCallback(distance_callback)
            routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

            def demand_callback(from_index: int) -> int:
                from_node = manager.IndexToNode(from_index)
                return instance.demands[from_node]

            demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
            routing.AddDimensionWithVehicleCapacity(
                demand_callback_index,
                0,
                [instance.capacity] * instance.max_vehicles,
                True,
                "Capacity",
            )

            search_parameters = pywrapcp.DefaultRoutingSearchParameters()
            search_parameters.first_solution_strategy = (
                routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
            )
            search_parameters.local_search_metaheuristic = (
                routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
            )
            search_parameters.time_limit.seconds = 5

            solution = routing.SolveWithParameters(search_parameters)
            if solution:
                ortools_routes: List[List[int]] = []
                for vehicle_id in range(instance.max_vehicles):
                    index = routing.Start(vehicle_id)
                    r = []
                    while not routing.IsEnd(index):
                        node = manager.IndexToNode(index)
                        if node != 0:
                            r.append(node)
                        index = solution.Value(routing.NextVar(index))
                    if r:
                        ortools_routes.append(r)

                cost = sum(calculate_route_distance(r, instance.dist_matrix) for r in ortools_routes)
                search_trace.append({
                    "step": 1,
                    "action": -1,
                    "operator": "ortools_gls_5s",
                    "applied": True,
                    "delta": cost - init_cost,
                    "cost": round(cost, 1),
                    "best_cost": round(cost, 1),
                    "routes": ortools_routes,
                })
                return build_solution_result(
                    ortools_routes, instance, search_trace, leg_geometries, t0_c, tenv_c, k_rate, min_temp
                )
        except Exception as e:
            logger.warning(f"OR-Tools solver unavailable or failed ({e}); falling back to Cyclic local search.")
            strategy = "cyclic"

    # 3. Local Search Iterations
    q_agent = None
    if strategy.lower() == "dqn":
        w = "src/cvrp_solver/weights/dqn_model.pt"
        w_path = w if Path(w).exists() else None
        q_agent = QNetworkInference(weights_path=w_path, seed=seed)
    elif strategy.lower() in ["double_dqn", "ddqn"]:
        w = "src/cvrp_solver/weights/double_dqn_model.pt"
        w_path = w if Path(w).exists() else None
        q_agent = QNetworkInference(weights_path=w_path, seed=seed)

    action_counts = [0, 0, 0, 0]
    action_successes = [0, 0, 0, 0]
    last_action = -1
    last_success = False
    no_improve_streak = 0

    cyclic_counter = 0

    for step in range(1, max_steps + 1):
        # Action Selection
        if strategy.lower() == "random":
            action = rng.randint(0, 3)

        elif strategy.lower() == "cyclic":
            action = cyclic_counter % 4
            cyclic_counter += 1

        elif strategy.lower() == "greedy":
            # Evaluate all 4 with 32 candidates each
            best_g_action = -1
            best_g_delta = 0.0
            best_g_routes = current_routes
            applied_any = False

            for a in range(4):
                app, dlt, cand, _ = best_move(
                    a, current_routes, instance, max_candidates=32, rng=rng
                )
                if app and dlt < best_g_delta:
                    best_g_delta = dlt
                    best_g_routes = cand
                    best_g_action = a
                    applied_any = True

            action = best_g_action if applied_any else (cyclic_counter % 4)
            cyclic_counter += 1

        elif strategy.lower() in ["dqn", "double_dqn", "ddqn"]:
            state = compute_f28_state(
                current_routes,
                current_cost,
                init_cost,
                best_cost,
                step,
                max_steps,
                no_improve_streak,
                feature_patience,
                action_counts,
                action_successes,
                last_action,
                last_success,
                instance,
            )
            action = q_agent.select_action(state, epsilon=0.0)

        else:
            action = cyclic_counter % 4
            cyclic_counter += 1

        # Execute Best Move
        action_counts[action] += 1
        applied, delta, new_routes, evals = best_move(
            action, current_routes, instance, max_candidates=max_candidates, rng=rng
        )

        if applied:
            current_routes = new_routes
            current_cost += delta
            action_successes[action] += 1
            last_success = True
            no_improve_streak = 0

            if current_cost < best_cost:
                best_cost = current_cost
                best_routes = [list(r) for r in current_routes]
        else:
            last_success = False
            no_improve_streak += 1

        last_action = action

        # Append to search trace
        search_trace.append({
            "step": step,
            "action": action,
            "operator": OPERATOR_NAMES[action],
            "applied": applied,
            "delta": round(delta, 2),
            "cost": round(current_cost, 1),
            "best_cost": round(best_cost, 1),
            "routes": [list(r) for r in current_routes] if applied else None,
        })

    return build_solution_result(
        best_routes, instance, search_trace, leg_geometries, t0_c, tenv_c, k_rate, min_temp
    )


def build_solution_result(
    routes: List[List[int]],
    instance: CVRPInstance,
    search_trace: List[Dict[str, Any]],
    leg_geometries: Optional[List[List[List[List[float]]]]] = None,
    t0_c: float = 85.0,
    tenv_c: float = 30.0,
    k_rate: float = 0.020,
    min_temp: float = 60.0,
) -> CVRPSolution:
    """Builds the comprehensive CVRPSolution object with thermal profiles and geometries."""
    is_feasible, total_dist, message = validate_cvrp_solution(routes, instance)
    detailed_routes: List[VehicleRoute] = []
    total_duration_sec = 0.0

    for v_idx, r in enumerate(routes):
        stops_info, route_duration, violations = calculate_thermal_profile(
            r, instance, t0_c, tenv_c, k_rate, min_temp
        )
        total_duration_sec += route_duration
        r_dist = calculate_route_distance(r, instance.dist_matrix)
        r_load = sum(instance.demands[n] for n in r)

        # Build leg geometries along real roads
        r_geoms: List[List[List[float]]] = []
        if leg_geometries is not None:
            curr_n = 0
            for next_n in r:
                r_geoms.append(leg_geometries[curr_n][next_n])
                curr_n = next_n
            # Return to depot leg
            r_geoms.append(leg_geometries[curr_n][0])

        detailed_routes.append(
            VehicleRoute(
                vehicle_id=v_idx + 1,
                customer_indices=r,
                stops=stops_info,
                leg_geometries=r_geoms,
                distance_km=round(r_dist / 1000.0, 2),
                duration_min=round(route_duration / 60.0, 1),
                total_load=r_load,
                thermal_violations_count=violations,
            )
        )

    return CVRPSolution(
        routes=routes,
        total_distance=round(total_dist, 1),
        total_duration_sec=round(total_duration_sec, 1),
        is_feasible=is_feasible,
        rejection_reason=None if is_feasible else message,
        detailed_routes=detailed_routes,
        search_trace=search_trace,
    )
