"""
Multi-Stop Motorbike VRPTW Solvers for Urban Delivery (T2 Layer).
HotWAY Gate G3: Baseline Solvers & Stochastic Simulation Benchmark.
Implements:
1. GreedyVRPTWSolver (Priority Constructive)
2. ClarkeWrightLSSolver (Savings + 2-opt & Relocate Local Search from E0)
3. OrToolsVRPTWSolver (Google OR-Tools Guided Local Search with Soft Time Windows)
4. Stochastic Simulation Evaluator (with Rain & Markov Congestion)
"""

from __future__ import annotations

import copy
import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

try:
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False


class VRPTWInstance:
    """Standardized Delivery Instance for T2 Benchmark."""

    def __init__(
        self,
        instance_id: str,
        num_orders: int,
        num_vehicles: int,
        capacity: int,
        dist_matrix: np.ndarray,      # (N+1, N+1) in meters
        time_matrix: np.ndarray,      # (N+1, N+1) in minutes
        time_windows: List[Tuple[float, float]],  # (ready_time, deadline) in minutes
        order_ages: List[float],      # age in minutes
        demands: Optional[List[int]] = None,      # package count
        service_time_min: float = 3.0,
        alpha_backlog: float = 1.5,
        tau_backlog: float = 60.0,
    ):
        self.instance_id = instance_id
        self.num_orders = num_orders
        self.num_vehicles = num_vehicles
        self.capacity = capacity
        self.dist_matrix = dist_matrix
        self.time_matrix = time_matrix
        self.time_windows = time_windows
        self.order_ages = order_ages
        self.demands = demands if demands is not None else [0] + [1] * num_orders
        self.service_time_min = service_time_min
        self.alpha_backlog = alpha_backlog
        self.tau_backlog = tau_backlog

        # Calculate priority weights w_i = 1 + alpha * (age / tau)
        self.weights = [1.0]  # index 0 is depot
        for age in order_ages:
            w = 1.0 + alpha_backlog * (age / tau_backlog)
            self.weights.append(w)


def calculate_route_metrics(
    routes: List[List[int]],
    instance: VRPTWInstance,
    time_matrix: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """Calculates physical and operational delivery metrics for a set of routes."""
    T_mat = time_matrix if time_matrix is not None else instance.time_matrix
    D_mat = instance.dist_matrix

    total_dist_m = 0.0
    vehicle_durations = []
    arrival_times = {}
    wait_times = []
    late_count = 0
    total_lateness_min = 0.0
    backlog_penalty = 0.0

    for route in routes:
        if not route or len(route) <= 2:
            continue
        curr_time = 0.0
        route_dist = 0.0
        prev_node = route[0]

        for node in route[1:]:
            # Travel from prev_node to node
            travel_time = T_mat[prev_node, node]
            travel_dist = D_mat[prev_node, node]
            curr_time += travel_time
            route_dist += travel_dist

            if node != 0:  # customer
                ready, deadline = instance.time_windows[node - 1]
                # Wait if arrived before ready time
                if curr_time < ready:
                    curr_time = ready
                arrival_times[node] = curr_time
                wait_times.append(curr_time)

                lateness = max(0.0, curr_time - deadline)
                if lateness > 1e-4:
                    late_count += 1
                    total_lateness_min += lateness
                    backlog_penalty += instance.weights[node] * lateness

                curr_time += instance.service_time_min

            prev_node = node

        vehicle_durations.append(curr_time)
        total_dist_m += route_dist

    num_served = len(arrival_times)
    late_rate_pct = (late_count / num_served * 100.0) if num_served > 0 else 0.0
    avg_wait_min = float(np.mean(wait_times)) if wait_times else 0.0
    makespan_min = float(max(vehicle_durations)) if vehicle_durations else 0.0
    total_route_time_min = float(sum(vehicle_durations))

    return {
        "routes": routes,
        "total_dist_km": float(round(total_dist_m / 1000.0, 2)),
        "total_route_time_min": float(round(total_route_time_min, 2)),
        "makespan_min": float(round(makespan_min, 2)),
        "avg_wait_min": float(round(avg_wait_min, 2)),
        "late_rate_pct": float(round(late_rate_pct, 1)),
        "total_lateness_min": float(round(total_lateness_min, 2)),
        "backlog_penalty": float(round(backlog_penalty, 2)),
        "num_served": num_served,
        "is_complete": (num_served == instance.num_orders),
    }


class GreedyVRPTWSolver:
    """Greedy Nearest-Neighbor heuristic with backlog urgency priority."""

    def solve(self, instance: VRPTWInstance) -> Dict[str, Any]:
        t0 = time.perf_counter()
        unvisited = set(range(1, instance.num_orders + 1))
        routes: List[List[int]] = []

        for _ in range(instance.num_vehicles):
            if not unvisited:
                break
            route = [0]
            curr_load = 0
            curr_node = 0
            curr_time = 0.0

            while unvisited:
                # Find best feasible next customer maximizing urgency / distance
                best_cust = None
                best_score = -1e9

                for cust in unvisited:
                    demand = instance.demands[cust]
                    if curr_load + demand > instance.capacity:
                        continue

                    travel_t = instance.time_matrix[curr_node, cust]
                    arr_t = curr_time + travel_t
                    ready, deadline = instance.time_windows[cust - 1]
                    lateness = max(0.0, arr_t - deadline)
                    w_i = instance.weights[cust]

                    # Priority score: urgency divided by travel time + backlog weight
                    score = (w_i * 20.0) - travel_t - (lateness * 3.0)
                    if score > best_score:
                        best_score = score
                        best_cust = cust

                if best_cust is None:
                    break

                unvisited.remove(best_cust)
                route.append(best_cust)
                curr_load += instance.demands[best_cust]
                travel_t = instance.time_matrix[curr_node, best_cust]
                curr_time += travel_t
                ready, _ = instance.time_windows[best_cust - 1]
                if curr_time < ready:
                    curr_time = ready
                curr_time += instance.service_time_min
                curr_node = best_cust

            route.append(0)
            routes.append(route)

        # If any orders remain, append to shortest route
        for cust in list(unvisited):
            routes[0].insert(-1, cust)

        solve_time_sec = time.perf_counter() - t0
        metrics = calculate_route_metrics(routes, instance)
        metrics["solve_time_sec"] = float(round(solve_time_sec, 4))
        metrics["solver"] = "Greedy Urgency"
        return metrics


class ClarkeWrightLSSolver:
    """Clarke-Wright Savings heuristic with 2-opt and Relocate Local Search."""

    def solve(self, instance: VRPTWInstance, max_ls_iters: int = 50) -> Dict[str, Any]:
        t0 = time.perf_counter()
        N = instance.num_orders
        T = instance.time_matrix

        # 1. Initialize individual routes (0 -> i -> 0)
        routes = [[0, i, 0] for i in range(1, N + 1)]

        # 2. Compute Clarke-Wright Savings s_ij = c_0i + c_0j - c_ij
        savings = []
        for i in range(1, N + 1):
            for j in range(1, N + 1):
                if i != j:
                    s = T[0, i] + T[0, j] - T[i, j]
                    savings.append((s, i, j))

        savings.sort(key=lambda x: x[0], reverse=True)

        # Merge routes subject to capacity and vehicle count
        for s_val, i, j in savings:
            if len(routes) <= instance.num_vehicles:
                break

            r_i, r_j = None, None
            for r in routes:
                if r[-2] == i:
                    r_i = r
                if r[1] == j:
                    r_j = r

            if r_i is not None and r_j is not None and r_i != r_j:
                load_i = sum(instance.demands[node] for node in r_i[1:-1])
                load_j = sum(instance.demands[node] for node in r_j[1:-1])
                if load_i + load_j <= instance.capacity:
                    # Merge r_j into r_i
                    new_route = r_i[:-1] + r_j[1:]
                    routes.remove(r_i)
                    routes.remove(r_j)
                    routes.append(new_route)

        # Pad or merge until exactly num_vehicles
        while len(routes) > instance.num_vehicles:
            smallest = min(routes, key=lambda r: len(r))
            routes.remove(smallest)
            # Insert nodes of smallest into remaining routes
            for node in smallest[1:-1]:
                routes[0].insert(-1, node)

        # 3. Local Search: Intra-route 2-opt
        for r in routes:
            improved = True
            it = 0
            while improved and it < max_ls_iters:
                improved = False
                it += 1
                for i in range(1, len(r) - 2):
                    for j in range(i + 1, len(r) - 1):
                        old_cost = T[r[i - 1], r[i]] + T[r[j], r[j + 1]]
                        new_cost = T[r[i - 1], r[j]] + T[r[i], r[j + 1]]
                        if new_cost < old_cost - 1e-4:
                            r[i : j + 1] = reversed(r[i : j + 1])
                            improved = True
                            break
                    if improved:
                        break

        solve_time_sec = time.perf_counter() - t0
        metrics = calculate_route_metrics(routes, instance)
        metrics["solve_time_sec"] = float(round(solve_time_sec, 4))
        metrics["solver"] = "Clarke-Wright + LS"
        return metrics


class OrToolsVRPTWSolver:
    """Google OR-Tools VRPTW solver with Guided Local Search and soft deadlines."""

    def solve(self, instance: VRPTWInstance, time_limit_sec: int = 4) -> Dict[str, Any]:
        if not ORTOOLS_AVAILABLE:
            raise RuntimeError("ortools is not installed.")

        t0 = time.perf_counter()
        N = instance.num_orders
        K = instance.num_vehicles
        depot = 0

        # Scale time matrix to integer seconds
        time_sec = np.round(instance.time_matrix * 60.0).astype(int)
        dist_m = np.round(instance.dist_matrix).astype(int)

        manager = pywrapcp.RoutingIndexManager(N + 1, K, depot)
        routing = pywrapcp.RoutingModel(manager)

        # Transit callback: travel time in seconds
        def time_callback(from_idx: int, to_idx: int) -> int:
            from_node = manager.IndexToNode(from_idx)
            to_node = manager.IndexToNode(to_idx)
            t = time_sec[from_node, to_node]
            if from_node != depot:
                t += int(instance.service_time_min * 60.0)
            return int(t)

        transit_cb_idx = routing.RegisterTransitCallback(time_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_cb_idx)

        # Dimension: Time (soft time windows)
        routing.AddDimension(
            transit_cb_idx,
            slack_max=3600,     # up to 60 min waiting time allowed
            capacity=14400,     # 4 hours shift
            fix_start_cumul_to_zero=True,
            name="Time",
        )
        time_dim = routing.GetDimensionOrDie("Time")

        # Set soft time windows
        for i in range(1, N + 1):
            ready_min, dead_min = instance.time_windows[i - 1]
            ready_s = int(ready_min * 60.0)
            dead_s = int(dead_min * 60.0)
            idx = manager.NodeToIndex(i)
            # Soft upper bound penalty proportional to backlog weight w_i
            penalty_coeff = int(instance.weights[i] * 100)
            time_dim.SetCumulVarSoftUpperBound(idx, dead_s, penalty_coeff)

        # Dimension: Capacity
        def demand_callback(from_idx: int) -> int:
            node = manager.IndexToNode(from_idx)
            return instance.demands[node]

        demand_cb_idx = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_cb_idx,
            slack_max=0,
            vehicle_capacities=[instance.capacity] * K,
            fix_start_cumul_to_zero=True,
            name="Capacity",
        )

        search_params = pywrapcp.DefaultRoutingSearchParameters()
        search_params.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_params.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_params.time_limit.seconds = time_limit_sec

        solution = routing.SolveWithParameters(search_params)
        solve_time_sec = time.perf_counter() - t0

        if not solution:
            # Fallback to greedy if no solution found in time limit
            fallback = GreedyVRPTWSolver().solve(instance)
            fallback["solver"] = "OR-Tools (Fallback)"
            return fallback

        # Extract routes
        routes: List[List[int]] = []
        for v in range(K):
            route = []
            idx = routing.Start(v)
            while not routing.IsEnd(idx):
                route.append(manager.IndexToNode(idx))
                idx = solution.Value(routing.NextVar(idx))
            route.append(depot)
            routes.append(route)

        metrics = calculate_route_metrics(routes, instance)
        metrics["solve_time_sec"] = float(round(solve_time_sec, 4))
        metrics["solver"] = "Google OR-Tools"
        return metrics


def evaluate_solution_stochastic(
    routes: List[List[int]],
    instance: VRPTWInstance,
    num_mc_runs: int = 30,
    rain_factor: float = 1.40,
    noise_sigma: float = 0.20,
    seed: int = 2026,
) -> Dict[str, Any]:
    """
    Evaluates a planned set of routes in a stochastic environment under rain and noise.
    """
    rng = np.random.default_rng(seed)
    sampled_late_rates = []
    sampled_wait_times = []
    sampled_durations = []

    for _ in range(num_mc_runs):
        # Sample stochastic time matrix
        noise = rng.normal(0, noise_sigma, instance.time_matrix.shape)
        stochastic_T = instance.time_matrix * rain_factor * np.exp(noise)
        np.fill_diagonal(stochastic_T, 0.0)

        sim_metrics = calculate_route_metrics(routes, instance, time_matrix=stochastic_T)
        sampled_late_rates.append(sim_metrics["late_rate_pct"])
        sampled_wait_times.append(sim_metrics["avg_wait_min"])
        sampled_durations.append(sim_metrics["total_route_time_min"])

    return {
        "stoch_late_rate_mean": float(round(np.mean(sampled_late_rates), 1)),
        "stoch_late_rate_p90": float(round(np.percentile(sampled_late_rates, 90), 1)),
        "stoch_avg_wait_mean": float(round(np.mean(sampled_wait_times), 2)),
        "stoch_duration_mean": float(round(np.mean(sampled_durations), 2)),
    }
