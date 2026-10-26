"""Reinforcement Learning Research & Model Engineering Package.

Core modules:
- osm_graph_loader: Road network extraction & 64-node planar graph
- newton_cooling: Newton's law of cooling physics & thermal reward
- traffic_model: Dynamic rush-hour congestion simulator
- delivery_env: HangGonDeliveryEnv Gymnasium environment with action masking
- policy_runner: HotWAYPolicyRunner sub-20ms inference wrapper
- export_ghost_trajectory: AI Ghost telemetry exporter for 3D game
- ablation_study: Thermal ablation benchmark runner
"""

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
    SPEED_LIMITS_KPH,
    export_geojson_files,
    generate_deterministic_hanggon_graph,
    get_nearest_node,
    haversine_distance_meters,
    load_or_generate_hanggon_graph,
)
from src.rl.traffic_model import (
    PEAK_MULTIPLIERS_BY_HIGHWAY,
    RUSH_HOURS,
    compute_edge_traversal,
    get_dynamic_edge_weight,
    get_traffic_multiplier,
    time_to_minutes,
)
from src.rl.delivery_env import HangGonDeliveryEnv
from src.rl.policy_runner import HotWAYPolicyRunner

__all__ = [
    "HangGonDeliveryEnv",
    "HotWAYPolicyRunner",
    "DISH_PROFILES",
    "CONTAINER_FACTORS",
    "DEFAULT_AMBIENT_TEMP_C",
    "get_composite_cooling_rate",
    "newton_cooling_analytical",
    "step_cooling_update",
    "calculate_thermal_reward",
    "DEPOT_LAT",
    "DEPOT_LON",
    "DEPOT_NODE_ID",
    "DEPOT_NAME",
    "SPEED_LIMITS_KPH",
    "haversine_distance_meters",
    "generate_deterministic_hanggon_graph",
    "load_or_generate_hanggon_graph",
    "export_geojson_files",
    "get_nearest_node",
    "RUSH_HOURS",
    "PEAK_MULTIPLIERS_BY_HIGHWAY",
    "time_to_minutes",
    "get_traffic_multiplier",
    "compute_edge_traversal",
    "get_dynamic_edge_weight",
]
