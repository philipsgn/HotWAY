"""Newton's Law of Cooling Thermal Physics Engine for HotWAY.

Implements continuous and discrete thermal decay for food items during delivery:
    dT/dt = -k(T - T_env)
    T(t) = T_env + (T_0 - T_env) * exp(-k * t)
    k = k_dish * alpha_container

Authoritative References:
- PRD.md §3.1, TECH_ARCHITECTURE.md §3.1
- survey_rl.md §4.1 - §5.1
- TEST_INFRA.md Features 3 & 4
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Literal, Optional, Union

# Dish Thermal Configurations
DISH_PROFILES: Dict[str, Dict[str, Union[float, str]]] = {
    "HOT_SOUP": {
        "name": "Bánh Canh Gà Hàng Gòn",
        "T0": 88.0,
        "k_dish": 0.038,
        "threshold": 60.0,
        "type": "hot",
    },
    "DRY_WARM": {
        "name": "Gỏi Gà Xé Phay",
        "T0": 58.0,
        "k_dish": 0.022,
        "threshold": 45.0,
        "type": "warm",
    },
    "COLD_DRINK": {
        "name": "Nước Sâm / Mía Đá",
        "T0": 6.0,
        "k_dish": 0.030,
        "threshold": 15.0,
        "type": "cold",
    },
}

# Container Insulation Modifiers
CONTAINER_FACTORS: Dict[str, float] = {
    "INSULATED_BAG": 0.50,
    "FOAM_BOX": 0.70,
    "OPEN_BASKET": 1.00,
}

DEFAULT_AMBIENT_TEMP_C: float = 30.0  # Typical Long Khánh afternoon ambient


def get_composite_cooling_rate(dish: str = "HOT_SOUP", container: str = "INSULATED_BAG") -> float:
    """Calculates composite cooling rate k = k_dish * alpha_container in min^-1."""
    dish_info = DISH_PROFILES.get(dish, DISH_PROFILES["HOT_SOUP"])
    k_dish = float(dish_info["k_dish"])
    alpha = CONTAINER_FACTORS.get(container, CONTAINER_FACTORS["INSULATED_BAG"])
    return round(k_dish * alpha, 6)


def newton_cooling_analytical(
    t_minutes: float,
    t0: float,
    t_env: float = DEFAULT_AMBIENT_TEMP_C,
    k: float = 0.019,
) -> float:
    """Computes exact analytical temperature T(t) = T_env + (T_0 - T_env) * exp(-k * t).

    Raises:
        ValueError: If t_minutes < 0 or k < 0.
    """
    if t_minutes < 0.0:
        raise ValueError(f"Elapsed transit time cannot be negative: {t_minutes}")
    if k < 0.0:
        raise ValueError(f"Cooling rate k cannot be negative: {k}")

    # Instant step or perfect insulation
    if t_minutes == 0.0 or k == 0.0:
        return float(t0)

    # Thermal equilibrium
    if t0 == t_env:
        return float(t_env)

    decay_factor = math.exp(-k * t_minutes)
    temp = t_env + (t0 - t_env) * decay_factor

    # Enforce thermodynamic asymptotic limits
    if t0 > t_env:
        return max(temp, t_env)
    else:
        return min(temp, t_env)


def step_cooling_update(
    current_temp: float,
    delta_t_minutes: float,
    t_env: float = DEFAULT_AMBIENT_TEMP_C,
    k: float = 0.019,
) -> float:
    """Incremental discrete step update: T_{t+dt} = T_env + (T_t - T_env) * exp(-k * dt).

    Raises:
        ValueError: If delta_t_minutes < 0 or k < 0.
    """
    if delta_t_minutes < 0.0:
        raise ValueError(f"Step transit duration cannot be negative: {delta_t_minutes}")
    return newton_cooling_analytical(t_minutes=delta_t_minutes, t0=current_temp, t_env=t_env, k=k)


def calculate_thermal_reward(
    delivered_temp: float,
    threshold: float = 60.0,
    beta_1: float = 10.0,
    beta_2: float = 0.05,
    temp_scale: float = 25.0,
) -> float:
    """Computes piecewise quadratic culinary satisfaction reward.

    For T >= threshold (60°C):
        R = +beta_1 * ((T - 60) / 25)
    For T < threshold (60°C):
        R = -beta_2 * (60 - T)^2
    """
    if delivered_temp >= threshold:
        return float(beta_1 * ((delivered_temp - threshold) / temp_scale))
    else:
        deficit = threshold - delivered_temp
        return float(-beta_2 * (deficit ** 2))
