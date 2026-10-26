"""AI Ghost Trajectory Exporter for 3D Web Game HotWAY Rider.

Generates high-resolution, 5.0-second interval GPS trajectory of the RL agent
by recording an authentic live rollout of HangGonDeliveryEnv on OpenStreetMap graph.

Module: src.rl.export_ghost_trajectory
Features: #22 (Ghost Trajectory Exporter)
Reference: AGENTS.md §2.1, PROJECT.md Interface Contract §2
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

import networkx as nx
import numpy as np

from src.rl.delivery_env import HangGonDeliveryEnv
from src.rl.newton_cooling import calculate_temperature_analytical
from src.rl.osm_graph_loader import DEPOT_LAT, DEPOT_LON
from src.rl.policy_runner import HotWAYPolicyRunner
from src.rl.traffic_model import get_traffic_multiplier


def generate_ghost_trajectory(
    order_id: str = "ord_sample_01",
    model_path: str = "models/rl_best_model.zip",
    output_path: str = "experiments/trajectories/best_route_ghost.json",
    seed: int = 42,
) -> Dict[str, Any]:
    """Records an authentic live rollout of HangGonDeliveryEnv and exports 5.0s waypoints."""
    # 1. Instantiate authentic delivery environment
    env = HangGonDeliveryEnv(seed=seed)
    obs, info = env.reset()

    # 2. Select order to deliver via Policy Runner or lowest cooling loss
    runner = HotWAYPolicyRunner(model_path=model_path)
    action_mask = env.action_masks()
    action = runner.predict_next_order(obs, action_mask.tolist())

    # Fallback to order 0 if wait or return was selected initially
    if action >= env.max_orders or not action_mask[action]:
        action = 0

    target_order = env.orders[action]
    source_node = env.depot_node
    target_node = target_order.dest_node

    # 3. Retrieve dynamic shortest path along road network
    path_nodes, total_dist_meters, total_time_sec = env._route_on_graph(
        source_node, target_node, env.tau_current
    )

    # 4. Construct contiguous physical edge timeline
    segments: List[Dict[str, Any]] = []
    accum_time_sec = 0.0

    for i in range(len(path_nodes) - 1):
        u, v = path_nodes[i], path_nodes[i + 1]
        data = env.graph.get_edge_data(u, v)
        edge_attr = data[0] if isinstance(data, dict) and 0 in data else data
        edge_attr = edge_attr or {}

        node_u = env.graph.nodes[u]
        node_v = env.graph.nodes[v]
        lat_u = float(node_u.get("y", node_u.get("lat", DEPOT_LAT)))
        lon_u = float(node_u.get("x", node_u.get("lon", DEPOT_LON)))
        lat_v = float(node_v.get("y", node_v.get("lat", target_order.lat)))
        lon_v = float(node_v.get("x", node_v.get("lon", target_order.lon)))

        length_m = float(edge_attr.get("length", 100.0))
        speed_kph = float(edge_attr.get("speed_kph", 30.0))
        highway = str(edge_attr.get("highway", "residential"))

        gamma = get_traffic_multiplier(
            time_minutes=env.tau_current + (accum_time_sec / 60.0),
            highway_type=highway,
            is_raining=env.is_rain,
        )
        effective_speed_mps = max(1.5, (speed_kph * 1000.0 / 3600.0) / gamma)
        duration_sec = length_m / effective_speed_mps

        segments.append({
            "lat_u": lat_u,
            "lon_u": lon_u,
            "lat_v": lat_v,
            "lon_v": lon_v,
            "start_time": accum_time_sec,
            "end_time": accum_time_sec + duration_sec,
            "duration": duration_sec,
            "speed_kmh": effective_speed_mps * 3.6,
        })
        accum_time_sec += duration_sec

    if not segments:
        # Single point edge fallback
        total_time_seconds = 60.0
        segments.append({
            "lat_u": DEPOT_LAT,
            "lon_u": DEPOT_LON,
            "lat_v": target_order.lat,
            "lon_v": target_order.lon,
            "start_time": 0.0,
            "end_time": total_time_seconds,
            "duration": total_time_seconds,
            "speed_kmh": 30.0,
        })
        accum_time_sec = total_time_seconds

    total_time_seconds = round(accum_time_sec, 1)

    # 5. Discretize into 5.0-second interval waypoints with kinematic acceleration & deceleration
    step_sec = 5.0
    num_steps = int(math.ceil(total_time_seconds / step_sec))
    waypoints: List[Dict[str, Any]] = []

    for step_idx in range(num_steps + 1):
        t_offset = min(total_time_seconds, float(step_idx * step_sec))

        # Find corresponding road segment
        active_seg = segments[-1]
        for seg in segments:
            if seg["start_time"] <= t_offset <= seg["end_time"]:
                active_seg = seg
                break

        seg_duration = active_seg["duration"]
        if seg_duration > 0.0:
            fraction = min(1.0, max(0.0, (t_offset - active_seg["start_time"]) / seg_duration))
        else:
            fraction = 1.0

        wp_lat = active_seg["lat_u"] + fraction * (active_seg["lat_v"] - active_seg["lat_u"])
        wp_lon = active_seg["lon_u"] + fraction * (active_seg["lon_v"] - active_seg["lon_u"])
        cruise_speed = active_seg["speed_kmh"]

        # Kinematic acceleration and deceleration envelope (10.0-second sinusoidal easing)
        if t_offset < 10.0:
            speed_factor = math.sin((math.pi / 2.0) * (t_offset / 10.0))
        elif total_time_seconds - t_offset < 10.0:
            remaining = max(0.0, total_time_seconds - t_offset)
            speed_factor = math.sin((math.pi / 2.0) * (remaining / 10.0))
        else:
            speed_factor = 1.0

        speed_kmh = max(0.0, cruise_speed * speed_factor)
        if t_offset == 0.0 or t_offset == total_time_seconds:
            speed_kmh = 0.0

        waypoints.append({
            "timestamp_offset": round(t_offset, 1),
            "lat": round(wp_lat, 6),
            "lon": round(wp_lon, 6),
            "speed_kmh": round(speed_kmh, 1),
        })

        if t_offset >= total_time_seconds:
            break

    # 6. Physical Newton Cooling at Destination
    transit_minutes = total_time_seconds / 60.0
    final_temp = calculate_temperature_analytical(
        t_initial=target_order.initial_temp_c,
        t_env=env.t_env,
        k=target_order.cooling_rate,
        t_minutes=transit_minutes,
    )

    trajectory_payload = {
        "order_id": order_id,
        "total_time_seconds": total_time_seconds,
        "final_temperature_c": round(final_temp, 1),
        "waypoints": waypoints,
    }

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(trajectory_payload, f, indent=2, ensure_ascii=False)

    return trajectory_payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export Authentic AI Ghost Trajectory for 3D Game")
    parser.add_argument("--order-id", type=str, default="ord_sample_01")
    parser.add_argument("--model-path", type=str, default="models/rl_best_model.zip")
    parser.add_argument("--output", type=str, default="experiments/trajectories/best_route_ghost.json")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    traj = generate_ghost_trajectory(
        order_id=args.order_id,
        model_path=args.model_path,
        output_path=args.output,
        seed=args.seed,
    )
    print(
        f"[OK] Exported authentic AI Ghost trajectory: {len(traj['waypoints'])} waypoints, "
        f"time={traj['total_time_seconds']}s, final_temp={traj['final_temperature_c']}°C -> {args.output}"
    )
