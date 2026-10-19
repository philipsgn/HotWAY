"""Tier 2: Boundary and Extreme Limits for Thermal Physics.

Opaque-box boundary testing covering:
1. Zero transit duration (t = 0).
2. Asymptotic infinite decay (t -> inf).
3. Thermal equilibrium boundary (T_0 == T_env).
4. Extreme ambient temperatures (heatwaves, cold rain).
5. Micro-stepping numerical stability and drift over thousands of discrete steps.
6. Reward continuity and extreme deficit bounds at threshold boundaries.
7. Zero cooling rate (adiabatic isolation: k = 0).

Authoritative References:
- survey_rl.md Edge Cases §1, §2, §3, §13
- PRD.md §3.1
"""

import math
import unittest


def newton_cooling_analytical(t_minutes: float, t0: float, t_env: float, k: float) -> float:
    """Exact analytical solution: T(t) = T_env + (T0 - T_env) * exp(-k * t)."""
    if t_minutes < 0:
        raise ValueError("Elapsed transit time cannot be negative")
    if k < 0:
        raise ValueError("Cooling rate k cannot be negative")
    return t_env + (t0 - t_env) * math.exp(-k * t_minutes)


def step_cooling_update(current_temp: float, delta_t: float, t_env: float, k: float) -> float:
    """Step update: T_{t+dt} = T_env + (T_t - T_env) * exp(-k * dt)."""
    if delta_t < 0:
        raise ValueError("Step transit duration cannot be negative")
    return t_env + (current_temp - t_env) * math.exp(-k * delta_t)


def calculate_thermal_reward(delivered_temp: float) -> float:
    """Piecewise quadratic thermal reward component."""
    if delivered_temp >= 60.0:
        return 10.0 * ((delivered_temp - 60.0) / 25.0)
    else:
        deficit = 60.0 - delivered_temp
        return -0.05 * (deficit ** 2)


class TestThermalLimits(unittest.TestCase):
    """Tier 2 Boundary Tests for HotWAY Thermal Engine."""

    def test_zero_time_elapsed_identity(self):
        """Edge Case 1: At dt = 0, final temperature must strictly equal initial temperature."""
        test_t0_values = [0.0, 25.0, 58.0, 88.0, 100.0]
        test_env_values = [15.0, 30.0, 40.0]
        k = 0.019

        for t0 in test_t0_values:
            for t_env in test_env_values:
                temp_at_zero = newton_cooling_analytical(0.0, t0, t_env, k)
                self.assertEqual(
                    temp_at_zero,
                    t0,
                    f"At dt=0, expected exact equality to initial temperature {t0}, got {temp_at_zero}",
                )

                # Incremental step update with dt=0
                step_temp = step_cooling_update(t0, 0.0, t_env, k)
                self.assertEqual(step_temp, t0)

    def test_asymptotic_infinite_time_convergence(self):
        """Edge Case 2: For t -> infinity, T(t) converges asymptotically to T_env and never crosses it."""
        t0 = 95.0
        t_env = 28.0
        k = 0.019

        # Moderate horizon (180 mins)
        temp_180 = newton_cooling_analytical(180.0, t0, t_env, k)
        self.assertGreater(temp_180, t_env, "Temperature should remain above ambient at 180 min")

        # Long horizon (1,000 mins)
        temp_1000 = newton_cooling_analytical(1000.0, t0, t_env, k)
        self.assertAlmostEqual(temp_1000, t_env, places=6)

        # Extreme horizon (10,000 mins)
        temp_10000 = newton_cooling_analytical(10000.0, t0, t_env, k)
        self.assertEqual(
            temp_10000,
            t_env,
            "At t=10000, temperature must converge exactly to ambient within float precision",
        )
        self.assertGreaterEqual(
            temp_10000,
            t_env,
            "Hot food temperature must NEVER drop below ambient environment temperature",
        )

    def test_thermal_equilibrium_invariance(self):
        """When initial temperature equals ambient temperature (T_0 == T_env), temperature is constant."""
        t_equilibrium = 32.5
        k = 0.038

        for t in [0.0, 1.0, 10.0, 60.0, 500.0]:
            temp = newton_cooling_analytical(t, t_equilibrium, t_equilibrium, k)
            self.assertEqual(
                temp,
                t_equilibrium,
                f"Equilibrium broken at t={t}: got {temp} instead of {t_equilibrium}",
            )

    def test_zero_cooling_rate_adiabatic_insulation(self):
        """With perfect insulation (k = 0), food retains 100% of its initial heat indefinitely."""
        t0 = 88.0
        t_env = 25.0
        k = 0.0

        for t in [0.0, 10.0, 60.0, 1440.0]:
            temp = newton_cooling_analytical(t, t0, t_env, k)
            self.assertEqual(
                temp,
                t0,
                f"Adiabatic insulation failed at t={t}: expected {t0}, got {temp}",
            )

    def test_negative_time_rejection(self):
        """Negative elapsed time or negative step duration is physically invalid and must be rejected."""
        with self.assertRaises(ValueError):
            newton_cooling_analytical(-5.0, 88.0, 30.0, 0.019)

        with self.assertRaises(ValueError):
            step_cooling_update(88.0, -0.01, 30.0, 0.019)

    def test_negative_cooling_rate_rejection(self):
        """Negative cooling coefficient violates second law of thermodynamics and must be rejected."""
        with self.assertRaises(ValueError):
            newton_cooling_analytical(10.0, 88.0, 30.0, -0.02)

    def test_extreme_environmental_temperatures(self):
        """Verifies behavior under extreme weather conditions (Dong Nai heatwave 45C, cold downpour 15C)."""
        t0 = 88.0
        k = 0.019
        t = 30.0

        # Heatwave scenario: T_env = 45°C
        temp_heatwave = newton_cooling_analytical(t, t0, 45.0, k)
        # Cold rain scenario: T_env = 15°C
        temp_cold_rain = newton_cooling_analytical(t, t0, 15.0, k)

        # In cold rain, food cools significantly faster than during a heatwave
        self.assertLess(temp_cold_rain, temp_heatwave)
        self.assertGreater(temp_heatwave, 45.0)
        self.assertGreater(temp_cold_rain, 15.0)

    def test_micro_stepping_numerical_stability(self):
        """Verifies zero accumulated numerical drift across 10,000 tiny steps (dt = 0.001 min)."""
        t0 = 88.0
        t_env = 30.0
        k = 0.019
        total_time = 10.0  # 10 minutes total
        num_steps = 10000
        dt = total_time / num_steps

        # Micro-stepping accumulation
        current_temp = t0
        for _ in range(num_steps):
            current_temp = step_cooling_update(current_temp, dt, t_env, k)

        # Analytical single evaluation
        analytical_temp = newton_cooling_analytical(total_time, t0, t_env, k)

        # Drift must remain smaller than 1e-6 °C over 10,000 floating point operations
        drift = abs(current_temp - analytical_temp)
        self.assertLess(
            drift,
            1e-6,
            f"Accumulated floating-point numerical drift exceeded tolerance: {drift:.2e}°C",
        )

    def test_reward_continuity_at_60c_threshold(self):
        """Verifies mathematical continuity of piecewise reward function at the T = 60°C boundary."""
        eps = 1e-6
        reward_at_60 = calculate_thermal_reward(60.0)
        reward_above = calculate_thermal_reward(60.0 + eps)
        reward_below = calculate_thermal_reward(60.0 - eps)

        self.assertEqual(reward_at_60, 0.0)
        self.assertAlmostEqual(reward_above, 0.0, places=4)
        self.assertAlmostEqual(reward_below, 0.0, places=4)
        self.assertLess(abs(reward_above - reward_below), 1e-3)

    def test_extreme_cold_penalty_bounds(self):
        """Verifies quadratic penalty for ruined cold food remains bounded and finite."""
        # Deep frozen: T = 0°C -> deficit = 60°C -> -0.05 * 3600 = -180.0
        r_zero = calculate_thermal_reward(0.0)
        self.assertEqual(r_zero, -180.0)
        self.assertFalse(math.isnan(r_zero))
        self.assertFalse(math.isinf(r_zero))

        # Absolute zero test: T = -273.15°C (theoretical lower limit)
        r_abs_zero = calculate_thermal_reward(-273.15)
        self.assertFalse(math.isnan(r_abs_zero))
        self.assertFalse(math.isinf(r_abs_zero))
        self.assertLess(r_abs_zero, 0.0)


if __name__ == "__main__":
    unittest.main()
