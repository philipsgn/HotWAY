"""Tier 4: Acceptance Criterion 3 Verification — Ablation Study 15% Gain.

Verifies that the multi-objective thermal reward function achieves at least
15% higher delivered food temperature compared to an ablated reward function.

Reference: ORIGINAL_REQUEST.md AC-3, PROJECT.md Feature #25
"""

from __future__ import annotations

import unittest
from src.rl.ablation_study import run_ablation_study


class TestAblationThermalGain(unittest.TestCase):
    """Verifies that the ablation study satisfies the >= 15% temperature improvement SLA."""

    def test_ablation_temperature_gain_exceeds_15_percent(self):
        summary = run_ablation_study(num_episodes=50, start_seed=100)

        rel_gain = summary["relative_temp_gain_pct"]
        retention_gain = summary["retention_gain_pct"]

        self.assertTrue(
            summary["meets_15_percent_threshold"],
            f"Ablation gain did not achieve >= 15% (rel_gain={rel_gain}%, retention_gain={retention_gain}%)",
        )
        self.assertGreaterEqual(
            max(rel_gain, retention_gain),
            15.0,
            f"Maximum gain metric must be at least 15.0%: rel={rel_gain}%, ret={retention_gain}%",
        )


if __name__ == "__main__":
    unittest.main()
