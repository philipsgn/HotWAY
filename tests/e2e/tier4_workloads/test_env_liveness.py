"""Tier 4: Acceptance Criterion 1 Verification.

Runs 1,000 random valid steps on HangGonDeliveryEnv without error and verifies
strictly monotone temperature decay curves and boundary limits.

Authoritative Reference:
- ORIGINAL_REQUEST.md AC-1
- PROJECT.md Feature 23
- TEST_INFRA.md Tier 4
"""

from __future__ import annotations

import math
import unittest
import numpy as np

from src.rl.delivery_env import HangGonDeliveryEnv


class TestEnvLivenessAC1(unittest.TestCase):
    """Verifies AC-1: 1,000 random steps without error and monotone cooling curves."""

    def setUp(self):
        self.env = HangGonDeliveryEnv(seed=42)

    def test_1000_random_steps_stability_and_monotonicity(self):
        """Executes 1,000 steps with random valid actions and asserts physical monotonicity."""
        total_steps = 1000
        step_counter = 0
        episodes_completed = 0

        obs, info = self.env.reset(seed=42)

        # Invariant checks on initial observation
        self.assertEqual(obs.shape, (40,))
        self.assertFalse(np.isnan(obs).any())
        self.assertFalse(np.isinf(obs).any())

        prev_order_temps = {o.order_id: o.current_temp_c for o in self.env.orders}
        cooling_trajectories = {o.order_id: [o.current_temp_c] for o in self.env.orders}

        rng = np.random.default_rng(42)

        while step_counter < total_steps:
            mask = self.env.action_masks()
            self.assertIsInstance(mask, np.ndarray)
            self.assertEqual(mask.dtype, bool)
            self.assertEqual(len(mask), self.env.action_space.n)

            valid_actions = np.where(mask)[0]
            self.assertGreater(len(valid_actions), 0, "Deadlock: Action mask has zero valid actions!")

            action = int(rng.choice(valid_actions))

            obs, reward, terminated, truncated, step_info = self.env.step(action)
            step_counter += 1

            # Invariant 1: No NaN / Inf in observations and within [-1.0, 1.0]
            self.assertFalse(np.isnan(obs).any(), f"NaN detected in observation at step {step_counter}")
            self.assertFalse(np.isinf(obs).any(), f"Inf detected in observation at step {step_counter}")
            self.assertTrue(
                np.all(obs >= -1.0 - 1e-5) and np.all(obs <= 1.0 + 1e-5),
                f"Observation out of [-1.0, 1.0] bounds at step {step_counter}: min={obs.min()}, max={obs.max()}",
            )

            # Invariant 2: Reward is finite
            self.assertFalse(math.isnan(reward), f"NaN reward at step {step_counter}")
            self.assertFalse(math.isinf(reward), f"Inf reward at step {step_counter}")

            # Invariant 3: Monotonic temperature decay check for hot dishes
            transit_duration = step_info.get("transit_duration_min", 0.0)
            for order in self.env.orders:
                curr_temp = order.current_temp_c
                prev_temp = prev_order_temps.get(order.order_id, curr_temp)

                if order.dish in ["HOT_SOUP", "DRY_WARM"] and order.is_active:
                    if transit_duration > 0.0:
                        self.assertLessEqual(
                            curr_temp,
                            prev_temp + 1e-9,
                            f"Monotonicity violation on {order.order_id} at step {step_counter}: "
                            f"{prev_temp:.4f}C -> {curr_temp:.4f}C over dt={transit_duration:.2f}m",
                        )
                    self.assertGreaterEqual(
                        curr_temp,
                        self.env.t_env - 1e-9,
                        f"Temperature dropped below ambient ({self.env.t_env}C): {curr_temp:.4f}C",
                    )

                prev_order_temps[order.order_id] = curr_temp
                if order.order_id in cooling_trajectories:
                    cooling_trajectories[order.order_id].append(curr_temp)

            if terminated or truncated:
                episodes_completed += 1
                obs, info = self.env.reset()
                prev_order_temps = {o.order_id: o.current_temp_c for o in self.env.orders}
                cooling_trajectories = {o.order_id: [o.current_temp_c] for o in self.env.orders}

        self.assertEqual(step_counter, total_steps)
        self.assertGreater(episodes_completed, 0, "At least one episode must complete during 1,000 steps")

    def test_invalid_action_rejection_and_penalty(self):
        """Verifies that selecting an invalid/masked action applies -50 penalty without state corruption."""
        obs, info = self.env.reset(seed=123)
        mask = self.env.action_masks()

        valid_orders = [i for i in range(self.env.max_orders) if mask[i]]
        first_order = valid_orders[0]

        obs, r1, term, trunc, info1 = self.env.step(first_order)
        self.assertFalse(self.env.orders[first_order].is_active)

        updated_mask = self.env.action_masks()
        self.assertFalse(updated_mask[first_order], "Delivered order must be masked out")

        prev_clock = self.env.tau_current
        obs, r_invalid, term, trunc, info_invalid = self.env.step(first_order)

        self.assertEqual(r_invalid, -50.0, "Invalid action must receive severe -50.0 penalty")
        self.assertEqual(self.env.tau_current, prev_clock, "Clock must not advance on invalid action")
        self.assertEqual(info_invalid.get("error"), "INVALID_ACTION")


if __name__ == "__main__":
    unittest.main()
