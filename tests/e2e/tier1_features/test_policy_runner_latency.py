"""Tier 1: Policy Runner Inference Latency Verification.

Verifies that HotWAYPolicyRunner executes inference within the sub-20ms latency SLA.

Reference: PROJECT.md Feature #21, AGENTS.md §2.1
"""

from __future__ import annotations

import time
import unittest
from src.rl.policy_runner import HotWAYPolicyRunner


class TestPolicyRunnerLatency(unittest.TestCase):
    """Verifies inference throughput and latency SLA (<20ms)."""

    def setUp(self):
        self.runner = HotWAYPolicyRunner()

    def test_predict_next_order_latency_sub_20ms(self):
        self.assertTrue(self.runner.is_loaded, "HotWAYPolicyRunner must have model loaded")
        mock_obs = {
            "shipper_pos": (10.9212, 107.2401),
            "speed_kmh": 35.0,
            "load_ratio": 0.6,
            "active_orders": [
                {
                    "is_active": True,
                    "lat": 10.925,
                    "lon": 107.243,
                    "current_temp": 80.0,
                    "deadline_remaining_min": 25.0,
                    "cooling_rate": 0.019,
                },
                {
                    "is_active": True,
                    "lat": 10.928,
                    "lon": 107.246,
                    "current_temp": 75.0,
                    "deadline_remaining_min": 35.0,
                    "cooling_rate": 0.019,
                },
            ],
            "time_of_day_min": 720.0,
            "ambient_temp_c": 30.0,
            "ql56_congestion": 2.0,
        }
        action_mask = [1, 1, 0, 0, 0, 1, 1]

        # Warm-up run
        _ = self.runner.predict_next_order(mock_obs, action_mask)

        # Benchmark 200 invocations
        durations = []
        for _ in range(200):
            t0 = time.perf_counter()
            action = self.runner.predict_next_order(mock_obs, action_mask)
            dur = (time.perf_counter() - t0) * 1000.0  # ms
            durations.append(dur)
            self.assertIn(action, [0, 1, 5, 6])

        mean_latency = sum(durations) / len(durations)
        self.assertLess(
            mean_latency,
            20.0,
            f"Mean inference latency ({mean_latency:.2f}ms) exceeded SLA (<20ms)",
        )


if __name__ == "__main__":
    unittest.main()
