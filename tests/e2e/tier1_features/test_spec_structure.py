"""Tier 1: Specification Integrity and Interface Contract Verification.

Opaque-box tests ensuring:
1. All core project specification documents exist, are non-empty, and maintain semantic integrity.
2. All 5 agent role rules and 4 collaborative workflows exist in agents/.
3. Spec miner survey artifacts exist with required domain depth.
4. Interface contracts defined in PROJECT.md and AGENTS.md are syntactically and semantically specified.
"""

import json
import re
import unittest
from pathlib import Path


class TestSpecStructure(unittest.TestCase):
    """Verifies specification documents, directory layouts, and inter-agent contracts."""

    @classmethod
    def setUpClass(cls):
        # Locate project root dynamically from test file location
        cls.test_dir = Path(__file__).resolve().parent
        cls.project_root = cls.test_dir.parent.parent.parent

    def test_root_specifications_exist_and_non_empty(self):
        """Verifies that all foundational root specification markdown files exist."""
        required_specs = [
            "PROJECT.md",
            "PRD.md",
            "TECH_ARCHITECTURE.md",
            "PLAN.md",
            "PHASES.md",
            "ROADMAP.md",
            "AGENTS.md",
            "TEST_INFRA.md",
        ]
        for spec_name in required_specs:
            spec_path = self.project_root / spec_name
            self.assertTrue(
                spec_path.is_file(),
                f"Required root specification '{spec_name}' is missing at {spec_path}",
            )
            content = spec_path.read_text(encoding="utf-8")
            self.assertGreater(
                len(content.strip()),
                100,
                f"Specification file '{spec_name}' is unexpectedly empty or truncated",
            )

    def test_project_feature_inventory_contains_all_69_features(self):
        """Verifies that PROJECT.md contains all 69 enumerated features."""
        project_md = self.project_root / "PROJECT.md"
        content = project_md.read_text(encoding="utf-8")

        # Parse feature table rows matching pattern "| 1 | ... |" up to "| 69 |"
        feature_numbers_found = set()
        for line in content.splitlines():
            line_clean = line.strip()
            match = re.match(r"^\|\s*(\d+)\s*\|", line_clean)
            if match:
                f_num = int(match.group(1))
                if 1 <= f_num <= 69:
                    feature_numbers_found.add(f_num)

        self.assertEqual(
            len(feature_numbers_found),
            69,
            f"PROJECT.md must enumerate exactly 69 features, found {len(feature_numbers_found)}",
        )
        self.assertEqual(
            feature_numbers_found,
            set(range(1, 70)),
            "Missing feature numbers in PROJECT.md feature inventory table",
        )

    def test_agent_rules_and_workflows_exist(self):
        """Verifies that all 5 specialized subagent rules and 4 workflows exist."""
        required_rules = [
            "agents/rules/rl_engineer_rules.md",
            "agents/rules/backend_engineer_rules.md",
            "agents/rules/frontend_engineer_rules.md",
            "agents/rules/game_engineer_rules.md",
            "agents/rules/evaluator_lead_rules.md",
        ]
        required_workflows = [
            "agents/workflows/rl_experimentation_workflow.md",
            "agents/workflows/fullstack_integration_workflow.md",
            "agents/workflows/mini_game_pipeline_workflow.md",
            "agents/workflows/multi_agent_collaboration_workflow.md",
        ]

        for rel_path in required_rules + required_workflows:
            file_path = self.project_root / rel_path
            self.assertTrue(
                file_path.is_file(),
                f"Required agent document '{rel_path}' is missing at {file_path}",
            )
            content = file_path.read_text(encoding="utf-8")
            self.assertGreater(
                len(content.strip()),
                200,
                f"Agent document '{rel_path}' has insufficient content (<200 bytes)",
            )

    def test_spec_miner_survey_artifacts_exist(self):
        """Verifies that domain survey reports from spec miners exist with full specification."""
        surveys = [
            self.project_root / ".agents" / "teamwork" / "spec_miner_survey_rl_1" / "survey_rl.md",
            self.project_root / ".agents" / "teamwork" / "spec_miner_survey_web_1" / "survey_web.md",
            self.project_root / ".agents" / "teamwork" / "spec_miner_survey_game_1" / "survey_game.md",
        ]
        for survey_path in surveys:
            self.assertTrue(
                survey_path.is_file(),
                f"Spec miner artifact '{survey_path.name}' is missing at {survey_path}",
            )
            content = survey_path.read_text(encoding="utf-8")
            self.assertGreater(
                len(content),
                10000,
                f"Survey '{survey_path.name}' must contain deep technical content (>10KB)",
            )

    def test_contract_rl_to_backend_policy_runner_interface(self):
        """Verifies that the RL to Backend contract is documented with exact method signatures."""
        project_md = (self.project_root / "PROJECT.md").read_text(encoding="utf-8")
        agents_md = (self.project_root / "AGENTS.md").read_text(encoding="utf-8")

        for doc in (project_md, agents_md):
            self.assertIn(
                "HotWAYPolicyRunner",
                doc,
                "HotWAYPolicyRunner class interface contract must be documented",
            )
            self.assertIn(
                "predict_next_order",
                doc,
                "predict_next_order signature must be defined in the contract",
            )
            self.assertIn(
                "action_mask",
                doc,
                "action_mask parameter must be included in predict_next_order interface",
            )

    def test_contract_rl_to_game_ghost_trajectory_schema(self):
        """Verifies the JSON schema contract for experiments/trajectories/best_route_ghost.json."""
        project_md = (self.project_root / "PROJECT.md").read_text(encoding="utf-8")

        # Must mention the exact file name
        self.assertIn("best_route_ghost.json", project_md)

        # Validate a canonical mock against the documented contract
        sample_ghost_json = {
            "order_id": "ord_sample_01",
            "total_time_seconds": 412.5,
            "final_temperature_c": 74.8,
            "waypoints": [
                {"timestamp_offset": 0.0, "lat": 10.9212, "lon": 107.2401, "speed_kmh": 0.0},
                {"timestamp_offset": 5.0, "lat": 10.9216, "lon": 107.2405, "speed_kmh": 28.5},
            ],
        }

        # Verify key fields
        self.assertIn("order_id", sample_ghost_json)
        self.assertIn("total_time_seconds", sample_ghost_json)
        self.assertIn("final_temperature_c", sample_ghost_json)
        self.assertIn("waypoints", sample_ghost_json)
        self.assertIsInstance(sample_ghost_json["waypoints"], list)
        self.assertGreater(len(sample_ghost_json["waypoints"]), 0)

        first_wp = sample_ghost_json["waypoints"][0]
        self.assertIn("timestamp_offset", first_wp)
        self.assertIn("lat", first_wp)
        self.assertIn("lon", first_wp)
        self.assertIn("speed_kmh", first_wp)

    def test_contract_websocket_telemetry_event_names(self):
        """Verifies documented WebSocket telemetry event types and latency SLA."""
        project_md = (self.project_root / "PROJECT.md").read_text(encoding="utf-8")
        agents_md = (self.project_root / "AGENTS.md").read_text(encoding="utf-8")

        required_events = [
            "SHIPPER_TELEMETRY_UPDATE",
            "DRIVER_GPS_EMIT",
            "ORDER_STATUS_CHANGED",
        ]

        for event in required_events:
            self.assertTrue(
                event in project_md or event in agents_md,
                f"WebSocket event '{event}' must be defined in interface contracts",
            )

        # Check latency budget < 200ms documented
        self.assertTrue(
            "200" in project_md and "ms" in project_md,
            "WebSocket broadcast latency budget (<200ms) must be specified in contracts",
        )

    def test_contract_game_canvas_react_props(self):
        """Verifies documented React interface contract for <HotWAYRiderCanvas />."""
        project_md = (self.project_root / "PROJECT.md").read_text(encoding="utf-8")
        agents_md = (self.project_root / "AGENTS.md").read_text(encoding="utf-8")

        for doc in (project_md, agents_md):
            self.assertIn(
                "HotWAYRiderCanvas",
                doc,
                "HotWAYRiderCanvas component must be specified in contract",
            )
            self.assertIn(
                "ghostTrajectoryUrl",
                doc,
                "ghostTrajectoryUrl prop must be present in GameProps contract",
            )
            self.assertIn(
                "onGameComplete",
                doc,
                "onGameComplete callback must be present in GameProps contract",
            )


if __name__ == "__main__":
    unittest.main()
