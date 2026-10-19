"""Tier 2: Boundary and Capacity Limits Verification.

Tests edge cases and boundary conditions for:
- Action masking boundaries (all orders delivered, none delivered)
- Order buffer capacity limits (max_orders = 5)
- Horizon truncation limits (30 steps max)
- Empty order queues and return depot conditions

Authoritative References:
- PRD.md §3.3
- survey_rl.md Edge Cases §4, §5
- TEST_INFRA.md Feature 7, 8
"""

from __future__ import annotations

import unittest
import numpy as np

from src.rl.delivery_env import HangGonDeliveryEnv


class TestCapacityLimits(unittest.TestCase):
    """Tier 2 Boundary tests for environment capacity and action masking bounds."""

    def setUp(self):
        self.env = HangGonDeliveryEnv(seed=42)

    def test_initial_action_mask_bounds(self):
        """Verifies initial action mask contains exactly M active order choices + WAIT + (RETURN if allowed)."""
        obs, info = self.env.reset(seed=10)
        mask = self.env.action_masks()

        self.assertEqual(len(mask), self.env.action_space.n)
        self.assertEqual(len(mask), 7)
        # All 5 order slots are initially active
        self.assertTrue(np.all(mask[:5]))
        # WAIT is always True
        self.assertTrue(mask[5])

    def test_action_mask_when_all_delivered(self):
        """Verifies that when all orders are fulfilled, only WAIT and RETURN_DEPOT remain valid."""
        obs, info = self.env.reset(seed=10)

        # Deliver all 5 orders
        for action in range(5):
            obs, reward, term, trunc, info = self.env.step(action)

        mask = self.env.action_masks()
        # All order actions should be False
        self.assertFalse(np.any(mask[:5]))
        # WAIT and RETURN_DEPOT must be True
        self.assertTrue(mask[5])
        self.assertTrue(mask[6])

    def test_max_step_truncation(self):
        """Verifies environment truncates after exceeding max_steps (30 steps)."""
        obs, info = self.env.reset(seed=99)
        done = False
        step_count = 0

        # Repeatedly choose WAIT (action 5)
        while not done:
            obs, reward, terminated, truncated, info = self.env.step(5)
            done = terminated or truncated
            step_count += 1
            if step_count > 35:
                break

        self.assertTrue(truncated)
        self.assertEqual(step_count, 30)


if __name__ == "__main__":
    unittest.main()
