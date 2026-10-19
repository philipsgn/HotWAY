"""Custom Gymnasium Environment for Thermal-Aware Food Delivery in Hàng Gòn.

Implements DVRP-TW-TD with Newton's cooling law, dynamic rush-hour traffic,
and discrete action masking compatible with Stable-Baselines3 / MaskablePPO.

Authoritative References:
- PRD.md §3.1 - §3.3
- survey_rl.md §5, §6
- TEST_INFRA.md Features 6 - 11, 23
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import gymnasium as gym
from gymnasium import spaces
import networkx as nx
import numpy as np

from src.rl.newton_cooling import (
    CONTAINER_FACTORS,
    DEFAULT_AMBIENT_TEMP_C,
    DISH_PROFILES,
    calculate_thermal_reward,
    get_composite_cooling_rate,
    newton_cooling_analytical,
    step_cooling_update,
)
from src.rl.osm_graph_loader import (
    DEPOT_LAT,
    DEPOT_LON,
    DEPOT_NAME,
    DEPOT_NODE_ID,
    haversine_distance_meters,
    load_or_generate_hanggon_graph,
)
from src.rl.traffic_model import (
    compute_edge_traversal,
    get_traffic_multiplier,
)


@dataclass
class Order:
    """Represents a customer food delivery order."""
    order_id: str
    dest_node: Any
    lat: float
    lon: float
    dish: str = "HOT_SOUP"
    container: str = "INSULATED_BAG"
    initial_temp_c: float = 88.0
    current_temp_c: float = 88.0
    cooling_rate: float = 0.019  # k = 0.038 * 0.50
    placed_time_min: float = 0.0
    deadline_minutes: float = 45.0
    is_active: bool = True
    delivered: bool = False
    delivery_time_min: float = 0.0
    final_temp_c: float = 0.0


class HangGonDeliveryEnv(gym.Env):
    """Gymnasium environment for dynamic thermal food delivery routing in Hàng Gòn.

    Observation space: Box(-1.0, 1.0, shape=(40,), dtype=np.float32)
    Action space: Discrete(M + 2 = 7)
    """

    metadata = {"render_modes": ["human"], "render_fps": 10}

    ACTION_WAIT: int = 5
    ACTION_RETURN_DEPOT: int = 6

    def __init__(
        self,
        graph: Optional[Union[nx.Graph, nx.DiGraph, nx.MultiDiGraph]] = None,
        depot_node: Optional[Any] = None,
        max_orders: int = 5,
        t_env: float = DEFAULT_AMBIENT_TEMP_C,
        is_rain: bool = False,
        seed: int = 42,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__()
        self.max_orders = max_orders
        self.default_t_env = t_env
        self.t_env = t_env
        self.is_rain = is_rain
        self._seed = seed
        self.np_random = np.random.default_rng(seed)

        # Reward Hyperparameters
        self.beta1 = 10.0   # Thermal bonus scaling
        self.beta2 = 0.05   # Cold quadratic penalty
        self.lambd = 0.15   # Travel time penalty per minute
        self.gamma1 = 5.0   # On-time delivery bonus
        self.gamma2 = 1.0   # Lateness penalty per minute
        self.mu = 0.10      # Distance penalty per km
        self.step_cost = 0.20
        self.invalid_action_penalty = 50.0
        self.completion_bonus = 20.0
        self.service_time_min = 2.0  # Customer handover time

        # Road Network Graph setup
        if graph is not None:
            self.graph = graph
        else:
            self.graph = load_or_generate_hanggon_graph()

        self.nodes_list = list(self.graph.nodes())
        if depot_node is not None and depot_node in self.graph:
            self.depot_node = depot_node
        elif DEPOT_NODE_ID in self.graph:
            self.depot_node = DEPOT_NODE_ID
        else:
            self.depot_node = self.nodes_list[0]

        depot_data = self.graph.nodes[self.depot_node]
        self.depot_lat = float(depot_data.get("y", depot_data.get("lat", DEPOT_LAT)))
        self.depot_lon = float(depot_data.get("x", depot_data.get("lon", DEPOT_LON)))

        # Geographical bounding normalization constants (~6km radius)
        self.max_delta_lat = 0.06
        self.max_delta_lon = 0.06

        # Spaces:
        # Observation space shape: 4 (shipper) + 5 * 6 (orders) + 1 (tau) + 2 (weather) + 3 (traffic) = 40
        obs_dim = 4 + (self.max_orders * 6) + 1 + 2 + 3
        self.observation_space = spaces.Box(
            low=-1.0, high=1.0, shape=(obs_dim,), dtype=np.float32
        )
        self.action_space = spaces.Discrete(self.max_orders + 2)

        # Internal simulation states
        self.shipper_node = self.depot_node
        self.shipper_lat = self.depot_lat
        self.shipper_lon = self.depot_lon
        self.shipper_speed_kmh = 30.0
        self.tau_current = 720.0  # 12:00 PM noon default
        self.tau_start = self.tau_current
        self.step_count = 0
        self.max_steps = 30
        self.orders: List[Order] = []

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        super().reset(seed=seed)
        if seed is not None:
            self._seed = seed
            self.np_random = np.random.default_rng(seed)

        # Reset clock and shipper position
        options = options or {}
        self.tau_current = float(options.get("start_time_min", 720.0))  # 12:00 PM default
        self.tau_start = self.tau_current
        self.t_env = float(options.get("t_env", self.default_t_env))
        self.is_rain = bool(options.get("is_rain", self.is_rain))
        self.shipper_node = self.depot_node
        self.shipper_lat = self.depot_lat
        self.shipper_lon = self.depot_lon
        self.shipper_speed_kmh = 30.0
        self.step_count = 0

        # Sample active customer orders
        self.orders = self._generate_random_orders()

        observation = self._get_observation()
        info = {
            "action_mask": self.action_masks(),
            "tau_current": self.tau_current,
            "active_orders_count": len([o for o in self.orders if o.is_active]),
        }
        return observation, info

    def _generate_random_orders(self) -> List[Order]:
        """Generates M random delivery orders distributed across graph nodes."""
        eligible_nodes = [n for n in self.nodes_list if n != self.depot_node]
        if not eligible_nodes:
            eligible_nodes = self.nodes_list

        orders: List[Order] = []
        for i in range(self.max_orders):
            dest_node = self.np_random.choice(eligible_nodes)
            dest_data = self.graph.nodes[dest_node]
            lat = float(dest_data.get("y", dest_data.get("lat", self.depot_lat + 0.005 * (i + 1))))
            lon = float(dest_data.get("x", dest_data.get("lon", self.depot_lon + 0.005 * (i + 1))))

            dish = "HOT_SOUP"
            container = "INSULATED_BAG"
            k_composite = get_composite_cooling_rate(dish, container)

            dist_meters = self._compute_route_distance(self.depot_node, dest_node)
            est_minutes = (dist_meters / 1000.0) / 30.0 * 60.0
            deadline = self.tau_current + max(25.0, est_minutes * 1.5 + 15.0)

            orders.append(
                Order(
                    order_id=f"ORD_{i+1:02d}",
                    dest_node=dest_node,
                    lat=lat,
                    lon=lon,
                    dish=dish,
                    container=container,
                    initial_temp_c=88.0,
                    current_temp_c=88.0,
                    cooling_rate=k_composite,
                    placed_time_min=self.tau_current,
                    deadline_minutes=deadline,
                    is_active=True,
                )
            )
        return orders

    def action_masks(self) -> np.ndarray:
        """Returns a 1D boolean numpy array of shape (M+2=7).

        mask[i] = True if order slot i is active (undelivered).
        mask[ACTION_WAIT] = True always.
        mask[ACTION_RETURN_DEPOT] = True if all orders delivered or away from depot.
        """
        mask = np.zeros(self.action_space.n, dtype=bool)
        for i in range(self.max_orders):
            if i < len(self.orders) and self.orders[i].is_active:
                mask[i] = True

        mask[self.ACTION_WAIT] = True

        active_count = sum(1 for o in self.orders if o.is_active)
        if active_count == 0 or self.shipper_node != self.depot_node:
            mask[self.ACTION_RETURN_DEPOT] = True

        return mask

    def get_action_mask(self) -> np.ndarray:
        """Backward-compatible alias for action_masks."""
        return self.action_masks()

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        self.step_count += 1
        mask = self.action_masks()

        # Handle Invalid / Masked Actions (Hardened against out-of-bounds & negative actions)
        if action < 0 or action >= self.action_space.n or not mask[action]:
            obs = self._get_observation()
            reward = -self.invalid_action_penalty
            terminated = False
            truncated = self.step_count >= self.max_steps
            info = {
                "error": "INVALID_ACTION",
                "action": action,
                "action_mask": mask,
                "step_count": self.step_count,
            }
            return obs, reward, terminated, truncated, info

        # Execute Valid Action
        step_reward = 0.0
        transit_duration_min = 0.0
        distance_km = 0.0

        if action < self.max_orders:
            # Deliver Active Order
            order = self.orders[action]
            target_node = order.dest_node

            is_static_routing = bool(self.beta1 == 0.0 and self.beta2 == 0.0)
            path_nodes, path_dist_meters, travel_time_sec = self._route_on_graph(
                self.shipper_node, target_node, self.tau_current, static_distance_only=is_static_routing
            )
            distance_km = path_dist_meters / 1000.0
            travel_time_min = travel_time_sec / 60.0
            transit_duration_min = travel_time_min + self.service_time_min

            # Advance clock and shipper position
            self.tau_current += transit_duration_min
            self.shipper_node = target_node
            self.shipper_lat = order.lat
            self.shipper_lon = order.lon

            # Thermal update on ALL active orders in the bag
            for o in self.orders:
                if o.is_active:
                    o.current_temp_c = step_cooling_update(
                        current_temp=o.current_temp_c,
                        delta_t_minutes=transit_duration_min,
                        t_env=self.t_env,
                        k=o.cooling_rate,
                    )

            # Fulfill delivered order
            delivered_temp = order.current_temp_c
            order.is_active = False
            order.delivered = True
            order.delivery_time_min = self.tau_current
            order.final_temp_c = delivered_temp

            # Compute Reward Components
            # 1. Thermal Reward
            r_thermal = calculate_thermal_reward(
                delivered_temp=delivered_temp,
                threshold=60.0,
                beta_1=self.beta1,
                beta_2=self.beta2,
            )

            # 2. Time & Deadline Reward
            r_time = -self.lambd * travel_time_min
            if self.tau_current <= order.deadline_minutes:
                r_time += self.gamma1  # On-time bonus
            else:
                lateness = self.tau_current - order.deadline_minutes
                r_time -= self.gamma2 * lateness

            # 3. Operational Distance & Step Penalty
            r_penalty = -self.mu * distance_km - self.step_cost

            step_reward = r_thermal + r_time + r_penalty

        elif action == self.ACTION_WAIT:
            wait_min = 3.0
            self.tau_current += wait_min
            transit_duration_min = wait_min

            # Cool orders during waiting
            for o in self.orders:
                if o.is_active:
                    o.current_temp_c = step_cooling_update(
                        current_temp=o.current_temp_c,
                        delta_t_minutes=wait_min,
                        t_env=self.t_env,
                        k=o.cooling_rate,
                    )

            step_reward = -self.lambd * wait_min - self.step_cost

        elif action == self.ACTION_RETURN_DEPOT:
            path_nodes, path_dist_meters, travel_time_sec = self._route_on_graph(
                self.shipper_node, self.depot_node, self.tau_current
            )
            distance_km = path_dist_meters / 1000.0
            travel_time_min = travel_time_sec / 60.0
            transit_duration_min = travel_time_min

            self.tau_current += travel_time_min
            self.shipper_node = self.depot_node
            self.shipper_lat = self.depot_lat
            self.shipper_lon = self.depot_lon

            for o in self.orders:
                if o.is_active:
                    o.current_temp_c = step_cooling_update(
                        current_temp=o.current_temp_c,
                        delta_t_minutes=travel_time_min,
                        t_env=self.t_env,
                        k=o.cooling_rate,
                    )

            step_reward = -self.lambd * travel_time_min - self.mu * distance_km - self.step_cost

            # Check if all orders were fulfilled
            active_remaining = sum(1 for o in self.orders if o.is_active)
            if active_remaining == 0:
                step_reward += self.completion_bonus

        # Check Termination / Truncation
        all_delivered = all(o.delivered for o in self.orders)
        at_depot = (self.shipper_node == self.depot_node)
        terminated = all_delivered and at_depot
        truncated = (self.step_count >= self.max_steps) or (self.tau_current - self.tau_start >= 180.0)

        observation = self._get_observation()
        info = {
            "step_count": self.step_count,
            "tau_current": self.tau_current,
            "action": action,
            "reward": step_reward,
            "action_mask": self.action_masks(),
            "delivered_count": sum(1 for o in self.orders if o.delivered),
            "remaining_orders": sum(1 for o in self.orders if o.is_active),
            "transit_duration_min": transit_duration_min,
            "distance_km": distance_km,
        }
        return observation, step_reward, terminated, truncated, info

    def _route_on_graph(
        self, u: Any, v: Any, current_time_min: float, static_distance_only: bool = False
    ) -> Tuple[List[Any], float, float]:
        """Computes shortest path between u and v using dynamic travel times or static distance."""
        if u == v:
            return [u], 0.0, 0.0

        def weight_func(node1, node2, edge_attrs):
            length = float(edge_attrs.get("length", 100.0))
            speed_kph = float(edge_attrs.get("speed_kph", 30.0))
            hw = str(edge_attrs.get("highway", "residential"))
            gamma = get_traffic_multiplier(
                time_minutes=current_time_min,
                highway_type=hw,
                is_raining=self.is_rain,
            )
            speed_mps = (speed_kph * 1000.0 / 3600.0) / gamma
            return length / max(1.0, speed_mps)

        try:
            if static_distance_only:
                path = nx.shortest_path(self.graph, source=u, target=v, weight="length")
            else:
                path = nx.shortest_path(self.graph, source=u, target=v, weight=weight_func)
            total_dist = 0.0
            total_time_sec = 0.0
            for i in range(len(path) - 1):
                n1, n2 = path[i], path[i + 1]
                data = self.graph.get_edge_data(n1, n2)
                edge_attr = data[0] if isinstance(data, dict) and 0 in data else data
                edge_attr = edge_attr or {}
                l = float(edge_attr.get("length", 100.0))
                total_dist += l
                total_time_sec += weight_func(n1, n2, edge_attr)
            return path, total_dist, total_time_sec
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            pos_u = self.graph.nodes[u]
            pos_v = self.graph.nodes[v]
            lat_u = float(pos_u.get("y", pos_u.get("lat", self.depot_lat)))
            lon_u = float(pos_u.get("x", pos_u.get("lon", self.depot_lon)))
            lat_v = float(pos_v.get("y", pos_v.get("lat", self.depot_lat)))
            lon_v = float(pos_v.get("x", pos_v.get("lon", self.depot_lon)))
            dist = haversine_distance_meters(lat_u, lon_u, lat_v, lon_v)
            time_sec = dist / (30.0 * 1000.0 / 3600.0)
            return [u, v], dist, time_sec

    def _compute_route_distance(self, u: Any, v: Any) -> float:
        """Computes static road distance in meters."""
        if u == v:
            return 0.0
        try:
            return float(nx.shortest_path_length(self.graph, source=u, target=v, weight="length"))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return 1000.0

    def _get_observation(self) -> np.ndarray:
        """Builds the 40-dimensional continuous Box observation vector.

        Features:
        1. Shipper State (4 features): x_norm, y_norm, v_norm, load_ratio
        2. Active Orders (M * 6 = 30 features): is_active, dx, dy, temp, deadline, k
        3. Temporal (1 feature): tau_norm
        4. Weather / Environment (2 features): t_env_norm, is_rain
        5. Congestion (3 features): primary, secondary, local
        """
        obs = np.zeros(self.observation_space.shape[0], dtype=np.float32)

        # 1. Shipper State
        obs[0] = np.clip((self.shipper_lon - self.depot_lon) / self.max_delta_lon, -1.0, 1.0)
        obs[1] = np.clip((self.shipper_lat - self.depot_lat) / self.max_delta_lat, -1.0, 1.0)
        obs[2] = np.clip(self.shipper_speed_kmh / 60.0, 0.0, 1.0)
        active_orders = [o for o in self.orders if o.is_active]
        obs[3] = len(active_orders) / float(self.max_orders)

        # 2. Active Orders (6 features per slot)
        base = 4
        for i in range(self.max_orders):
            offset = base + (i * 6)
            if i < len(self.orders):
                order = self.orders[i]
                obs[offset + 0] = 1.0 if order.is_active else 0.0
                obs[offset + 1] = np.clip((order.lon - self.shipper_lon) / self.max_delta_lon, -1.0, 1.0) if order.is_active else 0.0
                obs[offset + 2] = np.clip((order.lat - self.shipper_lat) / self.max_delta_lat, -1.0, 1.0) if order.is_active else 0.0
                # Temperature normalized [20°C, 95°C] -> [0.0, 1.0]
                obs[offset + 3] = np.clip((order.current_temp_c - 20.0) / 75.0, 0.0, 1.0) if order.is_active else 0.0
                # Remaining time to deadline in hours [-1.0, 1.0]
                obs[offset + 4] = np.clip((order.deadline_minutes - self.tau_current) / 60.0, -1.0, 1.0) if order.is_active else 0.0
                # Cooling rate k relative to 0.05
                obs[offset + 5] = np.clip(order.cooling_rate / 0.05, 0.0, 1.0) if order.is_active else 0.0
            else:
                obs[offset : offset + 6] = 0.0

        # 3. Temporal Feature
        base_time = 4 + (self.max_orders * 6)  # index 34
        obs[base_time] = (self.tau_current % 1440.0) / 1440.0

        # 4. Environment / Weather
        obs[base_time + 1] = np.clip((self.t_env - 15.0) / 25.0, 0.0, 1.0)
        obs[base_time + 2] = 1.0 if self.is_rain else 0.0

        # 5. Congestion status on primary, secondary, alleys
        g_prim = get_traffic_multiplier(self.tau_current, "primary", self.is_rain)
        g_sec = get_traffic_multiplier(self.tau_current, "secondary", self.is_rain)
        g_loc = get_traffic_multiplier(self.tau_current, "residential", self.is_rain)
        obs[base_time + 3] = np.clip((g_prim - 1.0) / 2.0, 0.0, 1.0)
        obs[base_time + 4] = np.clip((g_sec - 1.0) / 2.0, 0.0, 1.0)
        obs[base_time + 5] = np.clip((g_loc - 1.0) / 2.0, 0.0, 1.0)

        return obs
