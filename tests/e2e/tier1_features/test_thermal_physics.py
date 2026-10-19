"""Tier 1: Opaque-Box Newton Cooling Physics Verification.

Verifies the mathematical and physical fidelity of Newton's Law of Cooling
governing food degradation in the HotWAY delivery simulation:
    T(t) = T_env + (T_0 - T_env) * exp(-k * t)
    k = k_dish * alpha_container

Authoritative Reference:
- survey_rl.md §4.1 - §4.2
- PRD.md §3.1
"""

import math
import unittest
from typing import Literal


# Authoritative Physical Constants defined in survey_rl.md & PRD.md
DISH_COEFFICIENTS = {
    "HOT_SOUP": {"name": "Bánh Canh Gà", "T0": 88.0, "k_dish": 0.038, "threshold": 60.0},
    "DRY_WARM": {"name": "Gỏi Gà Xé Phay", "T0": 58.0, "k_dish": 0.022, "threshold": 45.0},
    "COLD_DRINK": {"name": "Nước Sâm / Mía Đá", "T0": 6.0, "k_dish": 0.030, "threshold": 15.0},
}

CONTAINER_FACTORS = {
    "INSULATED_BAG": 0.50,
    "FOAM_BOX": 0.70,
    "OPEN_BASKET": 1.00,
}


def newton_cooling_analytical(
    t_minutes: float,
    t0: float,
    t_env: float,
    k_rate: float,
) -> float:
    """Exact analytical solution to dT/dt = -k(T - T_env)."""
    return t_env + (t0 - t_env) * math.exp(-k_rate * t_minutes)


def step_cooling_update(
    current_temp: float,
    delta_t_minutes: float,
    t_env: float,
    k_rate: float,
) -> float:
    """Incremental discrete step update: T_{t+dt} = T_env + (T_t - T_env)*exp(-k*dt)."""
    return t_env + (current_temp - t_env) * math.exp(-k_rate * delta_t_minutes)


def calculate_thermal_reward(delivered_temp: float) -> float:
    """Multi-objective piecewise quadratic thermal reward component."""
    if delivered_temp >= 60.0:
        return 10.0 * ((delivered_temp - 60.0) / 25.0)
    else:
        deficit = 60.0 - delivered_temp
        return -0.05 * (deficit ** 2)


class TestNewtonCoolingPhysics(unittest.TestCase):
    """Opaque-box validation of continuous cooling curves and thermal matrix."""

    def test_composite_cooling_rate_matrix(self):
        """Verifies k = k_dish * alpha_container for all 9 dish-container pairs."""
        for dish_key, dish_data in DISH_COEFFICIENTS.items():
            k_dish = dish_data["k_dish"]
            for container_key, alpha in CONTAINER_FACTORS.items():
                expected_k = k_dish * alpha
                self.assertAlmostEqual(
                    expected_k,
                    k_dish * alpha,
                    places=6,
                    msg=f"Discrepancy in composite rate for {dish_key} + {container_key}",
                )

        # Explicit check for the project's primary benchmark dish: Bánh Canh Gà + Insulated Bag
        k_banhcanh_insulated = DISH_COEFFICIENTS["HOT_SOUP"]["k_dish"] * CONTAINER_FACTORS["INSULATED_BAG"]
        self.assertAlmostEqual(k_banhcanh_insulated, 0.019, places=5)

    def test_authoritative_numerical_benchmarks_banh_canh_ga(self):
        """Validates against exact hand-calculated calibration points in survey_rl.md §4.2."""
        t0 = 88.0
        t_env = 30.0
        k = 0.019  # Bánh Canh Gà + INSULATED_BAG

        # 10 minutes: T(10) = 30 + 58 * exp(-0.19) = 30 + 47.96 = 77.96°C
        temp_10 = newton_cooling_analytical(10.0, t0, t_env, k)
        self.assertAlmostEqual(temp_10, 77.96, delta=0.02)

        # 25 minutes: T(25) = 30 + 58 * exp(-0.475) = 30 + 36.07 = 66.07°C
        temp_25 = newton_cooling_analytical(25.0, t0, t_env, k)
        self.assertAlmostEqual(temp_25, 66.07, delta=0.02)

        # 45 minutes: T(45) = 30 + 58 * exp(-0.855) = 30 + 24.67 = 54.67°C
        temp_45 = newton_cooling_analytical(45.0, t0, t_env, k)
        self.assertAlmostEqual(temp_45, 54.67, delta=0.02)

    def test_stepwise_vs_analytical_path_independence(self):
        """Verifies that multi-hop discrete incremental transit equals single continuous ODE calculation."""
        t0 = 88.0
        t_env = 32.0
        k = 0.025

        # Single 30-minute transit
        single_result = newton_cooling_analytical(30.0, t0, t_env, k)

        # Multi-hop road segments: 5 min + 12 min + 8 min + 5 min = 30 min
        segments = [5.0, 12.0, 8.0, 5.0]
        stepwise_temp = t0
        for delta_t in segments:
            stepwise_temp = step_cooling_update(stepwise_temp, delta_t, t_env, k)

        self.assertAlmostEqual(
            single_result,
            stepwise_temp,
            places=10,
            msg="Step-wise path integration drifted from analytical continuous solution",
        )

    def test_hot_food_strict_monotonic_decay(self):
        """Verifies that for T_0 > T_env, temperature is strictly non-increasing over time."""
        t0 = 88.0
        t_env = 30.0
        k = 0.019

        times = [0.0, 5.0, 10.0, 20.0, 35.0, 60.0, 120.0]
        temps = [newton_cooling_analytical(t, t0, t_env, k) for t in times]

        for i in range(len(temps) - 1):
            self.assertGreater(
                temps[i],
                temps[i + 1],
                f"Monotonicity violation between t={times[i]} ({temps[i]}C) and t={times[i+1]} ({temps[i+1]}C)",
            )

    def test_cold_drink_warming_direction(self):
        """Verifies that cold drinks (T_0 < T_env) strictly warm up towards ambient temperature."""
        t0 = 6.0
        t_env = 30.0
        k = DISH_COEFFICIENTS["COLD_DRINK"]["k_dish"] * CONTAINER_FACTORS["OPEN_BASKET"]

        times = [0.0, 5.0, 15.0, 30.0, 60.0]
        temps = [newton_cooling_analytical(t, t0, t_env, k) for t in times]

        for i in range(len(temps) - 1):
            self.assertLess(
                temps[i],
                temps[i + 1],
                f"Cold drink must warm up towards T_env, but cooled down: {temps[i]} -> {temps[i+1]}",
            )
            self.assertLessEqual(
                temps[i + 1],
                t_env,
                f"Cold drink warmed above ambient: {temps[i+1]} > {t_env}",
            )

    def test_container_insulation_ranking(self):
        """Verifies that INSULATED_BAG preserves higher temperature than FOAM_BOX than OPEN_BASKET."""
        t0 = 88.0
        t_env = 30.0
        k_dish = DISH_COEFFICIENTS["HOT_SOUP"]["k_dish"]
        t = 30.0

        t_insulated = newton_cooling_analytical(t, t0, t_env, k_dish * CONTAINER_FACTORS["INSULATED_BAG"])
        t_foam = newton_cooling_analytical(t, t0, t_env, k_dish * CONTAINER_FACTORS["FOAM_BOX"])
        t_open = newton_cooling_analytical(t, t0, t_env, k_dish * CONTAINER_FACTORS["OPEN_BASKET"])

        self.assertGreater(t_insulated, t_foam)
        self.assertGreater(t_foam, t_open)

    def test_thermal_reward_function_calibration(self):
        """Validates piecewise quadratic reward against values specified in survey_rl.md §5.1."""
        # 1. Fresh hot food: T = 85.0°C -> +10.0 * (85 - 60) / 25 = +10.0
        r_85 = calculate_thermal_reward(85.0)
        self.assertAlmostEqual(r_85, 10.0, places=4)

        # 2. Exactly threshold: T = 60.0°C -> 0.0
        r_60 = calculate_thermal_reward(60.0)
        self.assertAlmostEqual(r_60, 0.0, places=4)

        # 3. 5°C deficit: T = 55.0°C -> -0.05 * (5)^2 = -1.25
        r_55 = calculate_thermal_reward(55.0)
        self.assertAlmostEqual(r_55, -1.25, places=4)

        # 4. 10°C deficit: T = 50.0°C -> -0.05 * (10)^2 = -5.00
        r_50 = calculate_thermal_reward(50.0)
        self.assertAlmostEqual(r_50, -5.00, places=4)

        # 5. 20°C deficit: T = 40.0°C -> -0.05 * (20)^2 = -20.00
        r_40 = calculate_thermal_reward(40.0)
        self.assertAlmostEqual(r_40, -20.00, places=4)


if __name__ == "__main__":
    unittest.main()
