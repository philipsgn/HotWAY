"""Tier 3: Pairwise Combinatorial Tests for Thermal Matrix.

Combinatorial tests systematically evaluating combinations across:
- 3 Dish Types: HOT_SOUP, DRY_WARM, COLD_DRINK
- 3 Container Types: INSULATED_BAG, FOAM_BOX, OPEN_BASKET
- 4 Weather / Ambient Temperatures: 15.0°C (cold rain), 25.0°C (cool evening), 32.0°C (hot noon), 42.0°C (heatwave)
- 3 Delivery Horizons: 10 minutes (fast), 25 minutes (standard), 45 minutes (delayed rush-hour)

Total test evaluations: 3 * 3 * 4 * 3 = 108 pairwise scenarios.
"""

import math
import unittest


DISHES = {
    "HOT_SOUP": {"T0": 88.0, "k_dish": 0.038, "threshold": 60.0, "type": "hot"},
    "DRY_WARM": {"T0": 58.0, "k_dish": 0.022, "threshold": 45.0, "type": "warm"},
    "COLD_DRINK": {"T0": 6.0, "k_dish": 0.030, "threshold": 15.0, "type": "cold"},
}

CONTAINERS = {
    "INSULATED_BAG": 0.50,
    "FOAM_BOX": 0.70,
    "OPEN_BASKET": 1.00,
}

AMBIENT_TEMPS = [15.0, 25.0, 32.0, 42.0]
HORIZONS = [10.0, 25.0, 45.0]


def newton_cooling(t_min: float, t0: float, t_env: float, k: float) -> float:
    return t_env + (t0 - t_env) * math.exp(-k * t_min)


class TestThermalMatrixPairwise(unittest.TestCase):
    """Pairwise combinatorial verification of the full thermal matrix."""

    def test_pairwise_temperature_decay_invariants(self):
        """Verifies physical invariants hold across all 108 combinations."""
        for dish_name, dish in DISHES.items():
            t0 = dish["T0"]
            k_dish = dish["k_dish"]
            dish_type = dish["type"]

            for container_name, alpha in CONTAINERS.items():
                k_composite = k_dish * alpha

                for t_env in AMBIENT_TEMPS:
                    for horizon in HORIZONS:
                        temp = newton_cooling(horizon, t0, t_env, k_composite)

                        with self.subTest(
                            dish=dish_name,
                            container=container_name,
                            t_env=t_env,
                            horizon=horizon,
                        ):
                            # Invariant 1: No NaN or Inf
                            self.assertFalse(math.isnan(temp))
                            self.assertFalse(math.isinf(temp))

                            # Invariant 2: Bounded between initial and ambient temperature
                            min_bound = min(t0, t_env)
                            max_bound = max(t0, t_env)
                            self.assertGreaterEqual(
                                temp,
                                min_bound - 1e-9,
                                f"{dish_name} in {container_name} at T_env={t_env} dropped below min bound {min_bound}",
                            )
                            self.assertLessEqual(
                                temp,
                                max_bound + 1e-9,
                                f"{dish_name} in {container_name} at T_env={t_env} exceeded max bound {max_bound}",
                            )

                            # Invariant 3: Rate ranking holds across all ambient conditions
                            # Insulated bag must retain temperature closer to T0 than open basket
                            temp_open = newton_cooling(horizon, t0, t_env, k_dish * CONTAINERS["OPEN_BASKET"])
                            deviation_insulated = abs(temp - t0)
                            deviation_open = abs(temp_open - t0)
                            self.assertLessEqual(
                                deviation_insulated,
                                deviation_open + 1e-9,
                                f"Insulated bag should deviate less from T0 than open basket",
                            )

    def test_banh_canh_survival_matrix(self):
        """Verifies Bánh Canh Gà delivery feasibility (T >= 60°C) across container types."""
        t0 = DISHES["HOT_SOUP"]["T0"]
        k_dish = DISHES["HOT_SOUP"]["k_dish"]
        t_env = 30.0  # typical Dong Nai afternoon

        # At standard 25-minute delivery:
        # Insulated bag must maintain >= 60°C
        temp_insulated = newton_cooling(25.0, t0, t_env, k_dish * CONTAINERS["INSULATED_BAG"])
        self.assertGreaterEqual(
            temp_insulated,
            60.0,
            f"Bánh Canh in Insulated Bag failed 60C delicious threshold at 25m: {temp_insulated:.2f}C",
        )

        # Open basket at 25-minute delivery will cool faster:
        temp_open = newton_cooling(25.0, t0, t_env, k_dish * CONTAINERS["OPEN_BASKET"])
        self.assertLess(
            temp_open,
            temp_insulated,
            "Open basket should result in lower delivered temperature than insulated bag",
        )


if __name__ == "__main__":
    unittest.main()
