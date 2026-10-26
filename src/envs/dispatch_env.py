"""
DispatchEnv: Gymnasium Environment for GĐ2 (Dynamic Restaurant Real-Time Semi-MDP).
Simulates motorbike order dispatching with:
- 5-state Order FSM (PLACED -> COOKING -> READY -> DELIVERING -> DELIVERED)
- Semi-MDP event jumping with max wait cap tau_max
- NHPP arrival + Surge bursts + Overcapacity stress
- Exhaustive permutation routing for READY batches (m <= Q)
- Drain Phase preserving sum(r_k) == -sum(W_i) (error < 1e-9)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import gymnasium as gym
from gymnasium import spaces
import numpy as np

from src.routing.permutation_router import bundle_orders, route_batch_exhaustive


class DispatchEnv(gym.Env):
    metadata = {"render_modes": ["ansi", "json"]}

    def __init__(
        self,
        matrix_path: str | Path = "data/matrix_standard.npz",
        address_pool_path: str | Path = "data/address_pool_standard.json",
        num_drivers: int = 3,
        vehicle_capacity: int = 4,
        day_length_min: float = 720.0,  # 10:00 to 22:00
        max_wait_tau_min: float = 10.0,
        max_detour_km: float = 1.5,
        service_time_mean_min: float = 3.0,
        service_time_sigma: float = 0.25,
        kitchen_mean_min: float = 12.0,
        kitchen_sigma: float = 0.35,
        rain_factor: float = 1.0,
        surge_probability: float = 0.8,
        enable_event_logging: bool = True,
        event_log_path: Optional[str | Path] = None,
    ):
        super().__init__()
        self.num_drivers = num_drivers
        self.vehicle_capacity = vehicle_capacity
        self.capacity = vehicle_capacity
        self.day_length_min = day_length_min
        self.max_wait_tau_min = max_wait_tau_min
        self.max_detour_km = max_detour_km
        self.service_time_mean_min = service_time_mean_min
        self.service_time_sigma = service_time_sigma
        self.kitchen_mean_min = kitchen_mean_min
        self.kitchen_sigma = kitchen_sigma
        self.rain_factor = rain_factor
        self.surge_probability = surge_probability
        self.enable_event_logging = enable_event_logging
        self.event_log_path = Path(event_log_path) if event_log_path else None

        # Load precomputed distance and travel time matrices
        mat = np.load(matrix_path)
        self.dist_matrix: np.ndarray = mat["dist_matrix"].astype(np.float64)  # meters
        self.time_matrix: np.ndarray = mat["time_matrix"].astype(np.float64)  # minutes
        self.n_locations = self.dist_matrix.shape[0]

        with open(address_pool_path, "r", encoding="utf-8") as f:
            self.address_pool = json.load(f)
        self.depot_lat = float(self.address_pool[0]["lat"])
        self.depot_lon = float(self.address_pool[0]["lon"])

        # Action space: 0: Wait, 1..Q: Dispatch m READY orders
        self.action_space = spaces.Discrete(self.vehicle_capacity + 1)

        # Observation space: 12-dimensional continuous state vector
        self.observation_space = spaces.Box(
            low=0.0,
            high=100.0,
            shape=(12,),
            dtype=np.float32,
        )

        self.np_random = np.random.default_rng(2026)

        # State containers
        self.current_time: float = 0.0
        self.step_count: int = 0
        self.accumulated_reward: float = 0.0

        # Orders list
        self.orders: List[Dict[str, Any]] = []
        # Drivers list: dict of id, idle (bool), return_time (float), current_tour
        self.drivers: List[Dict[str, Any]] = []

        # Surge state
        self.surge_active: bool = False
        self.surge_start: float = 0.0
        self.surge_end: float = 0.0
        self.surge_multiplier: float = 1.0

        # Event log
        self.event_log: List[Dict[str, Any]] = []

    def _get_obs(self) -> np.ndarray:
        # Count orders by 5-state FSM
        n_placed = sum(1 for o in self.orders if o["state"] == "PLACED")
        n_cooking = sum(1 for o in self.orders if o["state"] == "COOKING")
        n_ready = sum(1 for o in self.orders if o["state"] == "READY")
        n_delivering = sum(1 for o in self.orders if o["state"] == "DELIVERING")

        waiting_orders = [o for o in self.orders if o["state"] in ("PLACED", "COOKING", "READY")]
        if waiting_orders:
            ages = [self.current_time - o["placed_time"] for o in waiting_orders]
            a_max = max(ages)
            a_mean = float(np.mean(ages))
        else:
            a_max = 0.0
            a_mean = 0.0

        # Spatial dispersion of READY orders (tour time estimate)
        ready_orders = [o for o in self.orders if o["state"] == "READY"]
        if ready_orders:
            locs = [o["address_idx"] for o in ready_orders]
            # Simple MST or nearest tour estimate from depot
            tour_est = float(np.mean([self.time_matrix[0, loc] for loc in locs])) * 2.0
        else:
            tour_est = 0.0

        # Driver states
        idle_drivers = sum(1 for d in self.drivers if d["idle"])
        busy_returns = sorted([d["return_time"] - self.current_time for d in self.drivers if not d["idle"]])
        rem1 = busy_returns[0] if len(busy_returns) > 0 else 0.0
        rem2 = busy_returns[1] if len(busy_returns) > 1 else 0.0

        # Time fraction
        h_t = min(1.0, self.current_time / self.day_length_min)

        # Recent arrival rate (last 30 minutes)
        t_window = max(0.0, self.current_time - 30.0)
        recent_count = sum(1 for o in self.orders if o["placed_time"] >= t_window)
        rate_recent = (recent_count / 30.0) * 60.0  # orders per hour

        obs = np.array([
            n_placed / 10.0,
            n_cooking / 10.0,
            n_ready / 10.0,
            n_delivering / 10.0,
            a_max / 60.0,
            a_mean / 60.0,
            tour_est / 60.0,
            idle_drivers / self.num_drivers,
            rem1 / 60.0,
            rem2 / 60.0,
            h_t,
            rate_recent / 30.0,
        ], dtype=np.float32)
        return obs

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        super().reset(seed=seed)
        if seed is not None:
            self.np_random = np.random.default_rng(seed)

        self.current_time = 0.0
        self.step_count = 0
        self.accumulated_reward = 0.0
        self.event_log = []

        # Initialize drivers
        self.drivers = [
            {"id": i, "idle": True, "return_time": 0.0, "total_km": 0.0, "total_busy_min": 0.0}
            for i in range(self.num_drivers)
        ]

        # Generate orders schedule for the entire day using NHPP + Surge
        self.orders = self._generate_day_orders()

        # Update initial order states at t = 0
        self._update_order_lifecycle(self.current_time)

        obs = self._get_obs()
        info = {
            "time": self.current_time,
            "total_orders": len(self.orders),
            "idle_drivers": self.num_drivers,
            "ready_orders": sum(1 for o in self.orders if o["state"] == "READY"),
        }
        return obs, info

    def _generate_day_orders(self) -> List[Dict[str, Any]]:
        """Generates order arrivals via Non-Homogeneous Poisson Process + Surge bursts."""
        orders: List[Dict[str, Any]] = []
        t = 0.0

        # Sample surge burst
        has_surge = self.np_random.random() < self.surge_probability
        if has_surge:
            self.surge_start = float(self.np_random.uniform(90.0, 600.0))
            self.surge_end = self.surge_start + float(self.np_random.uniform(20.0, 60.0))
            self.surge_multiplier = float(self.np_random.uniform(2.0, 4.0))
        else:
            self.surge_start = -1.0
            self.surge_end = -1.0
            self.surge_multiplier = 1.0

        order_id = 1
        while t < self.day_length_min:
            # Determine arrival rate lambda(t) in orders per hour
            hour = 10.0 + (t / 60.0)
            if 11.5 <= hour <= 13.0:
                base_rate = 25.0
            elif 18.0 <= hour <= 19.5:
                base_rate = 22.0
            else:
                base_rate = 6.0

            if self.surge_start <= t <= self.surge_end:
                base_rate *= self.surge_multiplier

            rate_per_min = base_rate / 60.0
            dt = float(self.np_random.exponential(1.0 / rate_per_min))
            t += dt
            if t >= self.day_length_min:
                break

            # Sample customer address (1 to n_locations - 1)
            # Spatial clustering during surge: pick from top 30% nearest cluster
            if self.surge_start <= t <= self.surge_end and self.np_random.random() < 0.6:
                addr_idx = int(self.np_random.choice(range(1, min(50, self.n_locations))))
            else:
                addr_idx = int(self.np_random.integers(1, self.n_locations))

            # Sample kitchen prep time: Lognormal
            prep_time = float(self.np_random.lognormal(np.log(self.kitchen_mean_min), self.kitchen_sigma))
            prep_time = max(5.0, min(30.0, prep_time))

            # Locked Promised ETA: t_placed + 12.0 + t_direct + 15.0
            t_direct = float(self.time_matrix[0, addr_idx])
            promised_eta = t + 12.0 + t_direct + 15.0

            orders.append({
                "id": order_id,
                "placed_time": t,
                "ready_time": t + prep_time,
                "prep_time": prep_time,
                "address_idx": addr_idx,
                "state": "PLACED",
                "dispatched_time": None,
                "delivered_time": None,
                "promised_eta": promised_eta,
                "in_surge": bool(self.surge_start <= t <= self.surge_end),
            })
            order_id += 1

        return orders

    def _update_order_lifecycle(self, current_time: float) -> None:
        """Transitions orders according to FSM: PLACED -> COOKING -> READY."""
        for o in self.orders:
            if o["state"] == "PLACED" and current_time >= o["placed_time"]:
                o["state"] = "COOKING"
            if o["state"] == "COOKING" and current_time >= o["ready_time"]:
                o["state"] = "READY"

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        self.step_count += 1
        self._update_order_lifecycle(self.current_time)

        # Identify ready orders
        ready_orders = [o for o in self.orders if o["state"] == "READY"]
        for o in ready_orders:
            o["order_age"] = self.current_time - o["placed_time"]

        idle_driver = next((d for d in self.drivers if d["idle"]), None)

        dispatched_count = 0
        if idle_driver is not None and action > 0 and len(ready_orders) > 0:
            # Action m: dispatch m orders
            m = min(action, self.vehicle_capacity, len(ready_orders))
            bundled = bundle_orders(ready_orders, self.dist_matrix, target_m=m, max_detour_km=self.max_detour_km)
            dispatched_count = len(bundled)

            if dispatched_count > 0:
                routing_res = route_batch_exhaustive(
                    bundled,
                    self.time_matrix,
                    self.current_time,
                    service_time_min=self.service_time_mean_min,
                    rain_factor=self.rain_factor,
                )

                # Update driver
                idle_driver["idle"] = False
                idle_driver["return_time"] = routing_res["driver_return_time"]
                idle_driver["total_busy_min"] += (routing_res["driver_return_time"] - self.current_time)
                idle_driver["total_km"] += (routing_res["tour_travel_time"] * (25.0 / 60.0))

                # Update orders to DELIVERING and record delivery times
                for o in bundled:
                    o["state"] = "DELIVERING"
                    o["dispatched_time"] = self.current_time
                    o["delivered_time"] = routing_res["delivery_times"][o["id"]]

                if self.enable_event_logging:
                    self.event_log.append({
                        "step": self.step_count,
                        "time": round(self.current_time, 2),
                        "event": "DISPATCH",
                        "driver_id": idle_driver["id"],
                        "order_ids": [o["id"] for o in bundled],
                        "return_time": round(routing_res["driver_return_time"], 2),
                    })

        # Future event candidates for exact continuous-time integration:
        # 1. Next driver return
        # 2. Next kitchen ready time
        # 3. Next customer delivery arrival
        # 4. Next order placement time (if before day_length)
        # 5. Maximum wait cap: current_time + max_wait_tau_min
        future_events = [self.current_time + self.max_wait_tau_min]

        # Busy driver returns
        for d in self.drivers:
            if not d["idle"] and d["return_time"] > self.current_time:
                future_events.append(d["return_time"])

        # Kitchen ready times
        for o in self.orders:
            if o["state"] in ("PLACED", "COOKING") and o["ready_time"] > self.current_time:
                future_events.append(o["ready_time"])

        # Order delivery arrival times
        for o in self.orders:
            if o["state"] == "DELIVERING" and o["delivered_time"] is not None and o["delivered_time"] > self.current_time:
                future_events.append(o["delivered_time"])

        # Next order placement (only if t < day_length)
        if self.current_time < self.day_length_min:
            for o in self.orders:
                if o["placed_time"] > self.current_time:
                    future_events.append(o["placed_time"])
                    break

        # Next decision epoch
        next_time = min(future_events)
        dt = next_time - self.current_time

        # Exact continuous-time integration:
        # Sum of wait time accumulated by all active orders across [current_time, next_time)
        # For each order, overlap = max(0, min(next_time, t_delivered) - max(current_time, t_placed))
        total_interval_wait = 0.0
        n_active_orders = 0
        for o in self.orders:
            t_start = max(self.current_time, o["placed_time"])
            t_end = min(next_time, o["delivered_time"]) if o["delivered_time"] is not None else next_time
            if t_end > t_start:
                total_interval_wait += (t_end - t_start)
                n_active_orders += 1

        step_reward = -total_interval_wait
        self.accumulated_reward += step_reward

        # Advance current time
        self.current_time = next_time

        # Check driver returns at new time
        for d in self.drivers:
            if not d["idle"] and self.current_time >= d["return_time"]:
                d["idle"] = True
                if self.enable_event_logging:
                    self.event_log.append({
                        "step": self.step_count,
                        "time": round(self.current_time, 2),
                        "event": "DRIVER_RETURN",
                        "driver_id": d["id"],
                    })

        # Check order deliveries at new time
        for o in self.orders:
            if o["state"] == "DELIVERING" and o["delivered_time"] is not None and self.current_time >= o["delivered_time"]:
                o["state"] = "DELIVERED"
                if self.enable_event_logging:
                    self.event_log.append({
                        "step": self.step_count,
                        "time": round(self.current_time, 2),
                        "event": "ORDER_DELIVERED",
                        "order_id": o["id"],
                        "wait_time": round(o["delivered_time"] - o["placed_time"], 2),
                    })

        self._update_order_lifecycle(self.current_time)

        # Check episode termination: Drain Phase finished (all orders DELIVERED and t >= day_length)
        all_delivered = all(o["state"] == "DELIVERED" for o in self.orders)
        all_drivers_home = all(d["idle"] for d in self.drivers)
        terminated = bool(all_delivered and all_drivers_home and self.current_time >= self.day_length_min)
        truncated = bool(self.step_count >= 5000 and not terminated)

        obs = self._get_obs()
        info = {
            "current_time": self.current_time,
            "dispatched_count": dispatched_count,
            "ready_count": sum(1 for o in self.orders if o["state"] == "READY"),
            "undelivered_count": sum(1 for o in self.orders if o["state"] != "DELIVERED"),
            "terminated": terminated,
        }

        if terminated and self.event_log_path:
            self._save_event_log()

        return obs, step_reward, terminated, truncated, info

    def _save_event_log(self) -> None:
        if self.event_log_path:
            self.event_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.event_log_path, "w", encoding="utf-8") as f:
                for ev in self.event_log:
                    f.write(json.dumps(ev, ensure_ascii=False, default=float) + "\n")

    def get_metrics(self) -> Dict[str, Any]:
        """Calculates final comprehensive metrics for the completed episode."""
        completed_orders = [o for o in self.orders if o["delivered_time"] is not None]
        if not completed_orders:
            return {
                "num_orders": len(self.orders),
                "delivered_orders": 0,
                "mean_wait_min": 0.0,
                "p90_wait_min": 0.0,
                "p95_wait_min": 0.0,
                "max_wait_min": 0.0,
                "p90_surge_wait_min": 0.0,
                "late_rate_pct": 0.0,
                "mean_lateness_min": 0.0,
                "gini_coefficient": 0.0,
                "fleet_utilization": 0.0,
                "total_km": 0.0,
                "true_sum_wait": 0.0,
                "reward_sum_wait": -self.accumulated_reward,
                "bellman_abs_error": 0.0,
            }

        wait_times = np.array([o["delivered_time"] - o["placed_time"] for o in completed_orders], dtype=np.float64)
        latenesses = np.array([max(0.0, o["delivered_time"] - o["promised_eta"]) for o in completed_orders], dtype=np.float64)

        # Gini coefficient
        diff_sum = float(np.abs(wait_times[:, None] - wait_times[None, :]).sum())
        gini = diff_sum / (2.0 * len(wait_times) * float(wait_times.sum())) if wait_times.sum() > 0 else 0.0

        # Surge-specific wait times
        surge_waits = [o["delivered_time"] - o["placed_time"] for o in completed_orders if o["in_surge"]]
        p90_surge = float(np.percentile(surge_waits, 90)) if surge_waits else float(np.percentile(wait_times, 90))

        # Fleet utilization
        total_driver_time = self.num_drivers * self.current_time
        busy_time = sum(d["total_busy_min"] for d in self.drivers)
        utilization = busy_time / total_driver_time if total_driver_time > 0 else 0.0

        # Bellman sum check: sum(wait_times) vs -accumulated_reward
        true_sum_w = float(wait_times.sum())
        reward_sum_w = -self.accumulated_reward
        bellman_abs_error = abs(true_sum_w - reward_sum_w)

        return {
            "num_orders": len(completed_orders),
            "mean_wait_min": float(np.mean(wait_times)),
            "p90_wait_min": float(np.percentile(wait_times, 90)),
            "p95_wait_min": float(np.percentile(wait_times, 95)),
            "max_wait_min": float(np.max(wait_times)),
            "p90_surge_wait_min": p90_surge,
            "late_rate_pct": float(np.mean(latenesses > 0.0)) * 100.0,
            "mean_lateness_min": float(np.mean(latenesses)),
            "gini_coefficient": float(gini),
            "fleet_utilization": float(utilization),
            "total_km": float(sum(d["total_km"] for d in self.drivers)),
            "true_sum_wait": true_sum_w,
            "reward_sum_wait": reward_sum_w,
            "bellman_abs_error": bellman_abs_error,
        }
